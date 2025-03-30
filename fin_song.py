from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import random
from typing import List, Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pydantic import BaseModel
import random

router = APIRouter(
    title="AI Music Recommendation API",
    description="Emotion-based music recommendation with AI-powered Spotify search",
    version="1.1.0"
)

# Spotify Setup
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="1db00c9b882c4da2b03a7b3db112c2db",
    client_secret="d98d69b9299f4436a6d1d0ce49d9f22c",
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-modify-playback-state user-read-playback-state"
))

class TrackInfo(BaseModel):
    name: str
    artist: str
    uri: str
    image_url: Optional[str] = None
    preview_url: Optional[str] = None

class RecommendationResponse(BaseModel):
    emotion: str
    tracks: List[TrackInfo]
    search_query: str
    message: Optional[str] = None

# AI-enhanced emotion to music characteristics mapping
EMOTION_PROFILES = {
    "happy": {
        "keywords": ["upbeat", "joyful", "happy", "summer", "dance"],
        "danceability": 0.7,
        "energy": 0.8,
        "valence": 0.9,
        "tempo": (120, 140),
        "genres": ["pop", "dance", "disco", "funk"]
    },
    "sad": {
        "keywords": ["melancholic", "sad", "heartbreak", "rainy day"],
        "danceability": 0.3,
        "energy": 0.3,
        "valence": 0.2,
        "tempo": (60, 90),
        "genres": ["soul", "blues", "acoustic", "indie"]
    },
    "angry": {
        "keywords": ["intense", "angry", "rage", "powerful"],
        "danceability": 0.5,
        "energy": 0.9,
        "valence": 0.3,
        "tempo": (140, 180),
        "genres": ["rock", "metal", "punk", "hardcore"]
    },
    "calm": {
        "keywords": ["peaceful", "calm", "relaxing", "meditation"],
        "danceability": 0.3,
        "energy": 0.2,
        "valence": 0.5,
        "tempo": (60, 80),
        "genres": ["ambient", "classical", "jazz", "chill"]
    },
    "surprise": {
        "keywords": ["unexpected", "surprising", "eclectic", "unique"],
        "danceability": 0.6,
        "energy": 0.7,
        "valence": 0.7,
        "tempo": (100, 130),
        "genres": ["experimental", "indie", "alternative", "world"]
    },
    "fear": {
        "keywords": ["dark", "ominous", "suspenseful", "haunting"],
        "danceability": 0.3,
        "energy": 0.5,
        "valence": 0.2,
        "tempo": (70, 100),
        "genres": ["dark ambient", "soundtrack", "gothic", "industrial"]
    },
    "neutral": {
        "keywords": ["balanced", "neutral", "background", "easy listening"],
        "danceability": 0.5,
        "energy": 0.5,
        "valence": 0.5,
        "tempo": (90, 110),
        "genres": ["pop", "indie", "electronic", "lounge"]
    }
}

def generate_search_query(emotion: str) -> str:
    """Generate an AI-powered search query based on emotion"""
    profile = EMOTION_PROFILES.get(emotion.lower(), EMOTION_PROFILES["neutral"])
    keywords = profile["keywords"]
    genres = profile["genres"]
    
    # Combine keywords and genres for richer search
    query_parts = [
        random.choice(keywords),
        f"genre:{random.choice(genres)}"
    ]
    
    # 30% chance to add year range for variety
    if random.random() < 0.3:
        decade = random.choice(["2000", "2010", "2020"])
        query_parts.append(f"year:{decade}")
    
    return " ".join(query_parts)

def recommend_tracks(emotion: str, limit: int = 5) -> List[TrackInfo]:
    """Recommend tracks based on emotion using AI-powered Spotify search"""
    profile = EMOTION_PROFILES.get(emotion.lower(), EMOTION_PROFILES["neutral"])
    
    # Generate search query
    search_query = generate_search_query(emotion)
    
    # Search for tracks with emotion-based audio features
    try:
        results = sp.search(
            q=search_query,
            limit=limit,
            type="track",
            market="KR"  # South Korea market (adjust as needed)
        )
        
        tracks = []
        for track in results["tracks"]["items"]:
            # Get more detailed audio features for each track
            audio_features = sp.audio_features([track["uri"]])[0]
            
            # Filter tracks based on emotion profile
            if (audio_features and
                profile["danceability"] - 0.2 <= audio_features["danceability"] <= profile["danceability"] + 0.2 and
                profile["energy"] - 0.2 <= audio_features["energy"] <= profile["energy"] + 0.2 and
                profile["valence"] - 0.2 <= audio_features["valence"] <= profile["valence"] + 0.2):
                
                tracks.append(TrackInfo(
                    name=track["name"],
                    artist=track["artists"][0]["name"],
                    uri=track["uri"],
                    image_url=track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                    preview_url=track["preview_url"]
                ))
        
        # If we didn't get enough matches, relax the filters
        if len(tracks) < limit:
            backup_results = sp.search(
                q=random.choice(profile["keywords"]),
                limit=limit,
                type="track",
                market="KR"
            )
            for track in backup_results["tracks"]["items"]:
                if len(tracks) >= limit:
                    break
                if not any(t.uri == track["uri"] for t in tracks):
                    tracks.append(TrackInfo(
                        name=track["name"],
                        artist=track["artists"][0]["name"],
                        uri=track["uri"],
                        image_url=track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                        preview_url=track["preview_url"]
                    ))
        
        return tracks[:limit]
    
    except Exception as e:
        print(f"Error searching Spotify: {e}")
        return []


@router.get("/recommend-music", response_model=RecommendationResponse)
async def recommend_music(
    emotion: str = Query(..., description="Emotion for music recommendation", example="happy"),
    limit: int = Query(5, description="Number of tracks to recommend", ge=1, le=10)
):
    """
    Get music recommendations based on emotion with AI-powered Spotify search
    """
    try:
        tracks = recommend_tracks(emotion, limit)
        if not tracks:
            raise HTTPException(status_code=404, detail="No suitable tracks found for this emotion")
        
        return {
            "emotion": emotion,
            "tracks": tracks,
            "search_query": generate_search_query(emotion),
            "message": f"AI-powered music recommendations for {emotion} mood"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/play-emotion-playlist")
async def play_emotion_playlist(
    emotion: str = Query(..., description="Emotion for playlist", example="happy"),
    shuffle: bool = Query(True, description="Shuffle the playlist")
):
    """
    Start playback of an emotion-based playlist on Spotify
    """
    try:
        tracks = recommend_tracks(emotion, 20)

        if not tracks:
            raise HTTPException(status_code=404, detail="No suitable tracks found for this emotion")

        devices = sp.devices()
        active_device = next((d["id"] for d in devices["devices"] if d["is_active"]), None)

        if not active_device:
            raise HTTPException(status_code=400, detail="No active Spotify device found")

        sp.start_playback(
            device_id=active_device,
            uris=[t.uri for t in tracks],
            context_uri=None,
            offset={"position": 0},
            position_ms=0
        )

        if shuffle:
            sp.shuffle(True, device_id=active_device)

        return {
            "status": "success",
            "emotion": emotion,
            "track_count": len(tracks),
            "first_track": tracks[0].name,
            "device": next(d["name"] for d in devices["devices"] if d["is_active"])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))