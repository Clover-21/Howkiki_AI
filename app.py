from flask import Flask, request
from flask_cors import CORS
from api.routes import chatbot_bp  # routes.py의 블루프린트 임포트
import logging
import os

# logs 디렉토리 없으면 생성
if not os.path.exists('logs'):
    os.makedirs('logs')

# 로그 설정
logging.basicConfig(
    filename='logs/flask.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(
    app,
    origins=["https://kikibot.netlify.app", "https://howkiki.netlify.app"],
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

# 모든 요청을 로그로 출력
@app.before_request
def log_request():
    logger.info(f"{request.method} 요청 도착: {request.path}")

# 블루프린트 등록 (예: /api/chat으로 접근)
app.register_blueprint(chatbot_bp, url_prefix='/api')

# 서버 실행
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
