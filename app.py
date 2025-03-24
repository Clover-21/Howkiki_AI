from flask import Flask,jsonify,request
from flask_cors import CORS
from api.routes import chatbot_bp  # routes.py의 블루프린트 임포트
from api.config import Config  # 필요한 경우 config 사용
import os

#OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app, methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])

# 모든 요청을 로그로 출력
@app.before_request
def log_request():
    print(f"📌 {request.method} 요청 도착: {request.path}")

# OPTIONS 요청 처리
@app.route('/api/chat', methods=['OPTIONS'])
def handle_options():
    print("✅ OPTIONS 요청을 받음")
    response = jsonify()
    response.headers['Access-Control-Allow-Origin'] = 'https://kikibot.netlify.app'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, DELETE, PUT'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response, 204

# 블루프린트 등록 (예: /api/chat으로 접근)
app.register_blueprint(chatbot_bp, url_prefix='/api')

# 서버 실행
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    
