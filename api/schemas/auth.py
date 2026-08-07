import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class UserRegister(BaseModel):
    title: str | None = None
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8)
    confirm_password: str
    accept_terms: bool
    marketing_opt_in: bool = False

    @field_validator("accept_terms")
    @classmethod
    def must_accept_terms(cls, v: bool) -> bool:
        if not v:
            raise ValueError("You must accept the Conditions of Carriage and Privacy Policy to continue")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "UserRegister":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class GoogleOAuthRequest(BaseModel):
    id_token: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    title: str | None
    first_name: str
    last_name: str
    role: str
    is_email_verified: bool
    loyalty_tier: str
    loyalty_miles: int

    model_config = {"from_attributes": True}