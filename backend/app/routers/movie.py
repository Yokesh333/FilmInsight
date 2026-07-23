"""
movie.py — Movie metadata router for FilmInsight.

Fetches live data from TMDb and OMDb APIs:
  • Posters, backdrops, overview
  • IMDb rating, genre, runtime, director, cast
  • Quotes (from OMDb / curated set)
  • Trivia facts
  • /movie/details   — full rich metadata
  • /movie/popular   — list of popular movies with posters
  • /movie           — basic lookup (legacy)
  • /movie/list      — list known titles
"""

import asyncio
import logging
import httpx
from fastapi import APIRouter, Query, HTTPException, Depends
from app.core.config import get_settings
from app.models.schemas import MovieResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/movie', tags=['Movie'])

# ── API config ────────────────────────────────────────────────────────────────
TMDB_BASE   = "https://api.themoviedb.org/3"
TMDB_IMG    = "https://image.tmdb.org/t/p/w500"
TMDB_IMG_HD = "https://image.tmdb.org/t/p/original"
OMDB_BASE   = "http://www.omdbapi.com/"
TIMEOUT     = httpx.Timeout(12.0)

# ── Curated trivia & quotes per movie (supplement API data) ──────────────────
MOVIE_EXTRAS = {
    "inception": {
        "trivia": [
            "The film took Christopher Nolan 10 years to write.",
            "The spinning top at the end was Cobb's dead wife's totem — not his own.",
            "Hans Zimmer slowed Édith Piaf's 'Non, je ne regrette rien' to create the score.",
            "The hallway fight scene required a set built on a rotating gimbal.",
            "Joseph Gordon-Levitt trained for months for the zero-gravity corridor fight.",
        ],
        "quotes": [
            {"text": "You mustn't be afraid to dream a little bigger, darling.", "speaker": "Eames"},
            {"text": "An idea is like a virus, resilient, highly contagious.", "speaker": "Cobb"},
            {"text": "What is the most resilient parasite? An idea.", "speaker": "Cobb"},
            {"text": "I can't imagine you with a totem.", "speaker": "Ariadne"},
            {"text": "Inception. Is it possible?", "speaker": "Saito"},
        ],
    },
    "interstellar": {
        "trivia": [
            "Matthew McConaughey's tears in the film were genuine; the scene took one take.",
            "NASA scientists consulted on the film to ensure scientific accuracy.",
            "The wormhole and black hole visuals were created with new astrophysics software.",
            "Hans Zimmer recorded the score before seeing the finished film.",
            "The cornfield used 500 acres of real corn grown for the production.",
        ],
        "quotes": [
            {"text": "We used to look up at the sky and wonder at our place in the stars.", "speaker": "Cooper"},
            {"text": "Do not go gentle into that good night.", "speaker": "Brand"},
            {"text": "Love is the one thing we're capable of perceiving that transcends time.", "speaker": "Brand"},
            {"text": "Mankind was born on Earth. It was never meant to die here.", "speaker": "Cooper"},
            {"text": "We've always defined ourselves by the ability to overcome the impossible.", "speaker": "Cooper"},
        ],
    },
    "500 days of summer": {
        "trivia": [
            "The film is not a love story, according to the opening title card.",
            "Zooey Deschanel's natural hair color influenced Summer's character design.",
            "The IKEA scene was partly improvised by the two leads.",
            "The non-linear structure was inspired by Annie Hall.",
            "Joseph Gordon-Levitt has said Tom is not the hero of the story.",
        ],
        "quotes": [
            {"text": "I'm not easy to understand, Tom. And you can't figure me out by watching me walk.", "speaker": "Summer"},
            {"text": "Most days of the year are unremarkable.", "speaker": "Narrator"},
            {"text": "I love how she makes me feel, like anything's possible.", "speaker": "Tom"},
            {"text": "I just... I just woke up one day and I knew.", "speaker": "Summer"},
            {"text": "You know what's weird? I don't feel that bad.", "speaker": "Tom"},
        ],
    },
    "the dark knight": {
        "trivia": [
            "Heath Ledger stayed in a hotel room for six weeks to develop the Joker's character.",
            "The Joker's 'magic trick' pencil scene was not in the original script.",
            "The film was the first Batman movie to not have 'Batman' in the title.",
            "Christopher Nolan used real IMAX cameras for 28 minutes of footage.",
            "Heath Ledger kept a 'Joker diary' documenting the character's psychology.",
        ],
        "quotes": [
            {"text": "Why so serious?", "speaker": "The Joker"},
            {"text": "Some men just want to watch the world burn.", "speaker": "Alfred"},
            {"text": "You either die a hero, or you live long enough to see yourself become the villain.", "speaker": "Harvey Dent"},
            {"text": "This city deserves a better class of criminal.", "speaker": "The Joker"},
            {"text": "I believe whatever doesn't kill you simply makes you... stranger.", "speaker": "The Joker"},
        ],
    },
    "memento": {
        "trivia": [
            "Christopher Nolan wrote the screenplay while working as a bank teller.",
            "The film was shot chronologically, but edited in reverse for the audience.",
            "Guy Pearce wore contact lenses to play a character with short-term memory loss.",
            "The film's structure mirrors Leonard's fractured memory: B&W forward, colour backward.",
            "Nolan's brother Jonathan wrote the original short story 'Memento Mori'.",
        ],
        "quotes": [
            {"text": "Memory can change the shape of a room.", "speaker": "Leonard"},
            {"text": "I have to believe that my actions still have meaning.", "speaker": "Leonard"},
            {"text": "How am I supposed to heal if I can't feel time?", "speaker": "Leonard"},
            {"text": "We all need mirrors to remind ourselves who we are.", "speaker": "Leonard"},
            {"text": "Just because there are things I don't remember doesn't make my actions meaningless.", "speaker": "Leonard"},
        ],
    },
    "tenet": {
        "trivia": [
            "Christopher Nolan shot the film in 70mm for maximum visual impact.",
            "The inverted action sequences required actors to learn moves backwards.",
            "The word 'Tenet' is a palindrome — it reads the same forwards and backwards.",
            "John David Washington performed many of his own stunts.",
            "The film was shot across seven countries over 87 days.",
        ],
        "quotes": [
            {"text": "Don't try to understand it. Feel it.", "speaker": "Protagonist"},
            {"text": "What's happened, happened.", "speaker": "Neil"},
            {"text": "You have a future in the past.", "speaker": "Ives"},
            {"text": "We live in a twilight world.", "speaker": "Protagonist"},
            {"text": "Ignorance is our ammunition.", "speaker": "Neil"},
        ],
    },
    "oppenheimer": {
        "trivia": [
            "Cillian Murphy lost considerable weight to portray Oppenheimer.",
            "The Trinity test was recreated practically without CGI.",
            "Christopher Nolan refused to use CGI for the nuclear explosion.",
            "The film is based on the Pulitzer Prize-winning biography 'American Prometheus'.",
            "Florence Pugh learned to play the ukulele for her role.",
        ],
        "quotes": [
            {"text": "Now I am become Death, the destroyer of worlds.", "speaker": "Oppenheimer"},
            {"text": "We imagined we might make a thing that would end all wars.", "speaker": "Oppenheimer"},
            {"text": "Theory will only take you so far.", "speaker": "Oppenheimer"},
            {"text": "I don't know if we can be trusted with such a weapon.", "speaker": "Oppenheimer"},
            {"text": "The world is changed. I feel it in the water.", "speaker": "Oppenheimer"},
        ],
    },
    "the dark knight rises": {
        "trivia": [
            "Tom Hardy developed a unique voice for Bane inspired by an Irish traveller.",
            "The film was shot partly in New York City, Pittsburgh, and Los Angeles.",
            "Christian Bale wore a new Batsuit with over 110 individual pieces.",
            "The prologue was shot in IMAX and released before Mission: Impossible — Ghost Protocol.",
            "The pit prison scenes were shot in an actual underground cistern in Jodhpur, India.",
        ],
        "quotes": [
            {"text": "Rise.", "speaker": "Bane"},
            {"text": "You merely adopted the dark. I was born in it.", "speaker": "Bane"},
            {"text": "The night is darkest just before the dawn.", "speaker": "Harvey Dent / Batman"},
            {"text": "Peace has cost you your strength. Victory has defeated you.", "speaker": "Bane"},
            {"text": "A hero can be anyone.", "speaker": "Batman"},
        ],
    },
    "batman begins": {
        "trivia": [
            "Christian Bale was cast as Batman after an audition in Val Kilmer's Batsuit.",
            "Christopher Nolan deliberately set the film in an unnamed but very real-feeling city.",
            "Liam Neeson trained with real martial arts masters to portray Ra's al Ghul.",
            "The Tumbler Batmobile was a fully functional vehicle built from scratch.",
            "Michael Caine based Alfred's warmth on his own real-life father.",
        ],
        "quotes": [
            {"text": "Why do we fall? So we can learn to pick ourselves up.", "speaker": "Thomas Wayne"},
            {"text": "It's not who I am underneath, but what I do that defines me.", "speaker": "Bruce Wayne"},
            {"text": "You have to become a terrible thought. A wraith.", "speaker": "Ra's al Ghul"},
            {"text": "Theatricality and deception are powerful agents to the uninitiated.", "speaker": "Ra's al Ghul"},
            {"text": "I never said thank you.", "speaker": "Batman"},
        ],
    },
    "the prestige": {
        "trivia": [
            "Both Hugh Jackman and Christian Bale performed real magic tricks for their roles.",
            "The film's three-act structure mirrors the three parts of a magic trick.",
            "David Bowie was cast as Nikola Tesla — Nolan's dream casting that actually happened.",
            "The two leads genuinely disliked each other on set, enhancing their rivalry.",
            "Tesla's lab was built on location in Colorado, not on a sound stage.",
        ],
        "quotes": [
            {"text": "Every great magic trick consists of three parts or acts.", "speaker": "Cutter"},
            {"text": "Are you watching closely?", "speaker": "Alfred Borden"},
            {"text": "You're familiar with the phrase 'man's reach exceeds his grasp'?", "speaker": "Nikola Tesla"},
            {"text": "The secret impresses no one. The trick you use it for is everything.", "speaker": "Nikola Tesla"},
            {"text": "I have not come here to tell you who I am. I have come to show you.", "speaker": "Angier"},
        ],
    },
    "dunkirk": {
        "trivia": [
            "Nolan shot the film with a skeleton crew and minimal dialogue by design.",
            "The film uses three different timelines: one week, one day, and one hour.",
            "Real Dunkirk veterans served as extras in the film.",
            "The Spitfire scenes were filmed with real, airworthy WWII aircraft.",
            "Hans Zimmer used a Shepard tone — an audio illusion of endless rising tension — throughout the score.",
        ],
        "quotes": [
            {"text": "We shall fight on the beaches.", "speaker": "Churchill (radio)"},
            {"text": "All we did was survive.", "speaker": "Tommy"},
            {"text": "Men my age dictate this war. Why should it be fought by children like you?", "speaker": "Mr. Dawson"},
            {"text": "I'm not going back.", "speaker": "Tommy"},
            {"text": "Home.", "speaker": "Tommy"},
        ],
    },
    "deadpool & wolverine": {
        "trivia": [
            "Ryan Reynolds and Hugh Jackman filmed for over 100 days.",
            "Jackman's Wolverine suit features the classic yellow-and-blue comic-book colours for the first time.",
            "The film marks Deadpool's official entry into the MCU.",
            "Reynolds wrote many of Deadpool's jokes himself and pitched them to the director.",
            "Multiple variants of beloved Marvel characters appear in the Void sequences.",
        ],
        "quotes": [
            {"text": "I'm going to do what I do best: talk a lot and make questionable decisions.", "speaker": "Deadpool"},
            {"text": "I'm the best there is at what I do.", "speaker": "Wolverine"},
            {"text": "You're not a hero — you're a nuisance.", "speaker": "Wolverine"},
            {"text": "Maximum effort.", "speaker": "Deadpool"},
            {"text": "Together we are something.", "speaker": "Deadpool"},
        ],
    },
    "spider-man no way home": {
        "trivia": [
            "The film features three generations of Spider-Man actors sharing the screen.",
            "Alfred Molina reprised his Doc Ock role 17 years after Spider-Man 2.",
            "The Times Square reunion scene was kept entirely secret during filming.",
            "Tom Holland, Andrew Garfield, and Tobey Maguire all did their own stunts.",
            "The film earned over $1.9 billion globally, the sixth-highest of all time.",
        ],
        "quotes": [
            {"text": "With great power comes great responsibility.", "speaker": "May Parker"},
            {"text": "I'm something of a scientist myself.", "speaker": "Doctor Octopus"},
            {"text": "You're amazing. All of you.", "speaker": "Peter Parker (MCU)"},
            {"text": "Magic. Actually.", "speaker": "Peter Parker (MCU)"},
            {"text": "If you expect disappointment, then you can never really be disappointed.", "speaker": "MJ"},
        ],
    },
    "beauty and the beast": {
        "trivia": [
            "The 1991 animated film was the first animated feature nominated for Best Picture at the Oscars.",
            "Alan Menken won two Academy Awards for Best Score and Best Original Song.",
            "The ballroom scene was one of the earliest uses of CGI in a Disney animated film.",
            "Beauty and the Beast was directly adapted from the 18th-century French fairy tale.",
            "The Beast's design was inspired by a lion, gorilla, bear, and wolf combined.",
        ],
        "quotes": [
            {"text": "Tale as old as time.", "speaker": "Mrs. Potts"},
            {"text": "There's something there that wasn't there before.", "speaker": "Belle"},
            {"text": "I want adventure in the great wide somewhere.", "speaker": "Belle"},
            {"text": "If she is the one who'll break the spell, you must try to make her love you.", "speaker": "Mrs. Potts"},
            {"text": "He's no monster, Gaston, you are!", "speaker": "Belle"},
        ],
    },
    "bones and all": {
        "trivia": [
            "Timothée Chalamet and Taylor Russell prepared extensively for their roles.",
            "Director Luca Guadagnino filmed on location across the American Midwest.",
            "The film is based on Camille DeAngelis's 2015 novel of the same name.",
            "The film explores themes of otherness, belonging, and forbidden desire.",
            "Mark Rylance's performance was widely described as one of the most unsettling of the year.",
        ],
        "quotes": [
            {"text": "You are what you eat.", "speaker": "Sully"},
            {"text": "I'm not like you.", "speaker": "Maren"},
            {"text": "I just want to know where I come from.", "speaker": "Maren"},
            {"text": "We eat, and then we leave.", "speaker": "Lee"},
            {"text": "You have to eat to stay alive.", "speaker": "Lee"},
        ],
    },
    "project hail mary": {
        "trivia": [
            "Andy Weir wrote the novel while working remotely during the COVID-19 pandemic.",
            "The book features one of the most beloved alien characters in modern sci-fi.",
            "Ryan Gosling is attached to star in the film adaptation.",
            "The novel's science is meticulously researched and largely plausible.",
            "Weir previously wrote The Martian, which was also adapted into a hit film.",
        ],
        "quotes": [
            {"text": "I'm not sure I want to know what I'm doing here.", "speaker": "Ryland Grace"},
            {"text": "Science is about knowing. Engineering is about doing.", "speaker": "Ryland Grace"},
            {"text": "Rocky — that's what I'm calling you.", "speaker": "Ryland Grace"},
            {"text": "Question: friend?", "speaker": "Rocky"},
            {"text": "It's not about survival. It's about saving everyone else.", "speaker": "Ryland Grace"},
        ],
    },
    "frankenstein": {
        "trivia": [
            "Mary Shelley wrote the novel when she was just 18 years old.",
            "The story originated from a ghost-story competition at Lake Geneva in 1816.",
            "The creature is often mistakenly called 'Frankenstein' — that is the creator's name.",
            "The novel is considered one of the first works of science fiction.",
            "Boris Karloff's 1931 portrayal of the creature remains iconic.",
        ],
        "quotes": [
            {"text": "I am malicious because I am miserable.", "speaker": "The Creature"},
            {"text": "Beware, for I am fearless and therefore powerful.", "speaker": "The Creature"},
            {"text": "Nothing is so painful to the human mind as a great and sudden change.", "speaker": "Victor Frankenstein"},
            {"text": "I, the miserable and the abandoned, am an abortion, to be spurned at, and kicked, and trampled on.", "speaker": "The Creature"},
            {"text": "Life, although it may only be an accumulation of anguish, is dear to me.", "speaker": "Victor Frankenstein"},
        ],
    },
    "hamnet": {
        "trivia": [
            "Maggie O'Farrell's novel won the Women's Prize for Fiction in 2020.",
            "Hamnet was the name of William Shakespeare's son who died aged 11.",
            "The novel imagines the domestic life behind the writing of Hamlet.",
            "Shakespeare is never named in the novel — only called 'the husband' or 'the Latin tutor'.",
            "The film adaptation stars Paul Mescal as Shakespeare.",
        ],
        "quotes": [
            {"text": "He is here. He is not here. He will always be here.", "speaker": "Agnes"},
            {"text": "Grief is the price we pay for love.", "speaker": "Agnes"},
            {"text": "A child is a piece of your soul walking around outside your body.", "speaker": "Agnes"},
            {"text": "How can the world go on when he is not in it?", "speaker": "Agnes"},
            {"text": "He put their son into the play so that Hamnet would live forever.", "speaker": "Narrator"},
        ],
    },
    "superman": {
        "trivia": [
            "The 1978 film's tagline was 'You will believe a man can fly.'",
            "Marlon Brando was paid $3.7 million for 13 days of work as Jor-El.",
            "Christopher Reeve trained intensively and gained 30 lbs of muscle for the role.",
            "The flying scenes were achieved using optical printing techniques revolutionary for their time.",
            "The film launched the modern superhero movie era.",
        ],
        "quotes": [
            {"text": "You will believe a man can fly.", "speaker": "Tagline"},
            {"text": "I'm here to fight for truth, justice, and the American way.", "speaker": "Superman"},
            {"text": "You've got me? Who's got you?!", "speaker": "Lois Lane"},
            {"text": "A person can choose either the right way or the wrong way.", "speaker": "Jor-El"},
            {"text": "Son, you are here for a reason.", "speaker": "Jor-El"},
        ],
    },
}


