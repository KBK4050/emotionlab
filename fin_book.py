from fastapi import APIRouter, Query
from pydantic import BaseModel
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import random
from typing import Optional

router = APIRouter()

# Google Sheets 설정
# SHEET_NAME = "emotion_book"
# CREDENTIALS_FILE = "emotionlab-b1cf55707206.json"
#google Sheets → CSV 파일로 변경
router = APIRouter()

CSV_FILE = "books.csv"

class BookRequest(BaseModel):
    emotion: str

def get_books_data():
    """CSV 파일에서 도서 데이터 로드"""
    try:
        return pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        print("⚠️ books.csv 파일을 찾을 수 없습니다.")
        # 실패 시 기본 데이터 반환
        return pd.DataFrame({
            "감정": ["happy", "sad", "neutral", "angry"],
            "책 제목": ["행복한 책", "슬픈 책", "중립적인 책", "분노의 책"],
            "작가": ["행복 작가", "슬픔 작가", "중립 작가", "분노 작가"]
        })
        
books_df_global = None  # 전역 변수로 선언
 
@router.on_event("startup")
async def startup_event():
    global books_df_global
    books_df_global = get_books_data()

async def recommend_book(
    emotion: str = Query(..., description="감정 종류 (happy, sad, neutral, angry)", example="happy")
):
    """GET 방식으로 도서 추천"""
    try:
        df = router.state.books_df
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
