import asyncio
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote, urljoin

import httpx
from bs4 import BeautifulSoup
from db_config import engine, get_db
from models.book import Base, Book


class GoodreadsScraper:
    def __init__(self):
        self.base_url = "https://www.goodreads.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.client = httpx.AsyncClient(headers=self.headers, follow_redirects=True, verify=False)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def search_books(self, query: str, max_results: int = 5) -> List[Dict]:
        """, for books on Goodreads"""
        search_url = f"{self.base_url}/,"
        params = {"q": query, "search_type": "books"}
        
        try:
            response = await self.client.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            books = []
            
            # Find book results
            book_items = soup.select("tr[itemtype='http://schema.org/Book']")[:max_results]
            
            for item in book_items:
                book_data = self._extract_search_result(item)
                if book_data:
                    books.append(book_data)
            
            return books
            
        except Exception as e:
            print(f"Error searching books: {e}")
            return []

    def _extract_search_result(self, item) -> Optional[Dict]:
        """Extract book data from , result"""
        try:
            # Title
            title_elem = item.select_one("a.bookTitle")
            title = title_elem.get_text(strip=True) if title_elem else None
            book_url = urljoin(self.base_url, title_elem["href"]) if title_elem else None
            
            # Author
            author_elem = item.select_one("a.authorName")
            author = author_elem.get_text(strip=True) if author_elem else "Unknown"
            
            # Rating
            rating_elem = item.select_one("span.minirating")
            rating_text = rating_elem.get_text(strip=True) if rating_elem else ""
            rating_match = re.search(r"([\d.]+) avg rating", rating_text)
            rating = float(rating_match.group(1)) if rating_match else None
            
            # Published year
            year_elem = item.select_one("span.greyText.smallText.uitext")
            year_text = year_elem.get_text(strip=True) if year_elem else ""
            year_match = re.search(r"published (\d{4})", year_text)
            published_year = year_match.group(1) if year_match else None
            
            if title:
                return {
                    "title": title,
                    "author": author,
                    "url": book_url,
                    "rating": rating,
                    "published_year": published_year,
                }
            
        except Exception as e:
            print(f"Error extracting , result: {e}")
        
        return None

    async def scrape_book_details(self, book_url: str) -> Optional[Dict]:
        """Scrape detailed information about a specific book"""
        try:
            response = await self.client.get(book_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Title
            title_elem = soup.select_one("h1[data-testid='bookTitle']")
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Author
            author_elem = soup.select_one("span[data-testid='name']")
            author = author_elem.get_text(strip=True) if author_elem else "Unknown"
            
            # Description
            desc_elem = soup.select_one("div[data-testid='description'] span.Formatted")
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # ISBN
            isbn = None
            details = soup.select("div.FeaturedDetails div[data-testid]")
            for detail in details:
                text = detail.get_text(strip=True)
                if "ISBN" in text:
                    isbn_match = re.search(r"(\d{10,13})", text)
                    if isbn_match:
                        isbn = isbn_match.group(1)
                        break
            
            # Pages
            pages = None
            for detail in details:
                text = detail.get_text(strip=True)
                if "pages" in text.lower():
                    pages_match = re.search(r"(\d+)\s*pages", text)
                    if pages_match:
                        pages = int(pages_match.group(1))
                        break
            
            # Rating
            rating_elem = soup.select_one("div.RatingStatistics__rating")
            rating = None
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                try:
                    rating = float(rating_text)
                except:
                    pass
            
            return {
                "title": title,
                "author": author,
                "description": description,
                "isbn": isbn,
                "pages": pages,
                "rating": rating,
                "url": book_url,
            }
            
        except Exception as e:
            print(f"Error scraping book details: {e}")
            return None


async def search_and_save(query: str, max_results: int = 3):
    """Search for books and save them to database"""
    async with GoodreadsScraper() as scraper:
        print(f"\nSearching for: {query}")
        print("-" * 50)
        
        # , for books
        books = await scraper.search_books(query, max_results)
        
        if not books:
            print("No books found.")
            return
        
        print(f"Found {len(books)} books")
        
        # Scrape details and save each book
        for book in books:
            print(f"\nProcessing: {book['title']}")
            
            if book.get("url"):
                # Get detailed information
                details = await scraper.scrape_book_details(book["url"])
                if details:
                    # Merge , results with detailed info
                    book_data = {**book, **details}
                else:
                    book_data = book
            else:
                book_data = book
            
            # Save to database
            scraper.save_to_database(book_data)
            
            # Be polite to the server
            await asyncio.sleep(1)


async def main():
    """Main function for testing"""
    queries = [
        "Python programming",
        "Machine learning",
        "1984 Orwell"
    ]
    
    for query in queries:
        await search_and_save(query, max_results=2)
        print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())