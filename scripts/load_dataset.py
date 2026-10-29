
import csv
from pathlib import Path

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Movie, Rating


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "ml-latest-small"


def load_dataset():
    movies_file = DATA_DIR / "movies.csv"
    ratings_file = DATA_DIR / "ratings.csv"

    if not movies_file.exists() or not ratings_file.exists():
        raise FileNotFoundError(
            f"Expected movies.csv and ratings.csv in {DATA_DIR}"
        )

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Import movies without duplicating existing titles.
        existing_titles = set(
            db.scalars(select(Movie.title)).all()
        )

        movie_id_map = {}

        with movies_file.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                title = row["title"].strip()
                genres = row["genres"].replace("|", ",")

                movie = db.scalar(
                    select(Movie).where(Movie.title == title)
                )

                if movie is None:
                    movie = Movie(title=title, genres=genres)
                    db.add(movie)
                    db.flush()

                movie_id_map[row["movieId"]] = movie.id

        # Commit movies before importing ratings.
        db.commit()

        # Map external MovieLens user IDs to local user IDs.
        from app.models import User

        user_id_map = {}
        next_user_number = 1
        seen_rating_pairs = set()
        with ratings_file.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                external_user_id = row["userId"]
                if external_user_id not in user_id_map:
                    username = f"movielens_user_{next_user_number}"
                    email = f"movielens_user_{next_user_number}@example.com"
                    next_user_number += 1

                    user = db.scalar(
                        select(User).where(User.username == username)
                    )

                    if user is None:
                        user = User(username=username, email=email)
                        db.add(user)
                        db.flush()

                    user_id_map[external_user_id] = user.id

                movie_id = movie_id_map.get(row["movieId"])
                if movie_id is None:
                    continue

                rating_pair = (user_id_map[external_user_id], movie_id)

                if rating_pair in seen_rating_pairs:
                     continue

                existing_rating = db.scalar(
                    select(Rating).where(
                        Rating.user_id == rating_pair[0],
                        Rating.movie_id == rating_pair[1],
                    )
                )

                if existing_rating is None:
                    db.add(
                        Rating(
                            user_id=rating_pair[0],
                            movie_id=rating_pair[1],
                            rating=float(row["rating"]),
                        )
                    )

                seen_rating_pairs.add(rating_pair)

        db.commit()

        print(f"Dataset loaded successfully.")
        print(f"Movies in database: {db.query(Movie).count()}")
        print(f"Users in database: {db.query(User).count()}")
        print(f"Ratings in database: {db.query(Rating).count()}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_dataset()
