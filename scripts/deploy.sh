#!/bin/bash

echo "Starting deployment process..."

#  기존 서비스 중지
echo "Stopping the current Flask application..."
./scripts/stop.sh

#  최신 코드 가져오기
echo "Pulling the latest code from Git..."
git pull origin main  # main 브랜치에서 최신 코드 가져오기

#  가상환경 활성화 및 패키지 설치 (필요할 경우)
echo "Installing dependencies..."
source venv/bin/activate  # 가상환경 활성화
#pip install -r requirements.txt  # 필요한 패키지 설치

#  Flask 애플리케이션 재시작
echo "Restarting the Flask application..."
./scripts/start.sh

echo "Deployment completed!"
