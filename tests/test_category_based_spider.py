"""Contains category based spider tests"""
from unittest.mock import Mock, patch

import pytest

from scrapy_patterns.site_structure import VisitState
from scrapy_patterns.spiders.category_based_spider import CategoryBasedSpider, CategoryBasedSpiderData


@patch("scrapy_patterns.spiders.category_based_spider.SiteStructureDiscoverer")
@patch("scrapy_patterns.spiders.category_based_spider.SitePager")
@patch("scrapy_patterns.spiders.category_based_spider.CategoryBasedSpiderState")
def test_no_progress_start_requests_through_discoverer(
        mock_spider_state_cls, _, mock_site_structure_discoverer_cls):
    """Tests starting when progress file doesn't exist. Starts with site discoverer, and then discovery completes"""
    data = CategoryBasedSpiderData("some-progress-file-dir", "some-spider-name", "http://some-recipes.com")
    mock_request_factory = Mock()

    mock_spider_state_instance = __prepare_mock_spider_instance(False)
    mock_spider_state_cls.return_value = mock_spider_state_instance
    mock_next_category = Mock()
    mock_spider_state_instance.site_structure.find_leaf_with_visit_state.return_value = mock_next_category

    mock_site_structure_discoverer_instance = Mock()
    mock_site_structure_discoverer_instance.structure = mock_spider_state_instance.site_structure
    mock_site_structure_discoverer_cls.return_value = mock_site_structure_discoverer_instance

    spider = CategoryBasedSpider(Mock(), Mock(), data)
    spider.request_factory = mock_request_factory
    list(spider.start_requests())
    mock_site_structure_discoverer_instance.create_start_request.assert_called()

    # Simulate discovery complete.
    discovery_complete_callback = mock_site_structure_discoverer_cls.call_args[0][4]
    discovery_complete_callback(mock_site_structure_discoverer_instance)
    mock_spider_state_instance.save.assert_called()
    mock_next_category.set_visit_state.assert_called_with(VisitState.IN_PROGRESS, propagate=True)

    assert list(spider.parse(Mock())) == [None]


@patch("scrapy_patterns.spiders.category_based_spider.SiteStructureDiscoverer")
@patch("scrapy_patterns.spiders.category_based_spider.SitePager")
@patch("scrapy_patterns.spiders.category_based_spider.CategoryBasedSpiderState")
def test_with_progress_start_requests_all_visited(mock_spider_state_cls, mock_site_pager_cls, _):
    """Tests spider start when progress file exists, and then after paging completed with all categories visited."""
    data = CategoryBasedSpiderData("some-progress-file-dir", "some-spider-name", "http://some-recipes.com")
    mock_request_factory = Mock()

    mock_current_category_parent = Mock()
    mock_current_category_parent.parent = None
    mock_current_category_parent.children = [Mock(), Mock()]
    mock_current_category_parent.children[0].visit_state = VisitState.VISITED
    mock_current_category_parent.children[1].visit_state = VisitState.VISITED
    mock_current_category_node = Mock()
    mock_current_category_node.parent = mock_current_category_parent

    mock_spider_state_instance = __prepare_mock_spider_instance(True)
    mock_spider_state_instance.site_structure.get_node_at_path.return_value = mock_current_category_node
    mock_spider_state_cls.return_value = mock_spider_state_instance

    mock_site_pager_cls_instance = Mock()
    mock_site_pager_cls.return_value = mock_site_pager_cls_instance

    spider = CategoryBasedSpider(Mock(), Mock(), data)
    spider.request_factory = mock_request_factory
    list(spider.start_requests())
    mock_site_pager_cls_instance.start.assert_called()

    site_page_callbacks = mock_site_pager_cls.call_args[0][3]
    site_page_callbacks.on_page_finished("http://some-recipes.com/next-page")
    site_page_callbacks.on_paging_finished()
    mock_spider_state_instance.save.assert_called()
    mock_current_category_parent.set_visit_state.assert_called()


@patch("scrapy_patterns.spiders.category_based_spider.SiteStructureDiscoverer")
@patch("scrapy_patterns.spiders.category_based_spider.SitePager")
@patch("scrapy_patterns.spiders.category_based_spider.CategoryBasedSpiderState")
def test_with_progress_start_requests_not_all_visited(mock_spider_state_cls, mock_site_pager_cls, _):
    """Tests spider start when progress file exists, and then after paging completed with not all categories visited."""
    data = CategoryBasedSpiderData("some-progress-file-dir", "some-spider-name", "http://some-recipes.com")
    mock_request_factory = Mock()

    mock_current_category_parent = Mock()
    mock_current_category_parent.parent = None
    mock_current_category_parent.children = [Mock(), Mock()]
    mock_current_category_parent.children[0].visit_state = VisitState.VISITED
    mock_current_category_parent.children[1].visit_state = VisitState.IN_PROGRESS
    mock_current_category_node = Mock()
    mock_current_category_node.parent = mock_current_category_parent

    mock_spider_state_instance = __prepare_mock_spider_instance(True)
    mock_spider_state_instance.site_structure.get_node_at_path.return_value = mock_current_category_node
    mock_spider_state_cls.return_value = mock_spider_state_instance

    mock_site_pager_cls_instance = Mock()
    mock_site_pager_cls.return_value = mock_site_pager_cls_instance

    spider = CategoryBasedSpider(Mock(), Mock(), data)
    spider.request_factory = mock_request_factory
    list(spider.start_requests())
    mock_site_pager_cls_instance.start.assert_called()

    site_page_callbacks = mock_site_pager_cls.call_args[0][3]
    site_page_callbacks.on_page_finished("http://some-recipes.com/next-page")
    site_page_callbacks.on_paging_finished()
    mock_current_category_parent.set_visit_state.assert_not_called()


def test_missing_values():
    """Tests missing values when constructing the spider."""
    data = CategoryBasedSpiderData("some-progress-file-dir", "some-spider-name", "http://some-recipes.com")

    with pytest.raises(ValueError):
        CategoryBasedSpider(Mock(), Mock(), None)

    with pytest.raises(ValueError):
        CategoryBasedSpider(Mock(), None, data)

    with pytest.raises(ValueError):
        data.start_url = None
        CategoryBasedSpider(Mock(), Mock(), data)


def __prepare_mock_spider_instance(is_loaded: bool):
    mock_spider_state_instance = Mock()
    mock_spider_state_instance.is_loaded = is_loaded
    return mock_spider_state_instance
