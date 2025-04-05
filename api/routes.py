from flask import Blueprint, request, jsonify
from chatbot.bot import chat_with_gpt, client

# 블루프린트 생성
chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    """ 사용자의 질문을 받아 GPT 응답 반환 """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "요청 본문이 비어 있습니다."}), 400

        user_input = data.get("question")
        user_token = data.get("token")
        store_id = data.get("storeId")
        table_num = data.get("tableNum")

        if not isinstance(user_input, str):
            return jsonify({"error": "질문은 문자열이어야 합니다."}), 400

        # GPT 응답 생성 (function calling 포함)
        response_data = chat_with_gpt(client, user_input, user_token, store_id, table_num)

        # 사용자 정보 포함
        if user_token:
            response_data["token"] = user_token
        if store_id:
            response_data["storeId"] = store_id
        if table_num:
            response_data["tableNum"] = table_num

        return jsonify(response_data)

    except Exception as e:
        print(f"[❌ 서버 에러] /chat 처리 중 오류: {e}")
        return jsonify({"error": "서버에서 요청을 처리하는 중 오류가 발생했습니다."}), 500
