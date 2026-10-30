import re
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator

UserTypeEnum = Literal["Parent", "Student", "School"]
CategoryEnum = Literal["Scholarship", "Concert", "Admission", "General Query"]
StatusEnum = Literal["New", "In Progress", "Resolved"]


class InquiryCreate(BaseModel):
    user_type: UserTypeEnum
    category: CategoryEnum
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    phone: str = Field(..., min_length=7, max_length=50)
    message: str = Field(..., min_length=10, max_length=5000)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        return cleaned

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = v.strip()
        # Accept standard international phone formatting with digits, spaces, hyphens, plus, parens
        # E.g. +1 (555) 019-2834 or +91 98765 43210
        if not re.match(r"^[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9()]{6,30}$", cleaned):
            raise ValueError("Phone number must be a valid format with 7 to 30 digits/symbols.")
        return cleaned

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 10:
            raise ValueError("Message must be at least 10 characters long.")
        return cleaned


class InquiryStatusUpdate(BaseModel):
    status: StatusEnum


class InquiryResponse(BaseModel):
    id: str
    user_type: str
    category: str
    name: str
    email: str
    phone: str
    message: str
    status: str
    created_at: datetime
    updated_at: datetime


class InquiryListResponse(BaseModel):
    items: list[InquiryResponse]
    page: int
    limit: int
    total: int
    total_pages: int
