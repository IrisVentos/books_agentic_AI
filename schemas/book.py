"""Book-related Pydantic schemas for AI processing"""

from typing import Optional
from pydantic import BaseModel, Field


class BookSearchInfo(BaseModel):
    """Model for extracting book search information from user input"""

    title: Optional[str] = Field(None, description="Book title to search for")
    author: Optional[str] = Field(None, description="Author name to search for")
    search_query: str = Field(
        description="Search query for finding the book on Goodreads"
    )
    action: str = Field(
        description="Action to perform: 'search' for scraping from Goodreads, or 'save' for direct saving"
    )