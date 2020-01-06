"""Contains the site pager spiderling."""
import logging
from typing import List, Union, Tuple, Callable

from scrapy import Spider, Item, signals, exceptions, Request
from scrapy.http import Response
from scrapy_patterns.request_factory import RequestFactory


class ItemParser:
    """An interface used for parsing items from a response"""

    def parse(self, response: Response) -> Item:
        """
        Args:
            response: The response.

        Returns: The item.
        """
        raise NotImplementedError()


class ItemUrlsParser:
    """Interface used for parsing item urls from a response (typically from a page)"""

    def parse(self, response: Response) -> Union[List[str], List[Tuple[str, dict]]]:
        """
        Args:
            response (Response): The scrapy response

        Returns: Either the list of item URLs, or a list of tuples, where the first element is the item URL, and the
        second element is a dict that will be passed as kwargs to the Request constructor.
        """
        raise NotImplementedError()


class NextPageUrlParser:
    """Interface used for checking, and parsing the URL of the next page"""

    def has_next(self, response: Response) -> bool:
        """
        Checks whether the response contains a next page URL.
        Args:
            response (Response): The response.

        Returns: True if there's a next page, False otherwise.
        """
        raise NotImplementedError()

    def parse(self, response: Response) -> Union[str, Tuple[str, dict]]:
        """
        Parses the URL of the next page.
        Args:
            response (Response): The response.

        Returns: Either the next page's URL, or a tuple, where the first element is the next page's URL, and the
        second element is a dict that will be passed as kwargs to the Request constructor.
        """
        raise NotImplementedError()


class SitePageParsers:
    """Groups parsers."""
    def __init__(self, next_page_url: NextPageUrlParser, item_urls: ItemUrlsParser, item: ItemParser):
        """
        Args:
            next_page_url (NextPageUrlParser): Next page URL parser
            item_urls (ItemUrlsParser): Item URLs parser
            item (ItemParser): Item parser.
        """
        self.next_page_url = next_page_url
        self.item_urls = item_urls
        self.item = item


class SitePageCallbacks:
    """Callbacks for paging events."""
    def __init__(self, on_paging_finished: Callable = None, on_page_finished: Callable = None):
        """
        Args:
            on_paging_finished: Called when paging is finished. Callback receives no parameter.
            on_page_finished:  Called when a page is finished. Callback gets the URL of the next page.
        """
        self.on_paging_finished = on_paging_finished if on_page_finished else self.__do_nothing_callback
        self.on_page_finished = on_page_finished if on_page_finished else self.__do_nothing_callback

    def __do_nothing_callback(self, *args):
        pass


class SitePager:
    """From the given start URL, it goes through its pages and parses items."""
    def __init__(self, spider: Spider, request_factory: RequestFactory,
                 site_page_parsers: SitePageParsers, site_page_callback: SitePageCallbacks = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__request_factory = request_factory
        self.__next_page_data = _NextPageData()
        self.__items_counter = _ItemsCounter()
        self.__site_page_callbacks = site_page_callback if site_page_callback else SitePageCallbacks()
        self.__site_page_parsers = site_page_parsers
        self.name = spider.name  # Needed to conform to Scrapy Spiders.
        spider.crawler.signals.connect(self.__spider_idle, signal=signals.spider_idle)

    def start(self, start_page_url: str) -> Request:
        """
        Creates the starting request, and resets the pager. This request should be returned from spiders.
        start() can be used multiple times, but only when paging is finished!
        Args:
            start_page_url: The url of the start page.

        Returns: The starting request.
        """
        self.__next_page_data = _NextPageData()
        self.__items_counter = _ItemsCounter()
        return self.__request_factory.create(start_page_url, self.__process_page)

    def __process_page(self, response):
        self.__items_counter.success = 0
        self.__items_counter.failed = 0
        if self.__site_page_parsers.next_page_url.has_next(response):
            self.logger.info("[%s] Has next page.", self.name)
            url_data = self.__site_page_parsers.next_page_url.parse(response)
            self.__set_next_page_data(url_data)
        else:
            self.logger.info("[%s] No more pages.", self.name)
            self.__next_page_data.url = None
            self.__next_page_data.req_kwargs = {}
        item_requests = self.__create_next_item_requests(response)
        self.__items_counter.total = len(item_requests)
        for req in item_requests:
            yield req

    def __create_next_item_requests(self, page):
        urls = self.__site_page_parsers.item_urls.parse(page)
        requests = []
        for url_data in urls:
            url = url_data
            req_kwargs = {}
            if isinstance(url_data, tuple):
                url = url_data[0]
                req_kwargs = url_data[1]
            requests.append(
                self.__request_factory.create(
                    url, self.__process_item, errback=self.__process_item_failure, **req_kwargs)
            )
        return requests

    def __process_item(self, response):
        yield self.__site_page_parsers.item.parse(response)
        self.__items_counter.success += 1
        yield self.__on_item_event()

    def __process_item_failure(self, _):
        self.logger.warning("[%s] Failed to get an item!", self.name)
        self.__items_counter.failed += 1

    def __on_item_event(self):
        progress = self.__items_counter.success + self.__items_counter.failed
        self.logger.info("[%s] Item progress in current page: %3d [OK] / %3d [FAILED] / %3d [TOTAL]",
                         self.name, self.__items_counter.success, self.__items_counter.failed,
                         self.__items_counter.total)
        if progress == self.__items_counter.total:
            self.logger.info("[%s] All items processed in current page. Checking if there's more work to do.",
                             self.name)
            if self.__next_page_data.url:
                self.logger.info("[%s] Going to next page", self.name)
                self.__site_page_callbacks.on_page_finished(self.__next_page_data.url)
                return self.__request_factory.create(
                    self.__next_page_data.url, self.__process_page, **self.__next_page_data.req_kwargs)
            else:
                self.logger.info("[%s] No more pages.", self.name)
                return self.__site_page_callbacks.on_paging_finished()
        return None

    def __spider_idle(self, spider):
        # It happens when the last item request fails.
        self.logger.warning("Got spider idle!")
        next_req = self.__on_item_event()
        if next_req:
            # The request has to be 'manually' inserted.
            spider.crawler.engine.crawl(next_req, spider)
            raise exceptions.DontCloseSpider("Got spider idle, but there's more work to do!")

    def __set_next_page_data(self, url_data):
        if isinstance(url_data, tuple):
            self.__next_page_data.url = url_data[0]
            self.__next_page_data.req_kwargs = url_data[1]
        else:
            self.__next_page_data.url = url_data


class _ItemsCounter:
    def __init__(self):
        self.total = 0
        self.success = 0
        self.failed = 0


class _NextPageData:
    def __init__(self):
        self.url = None
        self.req_kwargs = {}
