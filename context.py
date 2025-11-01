#Shared context for all agents to coordinate and have same starting point
#for now, to ensure communication between search agent & quality agent
#using hint 

from pydantic import BaseModel, Field
from typing import Optional


class DataQualityResult(BaseModel):
    """Result of data quality validation check"""
    valid: bool
    issues: list[str] = Field(default_factory=list)
    quality_score: int = Field(ge=0, le=10, description="Quality score from 0 to 10")
    message: str


class BookContext(BaseModel):
    """Shared context passed between agents for book processing"""
    book_details: dict
    is_data_quality_checked: bool = False
    data_quality_result: Optional[DataQualityResult] = None
    scraping_errors: str = ""