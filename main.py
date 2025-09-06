import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from db_config import get_db, engine
from models.book import Book, Base
from scraping.goodreads import GoodreadsScraper
from schemas.book import BookSearchInfo

load_dotenv()

model = AnthropicModel(
    model_name="claude-3-5-sonnet-20241022",
    provider=AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY")),
)

agent = Agent(
    model=model,
    output_type=BookSearchInfo,
    instructions="""Extract book information from the user's input. 
    Determine if they want to:
    1. Search and scrape from Goodreads (action='search') - when they mention searching, finding, or scraping
    2. Save directly to database (action='save') - when they provide complete book info without mentioning search
    
    CRITICAL: Always fix spelling errors in book titles and author names before creating the search query.
    Pay special attention to:
    - Common book titles (Magellan not Maggelan, échecs not echecs)  
    - Author names (George not Goerge, Zweig, Orwell, etc.)
    - Accents in French words
    
    Create a search query preserving the ORIGINAL LANGUAGE but with CORRECTED spelling.
    DO NOT translate - only fix typos and spelling mistakes.

    If both title and author are mentioned, include both with corrected spelling.""",
)


async def extract_book_search_info(user_input: str) -> BookSearchInfo:
    """Extract book search information from user input"""
    result = await agent.run(user_input)
    return result.output


def save_book_to_db(title: str, author: str, description: str = None, url: str = None):
    """Save book information to database"""
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)

    db = next(get_db())
    try:
        new_book = Book(
            url=url or "manual_entry",
            title=title,
            author=author,
            description=description or "",
            scraped_at=datetime.now(),
            ai_processed_at=datetime.now() if description else None,
        )

        db.add(new_book)
        db.commit()
        db.refresh(new_book)

        print(
            f"✓ Book saved - ID: {new_book.id}, Title: {new_book.title}, Author: {new_book.author}"
        )
        return new_book

    finally:
        db.close()


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

        if book_info.action == "search":
            # Search and scrape from Goodreads
            await search_and_scrape_books(book_info.search_query, max_results=1)
        else:
            # Save directly if title and author are provided
            if book_info.title and book_info.author:
                saved_book = save_book_to_db(
                    title=book_info.title,
                    author=book_info.author,
                    description=user_input,
                )
                if saved_book:
                    print(f"✓ Book saved directly to database")
            else:
                print("Need more information to save. Searching Goodreads instead...")
                await search_and_scrape_books(book_info.search_query, max_results=1)

    except Exception as e:
        print(f"Error: {e}")
        return None


async def main():
    """Main function - intelligent book search and save"""

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
