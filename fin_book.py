from fastapi import FastAPI, Query
from pydantic import BaseModel
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import random
import uvicorn
from typing import Optional

app = FastAPI(title="감정 기반 도서 추천 API")

# Google Sheets 설정
SHEET_NAME = "emotion_book"
CREDENTIALS_FILE = "emotionlab-b1cf55707206.json"

class BookRequest(BaseModel):
    emotion: str

def get_books_data():
    """Google 스프레드시트에서 도서 데이터 로드"""
    try:
        scope = ["https://spreadsheets.google.com/feeds", 
                "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
        records = sheet.get_all_records()
        return pd.DataFrame(records)
    except Exception as e:
        print(f"Error loading sheet: {e}")
        # 실패 시 기본 데이터
        return pd.DataFrame({
            "감정": ["happy", "sad", "neutral", "angry"],
            "책 제목": ["행복한 책", "슬픈 책", "중립적인 책", "분노의 책"],
            "작가": ["행복 작가", "슬픔 작가", "중립 작가", "분노 작가"]
        })

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 데이터 로드"""
    app.state.books_df = get_books_data()
    print("도서 데이터 로드 완료. 샘플 데이터:")
    print(app.state.books_df.head())

@app.get("/recommend")
def recommend_book(
    emotion: str = Query(..., description="감정 종류 (happy, sad, neutral, angry)", example="happy")
):
    """GET 방식으로 도서 추천"""
    try:
        df = app.state.books_df
        filtered_books = df[df['감정'].str.lower() == emotion.lower()]
        
        if filtered_books.empty:
            return {
                "status": "error",
                "message": f"'{emotion}' 감정에 해당하는 도서가 없습니다.",
                "available_emotions": list(df['감정'].unique())
            }
        
        recommended = filtered_books.sample().iloc[0]
        return {
            "status": "success",
            "emotion": emotion,
            "book": {
                "title": recommended['책 제목'],
                "author": recommended['작가']
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/recommend")
def recommend_book_post(request: BookRequest):
    """POST 방식으로 도서 추천"""
    return recommend_book(request.emotion)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)