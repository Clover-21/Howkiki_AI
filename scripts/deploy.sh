#!/bin/bash

echo "Starting deployment process..."

#  기존 서비스 중지
echo "Stopping the current Flask application..."
./scripts/stop.sh

#  최신 코드 가져오기
echo "Pulling the latest code from Git..."

#  가상환경 활성화 및 패키지 설치 (필요할 경우)
echo "Installing dependencies..."

#배포된 디렉터리로 이동
cd /home/ubuntu/Howkiki_AI

# 가상환경이 없으면 생성
if [ ! -d "venv" ]; then
  echo "Virtual environment not found! Creating venv..."
  python3 -m venv venv
fi

# 가상환경 활성화 및 패키지 설치
echo "Activating virtual environment..."
source venv/bin/activate  # 가상환경 활성화
pip install -r requirements.txt  # 필요한 패키지 설치


# 서비스 파일 복사
echo "Copying the howkiki.service file..."
cp /home/ubuntu/Howkiki_AI/howkiki.service /etc/systemd/system/

# systemd 리로드
echo "Reloading systemd daemon..."
systemctl daemon-reload

# 서비스 시작
echo "Starting the howkiki service..."
systemctl start howkiki.service

# 서비스가 부팅 시 자동으로 시작되도록 설정
systemctl enable howkiki.service

#  Flask 애플리케이션 재시작
echo "Restarting the Flask application..."
./scripts/start.sh

echo "Deployment completed!"
