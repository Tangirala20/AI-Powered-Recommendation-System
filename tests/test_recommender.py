
from app.services.recommender import recommend_for_user


def test_recommendations_return_valid_movies(db_session, sample_user):
    recommendations = recommend_for_user(
        db=db_session,
        user_id=sample_user.id,
        limit=5,
    )

    assert len(recommendations) <= 5

    movie_ids = [item["movie_id"] for item in recommendations]
    assert len(movie_ids) == len(set(movie_ids))

    for item in recommendations:
        assert item["title"]
        assert 0.5 <= item["predicted_rating"] <= 5.0
