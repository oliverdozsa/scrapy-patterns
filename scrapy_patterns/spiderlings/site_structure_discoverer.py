import logging
from typing import List, Tuple

from scrapy.http import Response

from scrapy_patterns.request_factory import RequestFactory
from scrapy_patterns.site_structure import SiteStructure


class CategoryParser:
    def parse(self, response) -> List[Tuple[str, str]]:
        raise NotImplementedError()


class SiteStructureDiscoverer:
    def __init__(self, name: str, start_url: str, category_parsers: List[CategoryParser],
                 request_factory: RequestFactory, on_discovery_complete=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.structure = SiteStructure(name)
        self.__start_url = start_url
        self.__category_parsers = category_parsers
        self.__request_factory = request_factory
        self.name = name
        self.__remaining_work = 0
        self.__empty_func = lambda _: None
        self.__on_discovery_complete = on_discovery_complete if on_discovery_complete else self.__do_nothing

    def create_start_request(self):
        self.__remaining_work += 1
        return self.__request_factory.create(self.__start_url, self.__process_category_response,
                                             cb_kwargs={"category_index": 0, "path": None})

    def __process_category_response(self, response, category_index: int, path: str):
        self.__remaining_work -= 1
        category_parser = self.__category_parsers[category_index]
        urls_and_names = self.__get_urls_and_names(response, category_parser)
        requests = []
        for url, name in urls_and_names:
            structure_path = name if path is None else path + "/" + name
            self.structure.add_node_with_path(structure_path, url)
            if category_index + 1 < len(self.__category_parsers):
                request = self.__request_factory.create(
                    url, self.__process_category_response,
                    cb_kwargs={"category_index": category_index + 1, "path": structure_path})
                requests.append(request)
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
    def __do_nothing(discoverer):
        return None
