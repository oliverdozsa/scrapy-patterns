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
    next_item_reqs_generator = mock_request_factory.create.call_args[0][1]
    mock_response = Mock()
    parser.next_page_url.has_next.return_value = True
    parser.next_page_url.parse.return_value = "http://some-next-item-url.com"
    parser.item_urls.parse.return_value = ["http://item1.url"]

    # Item URL check
    _ = [req for req in next_item_reqs_generator(mock_response)]
    mock_request_factory.create.assert_called_with("http://item1.url", ANY, errback=ANY)

    # Since no more itesm, check next page URL
    next_item_reqs_generator = mock_request_factory.create.call_args[0][1]
    mock_item_response = Mock()
    _ = [req for req in next_item_reqs_generator(mock_item_response)]
    mock_request_factory.create.assert_called_with("http://some-next-item-url.com", ANY)


def __create_mock_site_page_parser():
    parser = SitePageParsers(Mock(), Mock(), Mock())
    return parser

