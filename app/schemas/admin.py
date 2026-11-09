from pydantic import BaseModel, Field


class AdminLogin(BaseModel):
    api_key: str = Field(min_length=1, max_length=512)


class AdminSessionOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
