#dedicated validation agent using Pydantic AI

from pydantic import BaseModel, Field
from pydantic_ai import Agent

class BookValidation(BaseModel):
    is_valid: bool = Field(description="Whether the book data is valid")
    quality_score: float = Field(description="Quality score from 0-1")
    issues: List[str] = Field(description="List of data quality issues found")
    suggestions: List[str] = Field(description="Suggestions to improve data quality")

validation_agent = Agent(
    model=model,
    output_type=BookValidation,
    instructions="""You are a book data quality validator. Analyze the provided book data and check:
    
    1. Completeness: Are critical fields present (title, author, ISBN, description)?
    2. Accuracy: Do values make sense (rating 0-5, reasonable page count)?
    3. Consistency: Does author name format look correct?
    4. Reliability: Does the description look real or like a scraping error?
    
    Provide a quality score (0-1) and actionable suggestions."""
)

async def validate_with_ai(book_data: Dict) -> BookValidation:
    """Use AI to validate book data quality"""
    result = await validation_agent.run(
        f"Validate this book data: {book_data}"
    )
    return result.output