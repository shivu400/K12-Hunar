from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=72)


class AdminResponse(BaseModel):
    id: str
    email: str


class LoginResponse(BaseModel):
    message: str
    admin: AdminResponse


class LogoutResponse(BaseModel):
    message: str
