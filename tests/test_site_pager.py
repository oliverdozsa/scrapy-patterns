"""Contains site pager tests"""
from unittest.mock import Mock
from scrapy_patterns.spiderlings.site_pager import SitePager, SitePageParsers


def test_create():
    """Tests the creation of site_pager."""
    mock_spider = Mock()
    mock_spider.name = "SomeName"
    mock_request_factory = Mock()
    pager = SitePager(mock_spider, mock_request_factory, __create_mock_site_page_parser())
    assert pager.name == "SomeName"


def __create_mock_site_page_parser():
    parser = SitePageParsers(Mock(), Mock(), Mock())
    return parser
