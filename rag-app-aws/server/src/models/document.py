from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import numpy as np


class RetrievedDocument(BaseModel):
    id: int
    title: str
    chunk: str
    similarity_score: float

    model_config = ConfigDict(from_attributes=True)  # Replaces orm_mode=True


class Document(BaseModel):
    id: Optional[
        int
    ] = None  # Unique identifier for the document, typically set by the database
    title: str = Field(..., description="The title of the document")
    summary: str = Field(..., description="A summary or abstract of the document")
    chunks: List[str] = Field(
        ..., description="A list of text chunks derived from the document"
    )
    embeddings: List[List[float]] = Field(
        ..., description="A list of embeddings for each chunk"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Optional metadata associated with the document, such as publication date, authors, or tags",
    )

    model_config = ConfigDict(from_attributes=True)  # Replaces orm_mode=True