def _get_extras(title: str) -> dict:
    """Return curated trivia and quotes for a movie title."""
    key = title.lower().strip()
    for k, v in MOVIE_EXTRAS.items():
        if k in key or key in k:
            return v
    return {"trivia": [], "quotes": []}


# ── TMDb helpers ──────────────────────────────────────────────────────────────

async def _tmdb_search(title: str, api_key: str) -> dict | None:
    """Search TMDb for a movie by title and return the best match."""
    url = f"{TMDB_BASE}/search/movie"
    params = {"api_key": api_key, "query": title, "language": "en-US", "page": 1}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            results = r.json().get("results", [])
            if not results:
                return None
            title_lower = title.lower()
            for item in results:
                if item.get("title", "").lower() == title_lower:
                    return item
            return results[0]
    except Exception as e:
        logger.warning(f"[TMDb] search failed for '{title}': {e}")
        return None


async def _tmdb_details(tmdb_id: int, api_key: str) -> dict:
    """Fetch full movie details from TMDb (genres, runtime, imdb_id)."""
    url = f"{TMDB_BASE}/movie/{tmdb_id}"
    params = {"api_key": api_key, "language": "en-US"}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning(f"[TMDb] details failed id={tmdb_id}: {e}")
        return {}


async def _tmdb_credits(tmdb_id: int, api_key: str) -> dict:
    """Fetch cast and crew from TMDb."""
    url = f"{TMDB_BASE}/movie/{tmdb_id}/credits"
    params = {"api_key": api_key}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning(f"[TMDb] credits failed id={tmdb_id}: {e}")
        return {}


