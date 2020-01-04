"""Contains site structure discoverer tests"""
from typing import List, Tuple
from unittest.mock import Mock, call, ANY
from scrapy_patterns.spiderlings.site_structure_discoverer import SiteStructureDiscoverer, CategoryParser


def test_responses_without_complete_cb():
    """Tests getting a response and there's no complete callback given."""
    mock_spider = Mock()
    mock_spider.name = "some_spider_name"
    mock_category_parsers = [_MockCategoryParserMain(), _MockCategoryParserSub()]
    mock_request_factory = Mock()

    discoverer = SiteStructureDiscoverer(mock_spider, "http://some-recipe.com", mock_category_parsers,
                                         mock_request_factory)
    discoverer.create_start_request()

    calls = [call.create("http://some-recipe.com", ANY, cb_kwargs=ANY)]
    mock_request_factory.assert_has_calls(calls)
    assert discoverer.name == "some_spider_name"

    # Main categories
    __simulate_category_response(mock_request_factory, 0)

    # Sub categories
    __simulate_category_response(mock_request_factory, 1)
    __simulate_category_response(mock_request_factory, 1)


def test_responses_with_complete_callback():
    """Tests getting a response with complete callback given."""
    mock_spider = Mock()
    mock_category_parsers = [_MockCategoryParserMain(), _MockCategoryParserSub()]
    mock_request_factory = Mock()
    mock_on_discovery_complete_callback = Mock()

    discoverer = SiteStructureDiscoverer(mock_spider, "http://some-recipe.com", mock_category_parsers,
                                         mock_request_factory, mock_on_discovery_complete_callback)
    discoverer.create_start_request()

    # Main categories
    __simulate_category_response(mock_request_factory, 0)
    calls = [
        call.create("http://some-recipe.com/main1", ANY, cb_kwargs=ANY),
        call.create("http://some-recipe.com/main2", ANY, cb_kwargs=ANY)
    ]
    mock_request_factory.assert_has_calls(calls)
    assert discoverer.structure.get_node_at_path("MainOne") is not None
    assert discoverer.structure.get_node_at_path("MainTwo") is not None

    # Sub categories
    __simulate_category_response(mock_request_factory, 1, "MainOne")
    __simulate_category_response(mock_request_factory, 1, "MainTwo")
    mock_on_discovery_complete_callback.assert_called()
    assert discoverer.structure.get_node_at_path("MainOne/SubOne") is not None
    assert discoverer.structure.get_node_at_path("MainOne/SubTwo") is not None
    assert discoverer.structure.get_node_at_path("MainTwo/SubOne") is not None
    assert discoverer.structure.get_node_at_path("MainTwo/SubTwo") is not None


class _MockCategoryParserMain(CategoryParser):
    def parse(self, response) -> List[Tuple[str, str]]:
        return [("http://some-recipe.com/main1", "MainOne"), ("http://some-recipe.com/main2", "MainTwo")]


class _MockCategoryParserSub(CategoryParser):
    def parse(self, response) -> List[Tuple[str, str]]:
        return [("http://some-recipe.com/sub1", "SubOne"),
                ("http://some-recipe.com/sub2", "SubTwo")]


def __simulate_category_response(mock_req_factory: Mock, category_index: int, path: str = None):
    process_category_response_callback = mock_req_factory.create.call_args[0][1]
    mock_category_response = Mock()
    return list(process_category_response_callback(mock_category_response, category_index, path))
