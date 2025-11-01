import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
import httpx
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from db_config import get_db, engine
from models.book import Book, Base
from scraping.goodreads import GoodreadsScraper
from schemas.book import BookSearchInfo

load_dotenv()

http_client_without_ssl_verification = httpx.AsyncClient(verify=False)

ANTHROPIC_API_KEY : str= os.getenv("ANTHROPIC_API_KEY","")
MODEL_NAME: str = "claude-3-5-sonnet-latest"
MAX_SEARCH_RESULTS: int = 1
SCRAPING_DELAY: float = 1.0

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

async def extract_book_search_info(user_input: str, context : BookContext) -> BookSearchInfo:
    """Extract book search information from user input"""
    result = await search_book_agent.run(user_input,deps=context)
    return result.output

@search_book_agent.tool
async def search_and_scrape_books(
    ctx: RunContext[BookContext],
    search_query: str, 
    max_results: int = MAX_SEARCH_RESULTS,
) -> dict[str, any]:
    if i == 1:  # First book
        ctx.deps.book_details = details
    except Exception as e:
        error_msg = f"Scraping error: {str(e)}"
        ctx.deps.scraping_errors.append(error_msg)
        return {"error": error_msg, "books": []}

if i == 1:
    ctx.deps.book_details = details
    
    # Print detailed book information
    print(f"\n{'=' * 60}")
    print(f"BOOK DETAILS")
    print(f"{'=' * 60}")
    print(f"Title: {details.get('title', 'N/A')}")
    print(f"Author: {details.get('author', 'N/A')}")
    
    if details.get("rating"):
        print(f"Rating: {details.get('rating')}")
    
    if details.get("description"):
        desc = details.get("description", "")[:200]
        print(f"Description: {desc}...")
    
    if details.get("genres"):
        print(f"Genres: {', '.join(details.get('genres', []))}")
    
    if details.get("pages"):
        print(f"Pages: {details.get('pages')}")
    
    if details.get("published_date"):
        print(f"Published: {details.get('published_date')}")
    
    if details.get("isbn"):
        print(f"ISBN: {details.get('isbn')}")
    
    print(f"{'=' * 60}\n")


@data_quality_agent.tool
async def validate_book_data(ctx: RunContext[BookContext]) -> DataQualityResult:
    """Validate the quality of scraped book data."""
    if not ctx.deps.book_details:
        return DataQualityResult(
            valid=False,
            issues=["No book data available"],
            quality_score=0,
            message="No book data to validate",
        )
    
    book = ctx.deps.book_details
    issues = []
    
    # Check required fields
    required_fields = ["title", "author"]
    for field in required_fields:
        if not book.get(field):
            issues.append(f"Missing {field}")
    
    # Validate rating if present
    if book.get("rating"):
        try:
            rating = float(book["rating"])
            if not (0 <= rating <= 5):
                issues.append("Invalid rating value")
        except (ValueError, TypeError):
            issues.append("Rating is not a valid number")
    
    ctx.deps.is_data_quality_checked = True
    
    quality_score = max(0, 100 - len(issues) * 20)
    valid = len(issues) == 0
    
    return DataQualityResult(
        valid=valid,
        issues=issues,
        quality_score=quality_score,
        message=f"Data quality: {'Valid' if valid else 'Issues found'}",
    )

@search_book_agent.tool
async def request_data_quality_check(ctx: RunContext[BookContext]) -> dict[str, Any]:
    """
    Request the data quality agent to validate the scraped book data.
    Call this after successfully scraping book data to ensure quality.
    """
    if not ctx.deps.book_details:
        return {"error": "No book data to validate"}
    
    print("\nRequesting data quality validation...")
    
    # Delegate to the quality agent
    quality_result = await data_quality_agent.run(
        "Validate the scraped book data",
        deps=ctx.deps
    )
    
    print(f"Quality: {quality_result.output.message}")
    
    if quality_result.output.issues:
        print(f"Issues found: {', '.join(quality_result.output.issues)}")
    
    return {
        "valid": quality_result.output.valid,
        "quality_score": quality_result.output.quality_score,
        "issues": quality_result.output.issues,
    }

async def process_user_input(user_input: str) -> BookContext:
    """Process user input - agents handle their own workflow."""
    print(f"\n💭 Understanding your request...")

    context = BookContext()

    try:
        book_info = await extract_book_search_info(user_input, context)
        print(f"✓ Extracted: {book_info.search_query}")
        print(f"  Action: {book_info.action}")

        return context
            
    except Exception as e:
        print(f"Error: {e}")
        context.scraping_errors.append(str(e))
        return context


async def main():
    """Main function - intelligent book search"""

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
            context = await process_user_input(user_input)

            if context.book_details:
                print ("\n Success!")
            if context.scraping_errors:
                print (f"\n Encountered {len(context.scraping_errors)} error(s)")

            print("\n" + "-" * 60)
            print("Enter another request (or 'quit' to exit):")
        else:
            print("Please enter a valid request.")


if __name__ == "__main__":
    asyncio.run(main())