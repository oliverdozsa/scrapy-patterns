"""Contains site pager tests"""
from unittest.mock import Mock, ANY
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

    # Starting URL has 1 item, and has next page.
    __simulate_page_response(mock_request_factory, parser, True, "http://some-next-page-url.com")

    # Item URL check
    mock_request_factory.create.assert_called_with("http://item1.url", ANY, errback=ANY)

    # Since no more items, check next page URL
    __simulate_items_response(mock_request_factory)
    mock_request_factory.create.assert_called_with("http://some-next-page-url.com", ANY)


def test_process_has_no_next():
    """Tests the last page reached scenario."""

    # Starting URL
    mock_request_factory = Mock()
    parser = __create_mock_site_page_parser()
    pager = SitePager(Mock(), mock_request_factory, parser)
    pager.start("http://some-starting-url.com")

    # Starting URL has 1 item, and has next page.
    __simulate_page_response(mock_request_factory, parser, False)

    # Since no more items, next items, or requests
    next_items_or_reqs = __simulate_items_response(mock_request_factory)
    assert len(next_items_or_reqs) == 2, "There should be items after item response!"
    assert next_items_or_reqs[1] is None, "The request after item should be None!"


def __create_mock_site_page_parser():
    parser = SitePageParsers(Mock(), Mock(), Mock())
    return parser


def __simulate_page_response(mock_req_factory: Mock, mock_site_parser: SitePageParsers,
                             has_next_page: bool, next_page_url: str = None):
    # With one item on page
    next_item_urls_reqs_generator = mock_req_factory.create.call_args[0][1]
    mock_response = Mock()
    mock_site_parser.next_page_url.has_next.return_value = has_next_page
    mock_site_parser.next_page_url.parse.return_value = next_page_url
    mock_site_parser.item_urls.parse.return_value = ["http://item1.url"]
    return list(next_item_urls_reqs_generator(mock_response))  # Next item URL request


def __simulate_items_response(mock_req_factory: Mock):
    next_items_or_reqs_generator = mock_req_factory.create.call_args[0][1]
    mock_item_response = Mock()
    return list(next_items_or_reqs_generator(mock_item_response))  # Next item, and next page
