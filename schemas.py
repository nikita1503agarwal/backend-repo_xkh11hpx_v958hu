"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Caption generator schemas
class Caption(BaseModel):
    """
    Captions collection schema
    Collection name: "caption"
    """
    topic: str = Field(..., description="Main topic or keywords for the caption")
    tone: str = Field("friendly", description="Tone/style: friendly, professional, witty, bold, luxury, casual, educational")
    platform: str = Field("instagram", description="Target platform: instagram, tiktok, twitter, linkedin, youtube")
    length: str = Field("medium", description="Caption length: short, medium, long")
    include_emojis: bool = Field(True, description="Whether to include emojis")
    include_hashtags: bool = Field(True, description="Whether to include hashtags")
    variants: List[str] = Field(default_factory=list, description="Generated caption options")
    favorite: bool = Field(False, description="User marked as favorite")

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
