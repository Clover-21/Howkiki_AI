
from flask import Blueprint, request, jsonify
from chatbot.bot import get_gpt_response, system_prompt, client

# 블루프린트 생성
chatbot_bp = Blueprint('chatbot', __name__)

# 챗봇 엔드포인트: 사용자가 질문을 입력하면 GPT 응답을 반환
@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()  # JSON 데이터 전체 가져오기

    if not data or "question" not in data:  # 데이터가 없거나, "question" 키가 없을 경우
        return jsonify({"error": "잘못된 요청 형식입니다. 'question' 키가 필요합니다."}), 400

    user_input = data["question"]  # "question" 값 가져오기

    if not isinstance(user_input, str):  # 문자열인지 확인
        return jsonify({"error": "잘못된 입력 형식입니다. 질문은 문자열이어야 합니다."}), 400

    # GPT 응답 생성
    response = get_gpt_response(client, system_prompt, user_input)
    
    # 응답 반환
    return jsonify({"response": response})

