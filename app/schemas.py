
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- User schemas ----------

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Movie schemas ----------

class MovieCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    genres: str = Field(default="Unknown", max_length=300)
    description: str | None = None


class MovieOut(BaseModel):
    id: int
    title: str
    genres: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)


# ---------- Rating schemas ----------

class RatingCreate(BaseModel):
    user_id: int = Field(gt=0)
    movie_id: int = Field(gt=0)
    rating: float = Field(ge=0.5, le=5.0)


class RatingOut(BaseModel):
    id: int
    user_id: int
    movie_id: int
    rating: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class RecommendationOut(BaseModel):
    movie_id: int
    title: str
    genres: str
    average_rating: float
    rating_count: int


class PersonalizedRecommendationOut(BaseModel):
    movie_id: int
    title: str
    genres: str
    predicted_rating: float