
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.database import Base, engine, get_db
from app.schemas import UserCreate, UserOut
from app.schemas import MovieCreate, MovieOut
from sqlalchemy import select, func
from app.schemas import RatingCreate, RatingOut,RecommendationOut
from app.services.recommender import recommend_for_user
from app.schemas import PersonalizedRecommendationOut

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    description="A personalized movie recommendation service.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "recommendation-api",
        "environment": settings.environment,
    }


@app.post(
    "/users",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    tags=["users"],
)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.scalar(
        select(models.User).where(
            (models.User.username == payload.username)
            | (models.User.email == payload.email)
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )

    user = models.User(
        username=payload.username,
        email=str(payload.email),
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )

    return user



@app.post(
    "/movies",
    response_model=MovieOut,
    status_code=status.HTTP_201_CREATED,
    tags=["movies"],
)
def create_movie(payload: MovieCreate, db: Session = Depends(get_db)):
    movie = models.Movie(
        title=payload.title,
        genres=payload.genres,
        description=payload.description,
    )

    db.add(movie)
    db.commit()
    db.refresh(movie)

    return movie


@app.get(
    "/movies/{movie_id}",
    response_model=MovieOut,
    tags=["movies"],
)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(models.Movie, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    return movie


@app.get(
    "/movies",
    response_model=list[MovieOut],
    tags=["movies"],
)
def list_movies(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")

    if offset < 0:
        raise HTTPException(status_code=422, detail="offset must be non-negative")

    statement = (
        select(models.Movie)
        .order_by(models.Movie.id)
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(statement).all())



@app.post(
    "/ratings",
    response_model=RatingOut,
    status_code=status.HTTP_201_CREATED,
    tags=["ratings"],
)
def create_rating(payload: RatingCreate, db: Session = Depends(get_db)):
    user = db.get(models.User, payload.user_id)
    movie = db.get(models.Movie, payload.movie_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    existing_rating = db.scalar(
        select(models.Rating).where(
            models.Rating.user_id == payload.user_id,
            models.Rating.movie_id == payload.movie_id,
        )
    )

    if existing_rating:
        raise HTTPException(
            status_code=409,
            detail="This user has already rated this movie",
        )

    rating = models.Rating(
        user_id=payload.user_id,
        movie_id=payload.movie_id,
        rating=payload.rating,
    )

    db.add(rating)

    try:
        db.commit()
        db.refresh(rating)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not save rating")

    return rating



@app.get(
    "/movies/{movie_id}/ratings",
    response_model=list[RatingOut],
    tags=["ratings"],
)
def get_movie_ratings(
    movie_id: int,
    db: Session = Depends(get_db),
):
    movie = db.get(models.Movie, movie_id)

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    statement = (
        select(models.Rating)
        .where(models.Rating.movie_id == movie_id)
        .order_by(models.Rating.id)
    )

    return list(db.scalars(statement).all())







@app.get(
    "/recommendations/popular",
    response_model=list[RecommendationOut],
    tags=["recommendations"],
)
def popular_recommendations(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    if not 1 <= limit <= 50:
        raise HTTPException(
            status_code=422,
            detail="limit must be between 1 and 50",
        )

    average_rating = func.avg(models.Rating.rating)
    rating_count = func.count(models.Rating.id)

    statement = (
        select(
            models.Movie.id.label("movie_id"),
            models.Movie.title,
            models.Movie.genres,
            average_rating.label("average_rating"),
            rating_count.label("rating_count"),
        )
        .join(models.Rating, models.Rating.movie_id == models.Movie.id)
        .group_by(
            models.Movie.id,
            models.Movie.title,
            models.Movie.genres,
        )
        .order_by(rating_count.desc(), average_rating.desc())
        .limit(limit)
    )

    rows = db.execute(statement).all()

    return [
        {
            "movie_id": row.movie_id,
            "title": row.title,
            "genres": row.genres,
            "average_rating": round(float(row.average_rating), 2),
            "rating_count": row.rating_count,
        }
        for row in rows
    ]



@app.get(
    "/recommendations/users/{user_id}",
    response_model=list[PersonalizedRecommendationOut],
    tags=["recommendations"],
)
def personalized_recommendations(
    user_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    if not 1 <= limit <= 50:
        raise HTTPException(
            status_code=422,
            detail="limit must be between 1 and 50",
        )

    if db.get(models.User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")

    return recommend_for_user(db, user_id=user_id, limit=limit)