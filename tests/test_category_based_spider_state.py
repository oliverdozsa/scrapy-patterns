"""Contains tests for category based spider state."""
from unittest.mock import Mock, patch, mock_open
import pytest
from scrapy_patterns.spiders.private.category_based_spider_state import CategoryBasedSpiderState
from scrapy_patterns.site_structure import SiteStructure


@patch("scrapy_patterns.spiders.private.category_based_spider_state.json")
@patch("scrapy_patterns.spiders.private.category_based_spider_state.os")
def test_save_file_and_path_doesnt_exist(os_mock, json_mock):
    """Tests state saving with not existing progress file, and path."""
    os_mock.path.isfile.return_value = False
    os_mock.path.isdir.return_value = False
    state = CategoryBasedSpiderState("some_spider_name", "some_spider_path")
    state.site_structure = Mock()
    state.current_page_url = "http://some-recipe-site.com/some-category/page1"
    state.current_page_site_path = "Some Category"
    os_mock.path.join.assert_called_with("some_spider_path", "some_spider_name_progress.json")

    with patch("builtins.open", mock_open(read_data="some_data")):
        state.save()
        os_mock.mkdir.assert_called()
        json_mock.dump.assert_called()


@patch("scrapy_patterns.spiders.private.category_based_spider_state.os")
def test_site_structure_is_none(os_mock):
    """Tests that exception is raised when site structure is None"""
    os_mock.path.isfile.return_value = False
    os_mock.path.isdir.return_value = False
    state = CategoryBasedSpiderState("some_spider_name", "some_spider_path")
    state.site_structure = None

    with pytest.raises(RuntimeError):
        state.save()


@patch("scrapy_patterns.spiders.private.category_based_spider_state.json")
@patch("scrapy_patterns.spiders.private.category_based_spider_state.os")
def test_progress_file_exists(os_mock, json_mock):
    """Tests state creation when progress file exists."""
    os_mock.path.isfile.return_value = True
    os_mock.path.isdir.return_value = True
    with patch("builtins.open", mock_open(read_data="some_data")):
        json_mock.load.return_value = {
            "site_structure": SiteStructure("some-struct").to_dict(),
            "current_page_url": "http://some-recipe-site.com/some-category/page1",
            "current_page_site_path": "Some Category"
        }
        CategoryBasedSpiderState("some_spider_name", "some_spider_path")
        json_mock.load.assert_called()
