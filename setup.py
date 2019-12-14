"""This module contains the packaging"""

from setuptools import setup, find_packages

setup(
    packages=find_packages(),
    install_requires=['scrapy>=1.0.0']
)
