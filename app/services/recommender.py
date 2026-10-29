
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Movie, Rating


def recommend_for_user(
    db: Session,
    user_id: int,
    limit: int = 10,
) -> list[dict]:
    # Load ratings into a DataFrame.
    rows = db.execute(
        select(
            Rating.user_id,
            Rating.movie_id,
            Rating.rating,
        )
    ).all()

    if not rows:
        return []

    ratings_df = pd.DataFrame(
        rows,
        columns=["user_id", "movie_id", "rating"],
    )

    if user_id not in ratings_df["user_id"].values:
        return []

    # Rows are users; columns are movies.
    user_movie_matrix = ratings_df.pivot(
        index="user_id",
        columns="movie_id",
        values="rating",
    )

    # Fill missing ratings with zero for similarity calculation.
    matrix_filled = user_movie_matrix.fillna(0)

    similarities = cosine_similarity(matrix_filled)

    similarity_df = pd.DataFrame(
        similarities,
        index=matrix_filled.index,
        columns=matrix_filled.index,
    )

    # Find users most similar to the target user.
    similar_users = (
        similarity_df.loc[user_id]
        .drop(index=user_id)
        .sort_values(ascending=False)
    )

    # Only recommend movies the target user has not rated.
    rated_movies = set(
        ratings_df.loc[
            ratings_df["user_id"] == user_id,
            "movie_id",
        ]
    )

    candidate_scores = {}

    for similar_user_id, similarity in similar_users.head(20).items():
        if similarity <= 0:
            continue

        neighbor_ratings = ratings_df[
            (ratings_df["user_id"] == similar_user_id)
            & (~ratings_df["movie_id"].isin(rated_movies))
        ]

        for row in neighbor_ratings.itertuples():
            score, weight = candidate_scores.get(row.movie_id, (0.0, 0.0))
            candidate_scores[row.movie_id] = (
                score + similarity * row.rating,
                weight + similarity,
            )

    if not candidate_scores:
        return []

    ranked_candidates = sorted(
        candidate_scores.items(),
        key=lambda item: item[1][0] / item[1][1],
        reverse=True,
    )[:limit]

    results = []

    for movie_id, (weighted_score, total_weight) in ranked_candidates:
        movie = db.get(Movie, movie_id)

        if movie is None:
            continue

        results.append(
            {
                "movie_id": movie.id,
                "title": movie.title,
                "genres": movie.genres,
                "predicted_rating": round(weighted_score / total_weight, 2),
            }
        )

    return results
