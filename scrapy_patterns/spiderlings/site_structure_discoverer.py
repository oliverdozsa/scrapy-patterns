"""Contains the site structure discoverer spiderling."""
import logging
from typing import List, Tuple, Callable, Optional

from scrapy import Spider, Request
from scrapy.http import Response

from scrapy_patterns.request_factory import RequestFactory
from scrapy_patterns.site_structure import SiteStructure


class CategoryParser:
    """Interface used for parsing categories."""
    def parse(self, response) -> List[Tuple[str, str]]:
        """
        Parses categories from the response.
        Args:
            response: The response

        Returns: List of tuples, where the first element is the URL of the category, and the second is the name.
        """
        raise NotImplementedError()


class SiteStructureDiscoverer:
    """Discovers the site structure."""
    # pylint: disable=too-many-arguments, too-many-instance-attributes
    def __init__(self, spider: Spider, start_url: str, category_parsers: List[CategoryParser],
                 request_factory: RequestFactory,
                 on_discovery_complete: Callable[['SiteStructureDiscoverer'], Optional[Request]] = None):
        """
        Args:
            spider: The spider to which this belongs.
            start_url: Starting URL of categories.
            category_parsers: List of category parsers for each level of categories. The last element in the list should
                              parse the leaf categories.
            request_factory: The request factory.
            on_discovery_complete: An optional callback when the discovery is complete. It'll receive this discoverer
            as its argument. It should return a scrapy request to continue the scraping with.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = spider.name  # Needed to conform to Scrapy Spiders.
        self.structure = SiteStructure(self.name)
        self.__start_url = start_url
        self.__category_parsers = category_parsers
        self.__request_factory = request_factory
        self.__remaining_work = 0
        self.__on_discovery_complete = on_discovery_complete if on_discovery_complete else self.__do_nothing

    def create_start_request(self):
        """
        Creates the starting request.
        Returns: The starting request.
        """
        self.__remaining_work += 1
        return self.__request_factory.create(self.__start_url, self.__process_category_response,
                                             cb_kwargs={"category_index": 0, "path": None})

    def __process_category_response(self, response, category_index: int, path: str):
        self.__remaining_work -= 1
        category_parser = self.__category_parsers[category_index]
        urls_and_names = self.__get_urls_and_names(response, category_parser)
        requests = self.__prepare_requests(urls_and_names, path, category_index)
        self.__remaining_work += len(requests)
        self.logger.info("[%s] Remaining work(s): %d", self.name, self.__remaining_work)
        if self.__remaining_work == 0:
            self.logger.info("[%s] Discovery complete.\n"
                             "%s", self.name, str(self.structure))
            yield self.__on_discovery_complete(self)
        for req in requests:
            yield req

    @staticmethod
    def __get_urls_and_names(response: Response, category_parser: CategoryParser):
        return category_parser.parse(response)

    @staticmethod
    def __do_nothing(_):
        return None

    def __prepare_requests(self, urls_and_names: List[Tuple[str, str]], current_path: str, category_index: int):
        requests = []
        for url, name in urls_and_names:
            structure_path = self.__determine_structure_path(current_path, name)
            is_added = self.__try_add_path(structure_path, url)
            if is_added:
                self.__append_to_requests_if_not_finished(category_index, requests, (url, structure_path))
        return requests

    @staticmethod
    def __determine_structure_path(current_path, name):
        if current_path is None:
            return name
        else:
            return current_path + "/" + name

    def __try_add_path(self, path: str, url: str) -> bool:
        if self.structure.get_node_at_path(path) is not None:
            self.logger.warning("Path \"path\" already exists; path to add is ignored!")
            return False
        else:
            self.structure.add_node_with_path(path, url)
            return True

    def __append_to_requests_if_not_finished(self, category_index: int, requests: List[Request],
                                             url_and_path: Tuple[str, str]):
        if category_index + 1 < len(self.__category_parsers):
            request = self.__request_factory.create(
                url_and_path[0], self.__process_category_response,
                cb_kwargs={"category_index": category_index + 1, "path": url_and_path[1]})
            requests.append(request)