async def _tmdb_popular(api_key: str, page: int = 1) -> list:
    """Fetch popular movies list from TMDb."""
    url = f"{TMDB_BASE}/movie/popular"
    params = {"api_key": api_key, "language": "en-US", "page": page}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json().get("results", [])
    except Exception as e:
        logger.warning(f"[TMDb] popular failed: {e}")
        return []


async def _omdb_fetch(title: str, year: str | None, imdb_id: str | None, api_key: str) -> dict:
    """Fetch data from OMDb — prefers IMDb ID lookup."""
    params: dict = {"apikey": api_key}
    if imdb_id and imdb_id != "N/A":
        params["i"] = imdb_id
    else:
        params["t"] = title
        if year:
            params["y"] = year
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(OMDB_BASE, params=params)
            r.raise_for_status()
            data = r.json()
            return data if data.get("Response") == "True" else {}
    except Exception as e:
        logger.warning(f"[OMDb] fetch failed for '{title}': {e}")
        return {}


# ── Core function: build full movie data ─────────────────────────────────────

async def _build_movie_data(title: str) -> dict:
    """Fetch and merge TMDb + OMDb data for a movie title."""
    settings = get_settings()
    tmdb_key = settings.TMDB_API_KEY or "239967a7888fc811609db5aa3b554431"
    omdb_key = settings.OMDB_API_KEY or "72bf0fb9"

    # Step 1 – TMDb search
    result = await _tmdb_search(title, tmdb_key)
    
    # If TMDb fails, fallback completely to OMDb
    if not result:
        omdb = await _omdb_fetch(title, None, None, omdb_key)
        extras = _get_extras(title)
        if not omdb or omdb.get("Response") == "False":
            return {
                "title": title, "year": None, "genre": [], "director": None,
                "cast": [], "plot": None, "rating": None, "runtime": None,
                "awards": None, "poster": None, "backdrop": None,
                "overview": None, "trivia": extras.get("trivia", []), "quotes": extras.get("quotes", []),
                "imdb_id": None, "tmdb_id": None, "tagline": None,
            }
            
        try:
            rating_float = float(omdb.get("imdbRating", 0)) if omdb.get("imdbRating") and omdb.get("imdbRating") != "N/A" else None
        except ValueError:
            rating_float = None

        year = omdb.get("Year", "")[:4] if omdb.get("Year") else None
        
        return {
            "title":    omdb.get("Title", title),
            "year":     int(year) if year else None,
            "genre":    omdb.get("Genre", "").split(", ") if omdb.get("Genre") else [],
            "director": omdb.get("Director"),
            "cast":     omdb.get("Actors", "").split(", ") if omdb.get("Actors") else [],
            "plot":     omdb.get("Plot"),
            "rating":   rating_float,
            "runtime":  omdb.get("Runtime"),
            "awards":   omdb.get("Awards") if omdb.get("Awards") != "N/A" else None,
            "poster":   omdb.get("Poster") if omdb.get("Poster") != "N/A" else None,
            "backdrop": None,
            "overview": omdb.get("Plot"),
            "tagline":  None,
            "imdb_id":  omdb.get("imdbID"),
            "tmdb_id":  None,
            "trivia":   extras.get("trivia", []),
            "quotes":   extras.get("quotes", []),
        }

    tmdb_id = result.get("id")

    # Step 2 – TMDb details + credits (parallel)
    details, credits = await asyncio.gather(
        _tmdb_details(tmdb_id, tmdb_key),
        _tmdb_credits(tmdb_id, tmdb_key),
    )

    # Step 3 – Extract TMDb fields
    poster_path   = result.get("poster_path") or details.get("poster_path")
    backdrop_path = result.get("backdrop_path") or details.get("backdrop_path")
    poster   = f"{TMDB_IMG}{poster_path}"     if poster_path   else None
    backdrop = f"{TMDB_IMG_HD}{backdrop_path}" if backdrop_path else None

    release_date = result.get("release_date", "")
    year  = release_date[:4] if release_date else None
    imdb_id = details.get("imdb_id")
    tagline = details.get("tagline") or ""

    genres_list = [g["name"] for g in details.get("genres", [])]

    runtime_min = details.get("runtime")
    runtime_str = f"{runtime_min} min" if runtime_min else None

    cast_list = [c["name"] for c in credits.get("cast", [])[:8]]
    directors = [c["name"] for c in credits.get("crew", []) if c.get("job") == "Director"]
    director  = ", ".join(directors) if directors else None

    overview = result.get("overview") or details.get("overview") or ""

    # Step 4 – OMDb enrich
    omdb = await _omdb_fetch(title, year, imdb_id, omdb_key)
    imdb_rating = omdb.get("imdbRating") or str(result.get("vote_average", ""))
    awards      = omdb.get("Awards") or ""
    if not runtime_str:
        runtime_str = omdb.get("Runtime")
        
    if not poster and omdb.get("Poster") and omdb.get("Poster") != "N/A":
        poster = omdb.get("Poster")

    try:
        rating_float = float(imdb_rating) if imdb_rating and imdb_rating != "N/A" else None
    except ValueError:
        rating_float = None

    # Step 5 – Curated extras
    extras = _get_extras(title)

    return {
        "title":    result.get("title", title),
        "year":     int(year) if year else None,
        "genre":    genres_list or (omdb.get("Genre", "").split(", ") if omdb.get("Genre") else []),
        "director": director or omdb.get("Director"),
        "cast":     cast_list or (omdb.get("Actors", "").split(", ") if omdb.get("Actors") else []),
        "plot":     overview or omdb.get("Plot"),
        "rating":   rating_float,
        "runtime":  runtime_str or omdb.get("Runtime"),
        "awards":   awards if awards != "N/A" else None,
        "poster":   poster,
        "backdrop": backdrop,
        "overview": overview,
        "tagline":  tagline,
        "imdb_id":  imdb_id,
        "tmdb_id":  tmdb_id,
        "trivia":   extras.get("trivia", []),
        "quotes":   extras.get("quotes", []),
    }


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get('/details', tags=['Movie'])
async def get_movie_details(title: str = Query(..., min_length=1)):
    """
    Full movie metadata: poster, backdrop, rating, cast, director,
    genre, runtime, awards, trivia, quotes — sourced from TMDb + OMDb.
    """
    logger.info(f"[/movie/details] title='{title}'")
    data = await _build_movie_data(title)
    return data


