from flask import Blueprint, request, jsonify
from chatbot.bot import chat_with_gpt, client

# 블루프린트 생성
chatbot_bp = Blueprint('chatbot', __name__)

# 챗봇 엔드포인트: 사용자가 질문을 입력하면 GPT 응답을 반환
@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    #print("📌 [DEBUG] chat() 함수 호출됨!")  # 가장 먼저 실행 확인
    data = request.get_json()  # JSON 데이터 전체 가져오기

    if not data or "question" not in data:  # 데이터가 없거나, "question" 키가 없을 경우
        return jsonify({"error": "잘못된 요청 형식입니다. 'question' 키가 필요합니다."}), 400

    user_input = data["question"]  # "question" 값 가져오기
    user_token = data.get("token")  # 프론트엔드에서 받은 토큰
    store_id = data.get("storeId")  # 가게 ID 받아오기
    table_num = data.get("tableNum")  # 테이블 번호 받아오기
    #print(f"📌 [DEBUG] Received store_id: {store_id}, table_num: {table_num}")


    if not isinstance(user_input, str):  # 문자열인지 확인
        return jsonify({"error": "잘못된 입력 형식입니다. 질문은 문자열이어야 합니다."}), 400
    
    # GPT 응답 생성 (function calling 포함)
    response_data = chat_with_gpt(client, user_input, user_token, store_id, table_num)

     # 기존 정보 포함하여 응답 반환
    if user_token:
        response_data["token"] = user_token
    if store_id:
        response_data["storeId"] = store_id
    if table_num:
        response_data["tableNum"] = table_num

    return jsonify(response_data)