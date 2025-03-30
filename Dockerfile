# 1. Python 3.11 slim 버전 사용
FROM python:3.11-slim

# 2. 시스템 패키지 설치 (libGL 포함)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리 생성
WORKDIR /app

# 4. 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 앱 코드 복사
COPY . .

# 6. FastAPI 실행 명령
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port

