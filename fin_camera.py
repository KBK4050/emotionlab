from fastapi import FastAPI, Query, HTTPException
from deepface import DeepFace
import uvicorn
import cv2
from typing import Optional
from pydantic import BaseModel
import os

app = FastAPI(title="감정 분석 api")

# 감정 분석 (카메라)
@app.get("/analyze-emotion")
def analyze_emotion():
    cap = cv2.VideoCapture(0)
    emotions = []
    
    for _ in range(5):  # 5초간 분석
        ret, frame = cap.read()
        if ret:
            result = DeepFace.analyze(frame, actions=['emotion'], silent=True)
            emotions.append(result[0]['dominant_emotion'])
    
    cap.release()
    dominant_emotion = max(set(emotions), key=emotions.count)
    return {"emotion": dominant_emotion}  # "happy", "sad", "angry" 등

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)