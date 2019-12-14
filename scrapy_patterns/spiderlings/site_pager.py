import logging
from typing import List, Union, Tuple

from scrapy import Spider, Item
from scrapy.http import Response
from recipes_scraper.patterns.request_factory import RequestFactory


class ItemParser:
    def parse(self, response) -> Item:
        raise NotImplementedError()


class ItemUrlsParser:
    def parse(self, response: Response) -> Union[List[str], List[Tuple[str, dict]]]:
        raise NotImplementedError()


class NextPageUrlParser:
    def has_next(self, response: Response) -> bool:
        raise NotImplementedError()

    def parse(self, response: Response) -> Union[str, Tuple[str, dict]]:
        raise NotImplementedError()


class SitePageParsers:
    def __init__(self, next_page_url: NextPageUrlParser, item_urls: ItemUrlsParser, item: ItemParser):
        self.next_page_url = next_page_url
        self.item_urls = item_urls
        self.item = item


class SitePager:
    def __init__(self, start_page_url: str, spider: Spider, request_factory: RequestFactory,
                 site_page_parsers: SitePageParsers,
                 on_paging_finished_callback=None, on_page_finished_callback=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__start_page_url = start_page_url
        self.__current_page_url = None
        self.__spider = spider
        self.__request_factory = request_factory
        self.__next_page_url = None
        self.__next_page_req_kwargs = {}
        self.__num_of_items = 0
        self.__num_of_items_scraped = 0
        self.__num_of_items_failed = 0
        self.__on_paging_finished_callback = on_paging_finished_callback
        self.__on_page_finished_callback = on_page_finished_callback
        self.__site_page_parsers = site_page_parsers
        self.name = spider.name

    def create_start_request(self):
        return self.__request_factory.create(self.__start_page_url, self.__process_page)

    def __process_page(self, response):
        self.__num_of_items_scraped = 0
        self.__num_of_items_failed = 0
        self.__current_page_url = response.url
        if self.__site_page_parsers.next_page_url.has_next(response):
            self.logger.info("[%s] Has next page.", self.__spider.name)
            url_data = self.__site_page_parsers.next_page_url.parse(response)
            if isinstance(url_data, tuple):
                self.__next_page_url = url_data[0]
                self.__next_page_req_kwargs = url_data[1]
            else:
                self.__next_page_url = url_data
        else:
            self.logger.info("[%s] No more pages.", self.__spider.name)
            self.__next_page_url = None
        item_requests = self.__create_next_item_requests(response)
        self.__num_of_items = len(item_requests)
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
        self.__num_of_items_scraped += 1
        yield self.__on_item_event()

    def __process_item_failure(self, _):
        self.logger.warning("[%s] Failed to get an item!", self.__spider.name)
        self.__num_of_items_failed += 1
        next_req = self.__on_item_event()
        if next_req:
            # Error callback returns are ignored, therefore the request has to be manually inserted.
            self.__spider.crawler.engine.crawl(next_req, self)

    def __on_item_event(self):
        total = self.__num_of_items
        success = self.__num_of_items_scraped
        failed = self.__num_of_items_failed
        progress = success + failed
        self.logger.info("[%s] Item progress in current page: %3d [OK] / %3d [FAILED] / %3d [TOTAL]",
                         self.__spider.name, success, failed, total)
        if progress == total:
            self.logger.info("[%s] All items processed in current page. Checking if there's more work to do.",
                             self.__spider.name)
            if self.__next_page_url:
                self.logger.info("[%s] Going to next page", self.__spider.name)
                self.__on_page_finished_callback(self.__next_page_url)
                return self.__request_factory.create(
                    self.__next_page_url, self.__process_page, **self.__next_page_req_kwargs)
            else:
                self.logger.info("[%s] No more pages.", self.__spider.name)
                return self.__on_paging_finished_callback()
        return None