@router.get('/popular', tags=['Movie'])
async def get_popular_movies(page: int = 1):
    """
    Returns popular movies from TMDb with poster URLs, ratings, genres.
    Used by the Home page movie grid.
    """
    settings = get_settings()
    tmdb_key = settings.TMDB_API_KEY or "239967a7888fc811609db5aa3b554431"

    results = await _tmdb_popular(tmdb_key, page)

    movies = []
    for m in results[:16]:
        poster_path   = m.get("poster_path")
        backdrop_path = m.get("backdrop_path")
        genres_raw = m.get("genre_ids", [])
        release    = m.get("release_date", "")
        movies.append({
            "id":       m.get("id"),
            "title":    m.get("title"),
            "overview": m.get("overview"),
            "year":     release[:4] if release else None,
            "rating":   round(m.get("vote_average", 0), 1),
            "poster":   f"{TMDB_IMG}{poster_path}"     if poster_path   else None,
            "backdrop": f"{TMDB_IMG_HD}{backdrop_path}" if backdrop_path else None,
        })

    return {"movies": movies, "total": len(movies)}


@router.get('/search', tags=['Movie'])
async def search_movies(query: str = Query(..., min_length=1)):
    """Search TMDb for movies matching the query."""
    settings = get_settings()
    tmdb_key = settings.TMDB_API_KEY or "239967a7888fc811609db5aa3b554431"
    url = f"{TMDB_BASE}/search/movie"
    params = {"api_key": tmdb_key, "query": query, "language": "en-US", "page": 1}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            results = r.json().get("results", [])
            movies = []
            for m in results[:10]:
                release = m.get("release_date", "")
                year = release[:4] if release else None
                poster_path = m.get("poster_path")
                movies.append({
                    "id": m.get("id"),
                    "title": m.get("title"),
                    "year": year,
                    "poster": f"{TMDB_IMG}{poster_path}" if poster_path else None
                })
            return {"results": movies}
    except Exception as e:
        logger.error(f"[TMDb] Search failed: {e}")
        return {"results": []}

