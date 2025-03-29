from fastapi import FastAPI, Query
from pydantic import BaseModel
import tensorflow as tf
import pandas as pd
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np
import uvicorn
from sklearn.model_selection import train_test_split
import re

app = FastAPI(title="영화 감정 분석 API")

# 데이터 로드 및 전처리
try:
    movies = pd.read_csv("movies.csv")
    df = movies[['title', 'plot', 'emotion']].dropna().sample(500, random_state=42)
except Exception as e:
    print(f"Error loading data: {e}")
    data = {
        "title": [
            "국제시장 (2014)", "7번방의 선물 (2013)", "극한직업 (2019)",
            "명량 (2014)", "베테랑 (2015)", "아바타 (2009)",
            "어벤져스 (2012)", "겨울왕국 (2013)", "인터스텔라 (2014)"
        ],
        "plot": [
            "가족과 희생을 그린 감동적인 이야기",
            "지적 장애 아버지와 어린 딸의 감동적인 이야기",
            "치킨집을 차린 형사들의 유쾌한 코미디",
            "이순신 장군의 해전을 그린 액션 드라마",
            "불의를 참지 않는 형사들의 액션 코미디",
            "판도라 행성을 배경으로 한 SF 영화",
            "슈퍼히어로들이 모여 지구를 구하는 이야기",
            "자매의 사랑을 그린 애니메이션 뮤지컬",
            "우주를 배경으로 한 과학적 모험 이야기"
        ],
        "emotion": ["sad", "sad", "happy", "angry", "happy", "happy", "happy", "happy", "sad"]
    }
    df = pd.DataFrame(data)

# 텍스트 전처리 함수
def preprocess_text(text):
    text = re.sub(r'[^가-힣a-zA-Z0-9 ]', '', text)
    return text

df['plot'] = df['plot'].apply(preprocess_text)

# 모델 설정
emotion_mapping = {emotion: idx for idx, emotion in enumerate(df['emotion'].unique())}
df['emotion_label'] = df['emotion'].map(emotion_mapping)

tokenizer = Tokenizer(num_words=5000)
tokenizer.fit_on_texts(df['plot'])

# 개선된 모델 구조
model = tf.keras.Sequential([
    tf.keras.layers.Embedding(5000, 128, input_length=100),
    tf.keras.layers.LSTM(128, return_sequences=True),
    tf.keras.layers.LSTM(64),
    tf.keras.layers.Dense(len(emotion_mapping), activation='softmax')
])
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# 모델 학습
sequences = tokenizer.texts_to_sequences(df['plot'])
padded = pad_sequences(sequences, maxlen=100)
X_train, X_test, y_train, y_test = train_test_split(padded, df['emotion_label'], test_size=0.2)
model.fit(X_train, y_train, epochs=20, validation_data=(X_test, y_test), batch_size=64, verbose=0)

# 감정 계층 구조 (추천을 위한)
emotion_hierarchy = {
    'sad': ['emotional', 'dramatic'],
    'happy': ['funny', 'exciting'],
    'angry': ['intense', 'action']
}

@app.get("/predict")
def predict_emotion(
    text: str = Query(..., description="분석할 텍스트 입력", example="가족을 잃은 슬픈 이야기")
):
    """GET 방식으로 영화 감정 분석 및 추천"""
    try:
        # 텍스트 전처리
        processed_text = preprocess_text(text)
        seq = tokenizer.texts_to_sequences([processed_text])
        padded = pad_sequences(seq, maxlen=100)
        
        # 예측
        prediction = model.predict(padded, verbose=0)[0]
        emotion_idx = np.argmax(prediction)
        emotion = list(emotion_mapping.keys())[emotion_idx]
        confidence = float(prediction[emotion_idx])
        
        # 추천 영화 선택
        main_emotion_movies = df[df['emotion'] == emotion]
        
        # 주 감정 영화가 3개 미만이면 유사 감정 영화 추가
        if len(main_emotion_movies) < 3:
            for related_emotion in emotion_hierarchy.get(emotion, []):
                if len(main_emotion_movies) < 3:
                    additional = df[df['emotion'] == related_emotion]
                    main_emotion_movies = pd.concat([main_emotion_movies, additional])
        
        # 최종 추천 (중복 제거)
        recommended = main_emotion_movies.drop_duplicates().sample(min(3, len(main_emotion_movies)))
        
        return {
            "input_text": text,
            "processed_text": processed_text,
            "emotion": emotion,
            "confidence": confidence,
            "movies": recommended[['title', 'plot', 'emotion']].to_dict('records')
        }
        
    except Exception as e:
        return {
            "error": "Prediction failed",
            "detail": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)