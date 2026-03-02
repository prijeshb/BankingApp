from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone_number: Optional[str]
    date_of_birth: Optional[date]
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone_number: Optional[str] = Field(
        None, max_length=20, pattern=r"^\+?[0-9\s\-]{7,20}$"
    )
    date_of_birth: Optional[date] = None

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_in_future(cls, v: date | None) -> date | None:
        if v is not None and v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v
