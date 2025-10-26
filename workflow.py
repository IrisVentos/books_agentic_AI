import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
import httpx
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from db_config import get_db, engine
from models.book import Book, Base
from scraping.goodreads import GoodreadsScraper
from schemas.book import BookSearchInfo

load_dotenv()

http_client_without_ssl_verification = httpx.AsyncClient(verify=False)

model = AnthropicModel(
    model_name="claude-3-5-sonnet-latest",
    provider=AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"), http_client=http_client_without_ssl_verification)
    
)


search_book_agent = Agent(
    model=model,
    output_type=BookSearchInfo,
    instructions= search_instructions,
    deps_type = BookContext,
)

data_quality_agent = Agent(
    model=model,
    output_type=DataQualityResult,
    instructions= data_quality_instructions,
    deps_type = BookContext,
)

async def extract_book_search_info(user_input: str) -> BookSearchInfo:
    """Extract book search information from user input"""
    result = await search_book_agent.run(user_input)
    return result.output


@search_book_agent.tool
async def search_and_scrape_books(search_query: str, max_results: int = 1):
    """Search and scrape books from Goodreads"""
    async with GoodreadsScraper() as scraper:
        print(f"\n🔍 Searching Goodreads for: {search_query}")

        # Search for books
        books = await scraper.search_books(search_query, max_results)

        if not books:
            print("No books found on Goodreads.")
            return []

        print(f"Found {len(books)} book{'s' if len(books) > 1 else ''}:")
        saved_books = []

        # Display and save each book
        for i, book in enumerate(books, 1):
            print(f"\n{i}. {book['title']} by {book['author']}")
            if book.get("rating"):
                print(f"   Rating: {book['rating']}")

            # Get more details if URL available
            if book.get("url"):
                details = await scraper.scrape_book_details(book["url"])
                if details:
                    book.update(details)

            # Save to database
            saved = scraper.save_to_database(book)
            if saved:
                saved_books.append(saved)

            await asyncio.sleep(1)  # Be polite

        return saved_books


async def process_user_input(user_input: str):
    """Process user input to either search Goodreads or save directly"""
    print(f"\n💭 Understanding your request...")

    try:
        # Extract information from user input
        book_info = await extract_book_search_info(user_input)
        print(f"✓ Extracted: {book_info.search_query}")
        print(f"  Action: {book_info.action}")
        await search_and_scrape_books(book_info.search_query, max_results=1)
        
    except Exception as e:
        print(f"Error: {e}")
        return None


async def main():
    """Main function - intelligent book search and save"""

    context = SharedContext()
    print("=" * 60)
    print("📚 Intelligent Book Manager")
    print("=" * 60)
    print("Enter your request (or 'quit' to exit):\n")

    while True:
        user_input = input("> ").strip()

        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        if user_input:
            await process_user_input(user_input)
            print("\n" + "-" * 60)
            print("Enter another request (or 'quit' to exit):")
        else:
            print("Please enter a valid request.")



if __name__ == "__main__":
    asyncio.run(main())