from fastapi import APIRouter
from deepface import DeepFace
import cv2

router = APIRouter()

# 감정 분석 (카메라)
@router.get("/analyze-emotion")
def analyze_emotion():
    cap = cv2.VideoCapture(0)
    emotions = []
    
    for _ in range(1):  # 5초간 분석
        ret, frame = cap.read()
        if ret:
            result = DeepFace.analyze(frame, actions=['emotion'], silent=True)
            emotions.append(result[0]['dominant_emotion'])
    
    cap.release()
    dominant_emotion = max(set(emotions), key=emotions.count)
    return {"emotion": dominant_emotion}  # "happy", "sad", "angry" 등
