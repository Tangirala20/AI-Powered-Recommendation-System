# AI-Powered Recommendation API

A movie recommendation system built using Python and FastAPI. The application stores users, movies, and ratings in a SQLite database and generates movie recommendations using collaborative filtering and cosine similarity.

## Technologies Used

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pandas
- Scikit-learn
- Pydantic
- Pytest

## Features

- Create and retrieve users and movies
- Store movie ratings
- Retrieve ratings for individual movies
- Generate popular movie recommendations
- Generate personalized recommendations using user similarity
- Validate API requests using Pydantic
- Interactive API documentation using Swagger UI

## Dataset

The project uses the MovieLens Latest Small dataset, containing movie metadata and user ratings.

Download: https://files.grouplens.org/datasets/movielens/ml-latest-small.zip

## Installation

Clone the repository and navigate to the project directory.

```bash
git clone <your-repository-url>
cd "AI Powered Recommendation API"
```

Create and activate a virtual environment.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies.

```bash
pip install -r requirements.txt
```

## Run the Application

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to explore and test the API using Swagger UI.

## Project Structure

```text
app/
    main.py
    config.py
    database.py
    models.py
    schemas.py
    services/
        recommender.py
scripts/
    load_dataset.py
data/
    ml-latest-small/
tests/
recommendations.db
requirements.txt
README.md
```

## Recommendation Approach

The application provides popularity-based recommendations using average movie ratings and rating counts. It also implements user-based collaborative filtering, using cosine similarity to identify users with similar rating patterns and recommend movies they have not rated.

The recommendation algorithm is an initial implementation and requires further evaluation and optimization.

## Future Improvements

- Matrix factorization and additional recommendation algorithms
- Recommendation quality evaluation
- Automated test coverage
- PostgreSQL support
- Docker deployment and CI/CD
