from fastapi import FastAPI
from fin_book import router as book_router
from fin_camera import router as camera_router
from fin_movie import router as movie_router
from fin_song import router as song_router

app = FastAPI(
    title="Emotion-based Media Recommendation API",
    description="Get movie, music, and book recommendations based on your emotion!",
    version="1.1.0"
)
 
@app.get("/")
def root():
    return {"message": "EmotionLab API is running!"}

app.include_router(book_router, prefix="/book")
app.include_router(camera_router, prefix="/camera")
app.include_router(movie_router, prefix="/movie")
app.include_router(song_router, prefix="/song")

# 아래처럼 추가해 주세요
#if __name__ == "__main__":
#    import uvicorn
#    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
