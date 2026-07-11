import logging
from fastapi import APIRouter
from app.models.schemas import MovieResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/movie', tags=['Movie'])

# Static movie knowledge base (extend with OMDB/TMDB API if needed)
MOVIE_DB = {
    '500 days of summer': {
        'title': '500 Days of Summer', 'year': 2009, 'rating': 7.7,
        'genre': ['Romance', 'Comedy', 'Drama'],
        'director': 'Marc Webb',
        'cast': ['Joseph Gordon-Levitt', 'Zooey Deschanel', 'Geoffrey Arend'],
        'plot': 'A man reflects on his failed relationship with a woman who did not believe in love.',
        'runtime': '1h 35m',
        'awards': 'Independent Spirit Award — Best Editing',
    },
    'inception': {
        'title': 'Inception', 'year': 2010, 'rating': 8.8,
        'genre': ['Sci-Fi', 'Action', 'Thriller'],
        'director': 'Christopher Nolan',
        'cast': ['Leonardo DiCaprio', 'Joseph Gordon-Levitt', 'Elliot Page'],
        'plot': 'A thief who steals corporate secrets through the use of dream-sharing technology.',
        'runtime': '2h 28m',
        'awards': '4 Academy Awards including Best Cinematography',
    },
    'interstellar': {
        'title': 'Interstellar', 'year': 2014, 'rating': 8.7,
        'genre': ['Sci-Fi', 'Drama', 'Adventure'],
        'director': 'Christopher Nolan',
        'cast': ['Matthew McConaughey', 'Anne Hathaway', 'Jessica Chastain'],
        'plot': "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
        'runtime': '2h 49m',
        'awards': 'Academy Award for Best Visual Effects',
    },
}


@router.get('', response_model=MovieResponse)
async def get_movie(title: str):
    """
    Return movie details for a given title.
    Searches local database; extend with OMDB/TMDB for full coverage.
    """
    key = title.lower().strip()
    for db_key, movie in MOVIE_DB.items():
        if db_key in key or key in db_key:
            return MovieResponse(**movie)

    # Fallback: return minimal info
    logger.info(f'[/movie] Not in local DB: {title}')
    return MovieResponse(
        title = title,
        plot  = f'Detailed information for "{title}" is not available in the local database.',
    )


@router.get('/list', tags=['Movie'])
async def list_movies():
    """List all movies in the local database."""
    return {'movies': [v['title'] for v in MOVIE_DB.values()], 'total': len(MOVIE_DB)}
