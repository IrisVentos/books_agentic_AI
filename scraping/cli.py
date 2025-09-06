#!/usr/bin/env python
"""
CLI tool for scraping books from Goodreads
Usage: python -m scraping.cli
"""

import asyncio
import sys
from .goodreads import search_and_save


async def interactive_mode():
    """Interactive CLI for searching and scraping books"""
    print("=" * 60)
    print("📚 Goodreads Book Scraper")
    print("=" * 60)
    print("Commands:")
    print("  - Enter a search query to find books")
    print("  - Type 'quit' to exit")
    print("-" * 60)

    while True:
        query = input("\nSearch for books > ").strip()

        if query.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        if not query:
            print("Please enter a search query.")
            continue

        # Ask for number of results
        try:
            max_results = input("How many results? (default: 3) > ").strip()
            max_results = int(max_results) if max_results else 3
            max_results = min(max_results, 10)  # Limit to 10 results
        except ValueError:
            max_results = 3

        await search_and_save(query, max_results)


async def batch_mode(queries: list):
    """Batch mode for scraping multiple queries"""
    print(f"Batch scraping {len(queries)} queries...")

    for query in queries:
        await search_and_save(query, max_results=3)
        await asyncio.sleep(2)  # Be polite between queries


async def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Batch mode with command line arguments
        queries = sys.argv[1:]
        await batch_mode(queries)
    else:
        # Interactive mode
        await interactive_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
