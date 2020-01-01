"""Contains the default request factory"""
from typing import Callable
from scrapy import Request


class RequestFactory:
    """
    Instances of this class produces Scrapy requests. This is the default factory, which creates Scrapy Requests.
    Inherit from this class to create your own requests if needed (e.g. if you you use scrapy-selenium).
    """

    @staticmethod
    def create(url: str, callback: Callable, **kwargs) -> Request:
        """
        Creates a Scrapy Request.

        @param url: The url.
        @param callback: The callback function. See Scrapy docs.
        @param kwargs: Keyword arguments passed to the request.
        @return: A Request instance.
        """
        return Request(url=url, callback=callback, **kwargs)
