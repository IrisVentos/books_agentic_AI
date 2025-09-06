# 📚 Intelligent Book Manager

An AI-powered book management system that can search, scrape, and store book information using natural language processing.

## Features

- **Natural Language Understanding**: Describe what you want in plain language
- **Goodreads Scraping**: Automatically search and scrape book details from Goodreads
- **AI Extraction**: Uses Claude AI to understand and extract book information
- **SQLite Database**: Stores all book information locally

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Create a `.env` file with your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

## Usage

### Main Application
```bash
python main.py
```

Examples:
- "Find books about Python programming"
- "Search for 1984 by George Orwell"
- "I want to find The Great Gatsby"

### Direct Scraping
```bash
python -m scraping.cli
```

## Project Structure

```
├── main.py               # Main application with AI integration
├── db_config.py          # Database configuration
├── schemas/              # Pydantic schemas for AI processing
│   ├── __init__.py
│   └── book.py           # Book-related schemas
├── scraping/             # Scraping modules
│   ├── __init__.py
│   ├── goodreads.py      # Goodreads scraper
│   └── cli.py            # CLI interface for scraping
├── models/               # SQLAlchemy database models
│   ├── __init__.py
│   └── book.py           # Book database model
└── data/
    └── books.db          # SQLite database (created automatically)
```

## Technologies

- **pydantic-ai**: AI agent framework
- **SQLAlchemy**: Database ORM
- **BeautifulSoup4**: Web scraping
- **httpx**: Async HTTP client
- **Claude AI**: Natural language understanding