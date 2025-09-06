"""Scraping module for book data extraction"""

from .goodreads import GoodreadsScraper, search_and_save

__all__ = ["GoodreadsScraper", "search_and_save"]