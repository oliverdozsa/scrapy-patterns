"""Request factory tests"""
from scrapy_patterns.request_factory import RequestFactory


def test_create_request():
    """Tests the creation of a request through the factory."""
    req_factory = RequestFactory()

    def mock_callable():
        pass

    request = req_factory.create("http://www.some-mock-url.com", mock_callable)
    assert request is not None, "Failed to create request!"