@router.get('', response_model=MovieResponse)
async def get_movie(title: str):
    """Basic movie lookup (legacy endpoint — prefer /movie/details)."""
    data = await _build_movie_data(title)
    return MovieResponse(
        title    = data["title"],
        year     = data["year"],
        genre    = data["genre"],
        director = data["director"],
        cast     = data["cast"],
        plot     = data["plot"],
        rating   = data["rating"],
        runtime  = data["runtime"],
        awards   = data["awards"],
        poster   = data["poster"],
    )


@router.get('/list', tags=['Movie'])
async def list_movies():
    """List movie titles available in the curated extras set."""
    titles = list(MOVIE_EXTRAS.keys())
    return {"movies": [t.title() for t in titles], "total": len(titles)}


from app.db.database import get_db
from sqlalchemy.orm import Session
from app.models.movie_script import MovieScript


@router.get('/our-movies', tags=['Movie'])
def get_our_movies(db: Session = Depends(get_db)):
    """
    Returns the movies from our PDF script library with real TMDB posters,
    ratings, and metadata. Used by the Home page featured grid.
    """
    scripts = db.query(MovieScript).filter(MovieScript.status.in_(["UPLOADED", "PROCESSING", "READY", "FAILED"])).all()
    
    movies = []
    for script in scripts:
        movies.append({
            "id":       script.tmdb_id or script.id,
            "title":    script.title,
            "overview": script.overview or "",
            "year":     script.release_date[:4] if script.release_date else None,
            "rating":   script.rating or 0.0,
            "poster":   script.poster_url,
            "backdrop": script.backdrop_url,
            "has_script": True,
            "trivia_count": 0,
            "quotes_count": 0,
            "status": script.status,
            "ingestion_error": script.ingestion_error,
        })

    return {"movies": movies, "total": len(movies)}

