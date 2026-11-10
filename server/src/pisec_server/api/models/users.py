"""File containing pydantic models for user data."""

from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field

from pisec_server.core.validation.regex import email_regex
from pisec_server.core.validation.user_validation import password_validator


class BaseUser(BaseModel):
    """Base User record/model. All except UserUpdate inherit from this class."""

    email: EmailStr = Field(pattern=email_regex)  # Rudimentary validation (won't check if email exists)


class UserWithPassword(BaseUser):
    """User record/model with password. Includes a validator for the password."""

    password: Annotated[str, AfterValidator(password_validator)]


class User(UserWithPassword):
    """Base User record/model."""

    id: int = Field(ge=1)

    class Config:
        """Config subclass of User."""

        from_attributes: bool = True


class UserCreate(UserWithPassword):
    """Request body input as a class for creating a new user."""



class UserUpdate(BaseModel):
    """Request body input as a class for updating a user's details."""

    email: EmailStr | None = Field(default=None, pattern=email_regex)
    password: Annotated[str | None, AfterValidator(password_validator)] = None


class UserResponse(BaseUser):
    """Used when returning to the user (removes sensitive info like passwords)."""

    id: int = Field(ge=1)
    is_admin: bool = Field(default=False)

    class Config:
        """Config subclass of UserResponse."""

        from_attributes: bool = True
