"""Contains site pager tests"""
from unittest.mock import Mock, ANY, call
import pytest
from scrapy.exceptions import DontCloseSpider
from scrapy_patterns.spiderlings.site_pager import SitePager, SitePageParsers


def test_create():
    """Tests the creation of site_pager."""
    mock_spider = Mock()
    mock_spider.name = "SomeName"
    mock_request_factory = Mock()
    pager = SitePager(mock_spider, mock_request_factory, __create_mock_site_page_parser())
    assert pager.name == "SomeName"


def test_start():
    """Tests the creation of the starting request."""
    mock_request_factory = Mock()
    pager = SitePager(Mock(), mock_request_factory, __create_mock_site_page_parser())
    pager.start("http://some-starting-url.com")
    mock_request_factory.create.assert_called_with("http://some-starting-url.com", ANY)


def test_process_page_has_next():
    """Tests when a page has a next page."""

    # Starting URL
    mock_request_factory = Mock()
    parser = __create_mock_site_page_parser()
    pager = SitePager(Mock(), mock_request_factory, parser)
    pager.start("http://some-starting-url.com")

    __simulate_page_response_with_items(mock_request_factory, parser, True, 2, "http://some-next-page-url.com")

    # Expect request factory calls for starting URls, and two items.
    calls = [call.create("http://some-starting-url.com", ANY),
             call.create("http://item1.url", ANY, errback=ANY),
             call.create("http://item2.url", ANY, errback=ANY)]
    mock_request_factory.assert_has_calls(calls)

    # Receive two items, and expect going to the next page.
    __simulate_items_response(mock_request_factory)
    __simulate_items_response(mock_request_factory)
    mock_request_factory.create.assert_called_with("http://some-next-page-url.com", ANY)


def test_process_page_has_no_next():
    """Tests the last page reached scenario."""

    # Starting URL
    mock_request_factory = Mock()
    parser = __create_mock_site_page_parser()
    pager = SitePager(Mock(), mock_request_factory, parser)
    pager.start("http://some-starting-url.com")

    __simulate_page_response_with_items(mock_request_factory, parser, False, 2)

    # Since no more items, next items, or requests
    next_items_or_reqs_for_first_response = __simulate_items_response(mock_request_factory)
    next_items_or_reqs_for_second_response = __simulate_items_response(mock_request_factory)
    for next_items_reqs in [next_items_or_reqs_for_first_response, next_items_or_reqs_for_second_response]:
        assert len(next_items_reqs) == 2, "There should be items after item response!"
        assert next_items_reqs[1] is None, "The request after item should be None!"


def test_request_item_failures_with_next_page():
    """Tests item request failure."""

    mock_request_factory = Mock()
    parser = __create_mock_site_page_parser()
    mock_spider = Mock()
    pager = SitePager(mock_spider, mock_request_factory, parser)
    pager.start("http://some-starting-url.com")

    __simulate_page_response_with_items(mock_request_factory, parser, True, 1, "http://some-next-page-url.com")

    failure_callback = mock_request_factory.create.call_args[1]["errback"]
    failure_callback(Mock())
    # Since the last item failed,spider_idle signal will be triggered.
    spider_idle_callback = mock_spider.crawler.signals.connect.call_args[0][0]
    with pytest.raises(DontCloseSpider):
        spider_idle_callback(mock_spider)
        mock_spider.crawler.engine.crawl.assert_called()


def test_page_and_items_with_request_kwargs():
    """Test when the item, and page urls also have request keywords attached to them"""
    # Starting URL
    mock_request_factory = Mock()
    parser = __create_mock_site_page_parser()
    pager = SitePager(Mock(), mock_request_factory, parser)
    pager.start("http://some-starting-url.com")

    process_page_callback = mock_request_factory.create.call_args[0][1]
    mock_response = Mock()
    parser.next_page_url.has_next.return_value = True
    parser.next_page_url.parse.return_value = ("http://some-next-page-url.com", {"some_page_req_kwarg": "some_value"})
    parser.item_urls.parse.return_value = [("http://item1.url", {"some_item_req_kwarg": "some_other_value"})]
    _ = list(process_page_callback(mock_response))

    req_kwargs = mock_request_factory.create.call_args[1]
    assert "some_item_req_kwarg" in req_kwargs
    assert req_kwargs["some_item_req_kwarg"] == "some_other_value"

    process_item_callback = mock_request_factory.create.call_args[0][1]
    _ = list(process_item_callback(Mock()))
    next_page_req_kwarg = mock_request_factory.create.call_args[1]
    assert "some_page_req_kwarg" in next_page_req_kwarg
    assert next_page_req_kwarg["some_page_req_kwarg"] == "some_value"


def __create_mock_site_page_parser():
    parser = SitePageParsers(Mock(), Mock(), Mock())
    return parser


def __simulate_page_response_with_items(mock_req_factory: Mock, mock_site_parser: SitePageParsers,
                                        has_next_page: bool, num_of_items=1, next_page_url: str = None):
    process_page_callback = mock_req_factory.create.call_args[0][1]
    mock_response = Mock()
    mock_site_parser.next_page_url.has_next.return_value = has_next_page
    mock_site_parser.next_page_url.parse.return_value = next_page_url
    mock_site_parser.item_urls.parse.return_value = ["http://item%d.url" % (i + 1) for i in range(0, num_of_items)]
    return list(process_page_callback(mock_response))  # Next item URL request


def __simulate_items_response(mock_req_factory: Mock):
    process_item_callback = mock_req_factory.create.call_args[0][1]
    mock_item_response = Mock()
    return list(process_item_callback(mock_item_response))  # Next item, and next page
