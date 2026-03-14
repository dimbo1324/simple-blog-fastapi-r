from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=150)


class UserRegister(UserBase):

    password: str = Field(
        min_length=8,
        max_length=72,
        description="Minimum of 8 characters",
    )


class UserLogin(BaseModel):

    username: str = Field(description="Username или email")
    password: str


class UserResponse(UserBase):

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    image_file: str | None
    image_path: str


class UserUpdate(BaseModel):

    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=150)
    image_file: str | None = Field(default=None, min_length=1, max_length=200)


class UserUpdatePassword(BaseModel):

    current_password: str
    new_password: str = Field(min_length=8, max_length=72)


class Token(BaseModel):

    access_token: str
    token_type: str = "bearer"


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date_posted: datetime
    author: UserResponse
