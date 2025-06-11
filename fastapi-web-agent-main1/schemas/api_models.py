# ==============================================================================
# File: schemas/api_models.py
# ==============================================================================

from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional

# --- Sub-models for nested data structures ---

class SocialMedia(BaseModel):
    """Defines the structure for social media links."""
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    facebook: Optional[str] = None
    instagram: Optional[str] = None

class ContactInfo(BaseModel):
    """Defines the structure for contact information."""
    email: Optional[str] = None
    phone: Optional[str] = None
    social_media: SocialMedia = Field(default_factory=SocialMedia)

class SentimentInfo(BaseModel):
    """Defines the structure for sentiment analysis results."""
    overall: str
    confidence: float
    key_themes: List[str] = Field(default_factory=list)

class CompanyInfo(BaseModel):
    """The core model for all extracted company details."""
    industry: str = "N/A"
    company_size: str = "N/A"
    location: str = "N/A"
    core_products_services: List[str] = Field(default_factory=list)
    unique_selling_proposition: str = "N/A"
    target_audience: str = "N/A"
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    sentiment: Optional[SentimentInfo] = None

class ExtractedAnswer(BaseModel):
    """A model for a specific question and its AI-generated answer."""
    question: str
    answer: str

class ConversationTurn(BaseModel):
    """Represents a single turn (user question + agent response) in a conversation."""
    user_query: str
    agent_response: str


# --- API Request and Response Models ---

class AnalysisRequest(BaseModel):
    """The request model for the /analyze endpoint."""
    url: HttpUrl  # Pydantic will automatically validate this is a valid URL
    questions: Optional[List[str]] = None

class AnalysisResponse(BaseModel):
    """The response model for the /analyze endpoint."""
    url: str
    analysis_timestamp: str
    company_info: CompanyInfo
    extracted_answers: List[ExtractedAnswer] = Field(default_factory=list)

class ChatRequest(BaseModel):
    """The request model for the /chat endpoint."""
    url: HttpUrl
    query: str
    conversation_history: List[ConversationTurn] = Field(default_factory=list)

class ChatResponse(BaseModel):
    """The response model for the /chat endpoint."""
    url: str
    user_query: str
    agent_response: str
    context_sources: Optional[List[str]] = None