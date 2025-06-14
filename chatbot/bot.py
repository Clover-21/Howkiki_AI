import os
import openai
import sys
import requests, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from chatbot.retriever import MongoDBRetriever
from api.redis_client import get_conversation, save_conversation
from api.config import config

# API 키 설정 (공식 라이브러리 사용 방식)
openai.api_key = config.OPENAI_API_KEY

#backend API 설정
api_url = config.api_url


#전체 시스템 프롬프트 정의
system_prompt='''
당신은 음식점의 고객 서비스 챗봇 역할을 수행하는 AI 어시스턴트입니다. 다음의 역할과 정보를 기반으로 고객 요청에 응답하세요.:

1. **주문 지원**:
   - 손님이 주문하고자 하는 메뉴와 수량을 파악하여 최종 주문 내역을 출력합니다.
   - 메뉴는 *메뉴 정보*를 바탕으로 주문을 받아야 하며, 메뉴 정보에 있지 않은 메뉴는 주문 및 추천을 받을 수 없다. 
   - 고객이 주문한 메뉴와 수량을 관리하세요.
   - 대화 중 주문 내역을 업데이트하고, 주문을 취소하거나 수량을 변경하려는 요청도 처리하세요.
   - 메뉴명은 정확하게 작성하고, 메뉴명에 "()" 괄호를 포함하지 마세요.

   1). **주문 수정**:
   - 고객이 "라구짜장 1개는 빼줘"와 같은 요청을 하면 해당 항목의 수량을 줄이고, 수량이 0이 되면 삭제하세요.
   - 고객이 "양장피 하나 추가해줘"라고 말하면 해당 메뉴의 수량을 늘리세요.
   - 변경된 주문 내역을 항상 최신 상태로 유지하세요.
   - 수정된 주문을 답하고, "주문을 확정해도 될까요?"라는 질문을 마지막에 같이 하세요.
   - 주문 확정 후 식사 방법을 항상 물어보고 최종 주문을 확정하세요.

   2). **주문 출력**:
    - 사용자가 주문을 입력하면 "현재 주문 내역은 다음과 같습니다."라는 멘트를 작성하세요.
    - 메뉴명은 정확하게 작성하고, 메뉴명에 "()" 괄호와 함께 작성하지 마세요.
    - 이전 주문 내역이 없으면, 다시 입력해달라고 요청하세요.
  
   예시:
     사용자: "라구짜장 5개 주문"
     GPT: {현재 주문 내역은 다음과 같습니다:
     - 라구짜장: 5개
     주문을 확정해도 될까요?}

     사용자: "블랙 허가우 하나랑 통새우 쇼마이 하나, 라구짜장 도삭면 하나, 공심채 볶음 하나 시켜줘"
     GPT: {현재 주문 내역은 다음과 같습니다:
     - 블랙 하가우: 1개
     - 통새우 쇼마이: 1개
     - 라구짜장 도삭면: 1개
     - 공심채 볶음: 1개
     주문을 확정해도 될까요? 🤗}

   - 사용자가 "어, o, 주문할게" 등의 긍정의 답을 하면 
    "포장인가요, 매장 식사(매장)인가요?"라고 묻고,
     사용자의 답변에 따라 식사 방법('포장', '매장 식사')을 포함하여 최종 주문 내역 출력하세요.
   - 최종 주문 내역을 파악하고 식사 방법을 확인 후에만 "최종 주문은 다음과 같습니다."라는 멘트를 작성하세요.

     예시:
     사용자: 포장
     GPT:최종 주문 내역은 다음과 같습니다:
     - 블랙 하가우: 1개
     - 통새우 쇼마이: 1개
     - 라구짜장 도삭면: 1개
     - 공심채 볶음: 1개
     식사 방법: 포장
     주문하신 메뉴는 곧 준비될 예정입니다. 감사합니다! 추가로 필요한 사항이나 궁금한 점이 있으시면 언제든지 말씀해 주세요.
       

2. **매장 정보 제공**:
   - 영업시간, 위치, 메뉴 항목, Wi-Fi 정보 등 음식점에 대한 자주 묻는 질문에 대해 정확하고 간결한 답변을 제공합니다.
   - 진행 중인 프로모션 정보와 같은 특별 요청도 도와줍니다.
   - 이외의 매장 정보를 물어보면 제공되지 않는 정보로 의견을 남겨주면 사장님께 의견을 전달드린다고 말하세요.

3. **정중하고 친절한 대화**:
   - 항상 정중하고 친근한 톤을 유지합니다.
   - 평소에는 ~해요 체로 응답해요. 다만 사과와 감사의 표현에는 '~습니다'체를 사용합니다.
   - 상황에 맞게 다양한 얼굴 이모티콘들을 사용하여 딱딱하지 않은 말투로 대답합니다.
   - 기술 용어를 피하고 이해하기 쉬운 방식으로 응답합니다.
   - 질문이 불분명할 경우 추가 질문을 통해 상세 정보를 요청합니다.

4. **행동 요청 처리**:
    - 사용자의 요청 사항을 다음과 같이 처리합니다:
      - 블랙 하가우 테이크아웃 요청, 음악 소리 조절, 에어컨 온도 조정, 접시 치우기, 사장님 호출 등과 같은 요청사항이 들어오면 다음과 같이 응답하세요:
        - "해당 사항을 사장님께 전달해 드릴까요?"
        - 사용자가 '응', 'o' 등 긍정을 하면 '요청 사항 내용'을 존댓말 또는 명사형으로 작성한 후 "요청을 전달해드렸어요."라고 응답하세요.
        
        예를 들어,
        {사용자: 블랙 하가우 테이크아웃 할 수 있을까요?
        GPT: 남은 음식을 포장해 드릴까요?
        사용자: 응응
        GPT: 해당 사항을 사장님께 전달해 드릴까요?
        사용자: 응
        GPT: 
        -요청 사항 내용:블랙 하가우 테이크아웃
        요청을 전달해드렸어요. 블랙 하가우 테이크아웃을 할 수 있도록 하겠습니다. 😊 추가로 필요한 사항이나 궁금한 점이 있으시면 언제든지 말씀해 주세요!}
        
        *만약 남은 음식이 아니면 새로운 주문으로 받으세요.

        ,{사용자: 음악 소리 좀 줄여줘.
        GPT: 해당 사항을 사장님께 전달해 드릴까요?
        사용자: 네
        GPT: 
        -요청 사항 내용: 음악 소리 좀 줄여주세요.
        요청을 전달해드렸어요. 음악 소리를 줄여달라고 전달했습니다. 😊 추가로 필요한 사항이나 궁금한 점이 있으시면 언제든지 말씀해 주세요!},
        {사용자: 에어컨 온도 좀 낮춰주세요.
        GPT: 해당 사항을 사장님께 전달해 드릴까요?
        사용자: o
        GPT: 
        -요청 사항 내용: 에어컨 온도 낮춰주세요.
        요청을 전달해드렸어요. 에어컨 온도를 낮춰달라고 사장님께 전달해드리겠습니다. 😊 추가로 필요한 사항이나 궁금한 점이 있으시면 언제든지 말씀해 주세요!},
        {사용자: 사장님 불러주세요.
        GPT: 해당 사항을 사장님께 전달해 드릴까요?
        사용자: 네
        GPT: 
        -요청 사항 내용: 사장님 불러주세요.
        요청을 전달해드렸어요. 사장님을 호출을 도와드리겠습니다. 😊 추가로 필요한 사항이나 궁금한 점이 있으시면 언제든지 말씀해 주세요!}


5. **메뉴 사진 제공 처리**
   고객이 "메뉴 사진을 보여줘"라고 요청하면 메뉴 사진을 제공합니다.
   사용자가 메뉴 사진을 보여달라고 요청하면 메뉴 사진 정보에 있는지 확인 후 다음과 같이 응답하세요:

   {사용자: "맑은 우육탕면 사진 보여줘"
   GPT:
   "여기 맑은 우육탕면의 사진입니다! 😊},
   { 사용자: 마늘칩 꿔바육 사진 좀 보고싶어.
   gpt: "여기 마늘칩 꿔바육의 사진입니다! 😊
   },
   {사용자: 블랙 허가우 사진 있어?
   gpt: 네 있습니다. 여기 블랙 허가우 사진입니다!
   }
   아직 메뉴 사진 정보가 없는 메뉴는 사진이 없다고 정중히 말씀드리세요.
   예: 죄송합니다. 현재 콜라 사진이 제공되지 않아 빠른시내에 추가하도록 하겠습니다.
   예: 해당 메뉴는 저희 매장에 없는 메뉴라 제공되지 않습니다.(메뉴 사진 정보에 있는지 확인 후)

6. **건의 사항 처리**:
   - 사용자가 서비스 개선점(예: 음악 소리가 크다, 테이블이 좁다, 숟가락이 더럽다 등)을 말하더라도, **즉시 건의 사항으로 처리하지 마세요.**
    - 먼저 정중하게 "해당 사항으로 사장님께 남길까요?" 또는 "해당 내용을 사장님께 전달해도 괜찮을까요?" 등으로 **사용자의 동의를 먼저 구하세요.**
    - 사용자가 긍정적인 답변(예: 네, 응, 좋아요, 부탁해요 등)을 명확히 한 경우에만, 다음과 같은 포맷으로 응답하세요:
   
    **"건의 사항 내용:"이라는 말은 동의 이후에만 등장**하도록 해.
   예를 들어,
   {사용자: 테이블이 너무 좁아
    GPT: "해당 사항으로 사장님께 남길까요?
    사용자: o
    GPT: 
    -건의 사항 내용: 테이블이 너무 좁아요.
    건의 사항으로 남겼습니다.  소중한 의견 감사합니다. 😊  고객님들의 편안한 식사를 위해 테이블 배치를 조정하는 방안을 내부적으로 논의해 보겠습니다!},
    {사용자: 숟가락이 너무 더러웠어. 기분 나빴어.
    GPT: "해당 내용을 사장님께 전달해도 괜찮을까요?"
    사용자: 네
    GPT: 
    -건의 사항 내용: 숟가락이 너무 더러워요.
    불편을 드려 정말 죄송합니다. 건의 사항으로 남겼습니다. 소중한 의견 감사합니다. 😊 앞으로 청결을 더욱 신경 쓰겠습니다!}
    {사용자: 실내가 너무 추워요
    GPT: "해당 사항으로 사장님께 남길까요?
    사용자: 네
    GPT: 
    -건의 사항 내용: 실내가 너무 추워요.
    건의 사항으로 남겼습니다. 소중한 의견 감사합니다. 😊 앞으로 실내 온도 관리를 더욱 신경 쓰겠습니다!}

7. **접근성**:
   - 대화 흐름을 간단하고 직관적으로 유지하여 모든 연령대와 기술 수준의 고객이 쉽게 사용할 수 있도록 합니다.

8. **요구사항과 건의 사항 구별 처리**:
   - 요구사항(예: 에어컨 꺼주세요, 남은 음식 포장해주세요 등)은 "해당 사항을 사장님께 전달해 드릴까요?"라고 묻습니다.
   - 사용자가 긍정적인 답을 하면 "(사용자 요청 사항을 재언급하면서) 요청을 전달해드렸어요."라고 응답하세요.
   - 건의 사항(예: 음악 소리가 너무 크다, 서비스가 느리다 등)은 "해당 사항을 사장님께 남길까요?"라고 묻습니다.
   - 사용자가 긍정적인 답을 하면 "(사용자 건의 사항을 재언급하면서)건의 사항으로 남겼습니다."라고 응답하세요.

당신의 궁극적인 목표는 고객의 요구를 효율적으로 충족시키고 음식점의 고품질 서비스를 반영하여 매끄럽고 즐거운 경험을 제공하는 것입니다.'''

# client는 openai 모듈 자체를 사용.
client = openai

### 📌 **RAG 기반 GPT 응답 생성 함수**
def get_rag_response(client, question,user_token):
    """RAG 기반 GPT 응답 생성"""

    conversation_history = get_conversation(user_token)

    # 대화 이력이 없으면 초기화
    if not conversation_history:
        conversation_history = [
            {"role": "system", "content": system_prompt}
        ]

    # 최종 주문 내역이 있는지 확인
    final_order_phrase = "최종 주문 내역은 다음과 같습니다"
    is_final_order = any(final_order_phrase in msg["content"] for msg in conversation_history if msg["role"] == "assistant")

    if is_final_order:
        conversation_history = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": "최종 주문 내역 있음"}
    ]
        
    # mongoDBRetriever에 검색
    retriever = MongoDBRetriever()
    retrieved_info = retriever.search(question)

    # 검색된 정보가 있을 경우, 시스템 프롬프트에 추가
    if retrieved_info:
        # 리스트를 문자열로 변환
        context_str = "\n".join([f"- {info}" for info in retrieved_info])
        system_prompt_with_context = f"""
        당신은 음식점 고객 서비스 챗봇입니다. 다음의 검색된 정보를 참고하여 답변하세요:

        --- 검색된 정보 ---
        {context_str}
        -------------------

        고객의 질문에 대해 관련 정보만 제공하고, --검색된 정보-- 및 대화기록을 바탕으로 답하세요.
        
        - 메뉴 정보는 아래와 같은 형식으로 답변을 제공합니다.
        메뉴에 대한 질문이 들어오면, 해당 메뉴에 대한 정보를 제공하고 마지막에는 **"(메뉴명)"의 사진입니다!** 라고 말합니다.
        예시:
        사용자: "소롱포가 뭐야?"
        GPT:"소롱포는 진한 고기 육즙을 가득 품은 딤섬이에요. 가격은 7,500원이며 고수는 포함되어 있지 않아요. 아래는 소롱포의 사진입니다😊.,
        사용자: "파이황과가 뭐야?"
        GPT:"파이황과는 ~~(설명)~~. 아래는 파이황과 사진입니다.

        이렇게 메뉴에 대한 실제 설명을 제공하고, **사진 제공 멘트"(메뉴명)"의 사진입니다!**를 꼭 작성합니다.
        
        제공되지 않은 정보에 대해서는 '제공되지 않은 정보입니다. 다른 궁금사항이 있다면 언제든 알려주세요'라고 말한 후 대화를 이어나가세요.
        """
    else:
        system_prompt_with_context = system_prompt

    # 대화 기록 업데이트
    conversation_history.append({"role": "system", "content": system_prompt_with_context})
    conversation_history.append({"role": "user", "content": question})

    # GPT-4o 응답 생성
    completion = client.chat.completions.create(
        model="gpt-4o", messages=conversation_history
    )
    assistant_reply = completion.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": assistant_reply})

    # Redis에 저장
    save_conversation(user_token, conversation_history)

    return assistant_reply


### 📌 **RAG 기반으로 사용자와 대화하는 함수**
def chat_with_gpt(client,question,user_token, store_id, table_num):
    """RAG 기반 챗오더 실행"""
    response = get_rag_response(client, question, user_token)

    # Redis에서 대화 이력 불러오기(최종 주문 내역 확인)
    conversation_history = get_conversation(user_token)
    final_order_check = "최종 주문 내역 있음"
    has_final_order = any(final_order_check in msg["content"] for msg in conversation_history if msg["role"] == "system")

    function_call_result = None

    if ("해당 사항을 사장님께 전달" in response) or ("해당 사항으로 사장님께 남길" in response):
        if has_final_order:
            function_call_result = gpt_functioncall(client, response, user_token, store_id, table_num)
        else:
            response = "최종 주문 내역이 없으므로, 주문을 먼저 해주세요. 😊"

    else:
        # 기본적으로 함수 호출 시도 (선택적 로직)
        function_call_result = gpt_functioncall(client, response, user_token, store_id, table_num)

    # JSON 형태로 프론트엔드에 반환
    return {
        "response": response,
        "function_call_result": function_call_result
    }


### 📌 **GPT 기반 행동 요청 처리 함수**
def gpt_functioncall(client, response,user_token, store_id, table_num):
    """GPT 응답을 분석하여 적절한 행동(주문, 요청, 건의 등)을 실행합니다."""
     
    function_prompt = '''
    사용자의 최종 주문을 정리하여 처리하고, 요청 사항 내용도 감지하여 처리하고, 건의 사항 내용, 사진 요청도 감지하여 처리하세요. 
    
    ***다음과 같이 '요청 사항 내용'이 입력되면 반드시 함수('create_request_notification')를 호출하세요.***
    
    ***다음과 같이 '건의 사항 내용' 단어가 입력되면 함수('create_suggestion')를 호출하세요***
    
    **사진 요청이 입력되면 반드시 함수 ("get_menu_image")을 호출하세요.**
    
    '''
    try:
        # GPT 모델 호출
        gpt_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": function_prompt},
                {"role": "user", "content": response}
            ],
            functions=function_specifications,
            function_call="auto"
        )

        # 함수 호출 여부 확인
        if gpt_response.choices[0].message.function_call:
            function_name = gpt_response.choices[0].message.function_call.name
            arguments = gpt_response.choices[0].message.function_call.arguments

            # 함수 호출이 주문 생성일 경우
            if function_name == "create_order":
                
                args = json.loads(arguments)
                final_order_data = {
                    "isTakeOut": args["isTakeOut"],  # 사용자 입력 반영
                    "tableNumber": int(table_num), #from frontend
                    "storeId": store_id,
                    "finalOrderDetails": [
                        {"menuName": item["menuName"], "quantity": item["quantity"]}
                        for item in args["finalOrderDetails"]
                    ]
                }
                result = post_order(final_order_data,user_token, store_id)
                return result
            
            #요청 사항 생성 함수
            elif function_name == "create_request_notification":
                
                # JSON 파싱 확인
                try:
                    if isinstance(arguments, str):
                        args = json.loads(arguments)  # JSON 파싱
                    else:
                        args = arguments

                    # 요청 데이터 생성
                    request_data = {
                        "tableNumber":int(table_num),
                        "storeId": store_id,
                        "content": args["content"]
                    }

                    result = send_request_notification(request_data, user_token)  

                    return result  

                except Exception as e:
                    return {"status": "error", "message": str(e)}

            #건의의 사항 생성 함수  
            elif function_name =="create_suggestion":
                # JSON 파싱 확인
                try:
                    if isinstance(arguments, str):
                        args = json.loads(arguments)  # JSON 파싱
                    else:
                        print("🔹 [DEBUG] arguments는 이미 JSON이므로 그대로 사용")
                        args = arguments
                    
                    #  방어 로직 추가: GPT 응답에 '건의 사항 내용:'이 포함되어 있는지 확인
                    if "건의 사항 내용:" not in response:
                        return {
                            "status": "skipped",
                            "message": "GPT 응답에 '건의 사항 내용:'이 없으므로 건의 사항 전송을 건너뜁니다."
                        }
                    # 요청 데이터 생성
                    suggestion_data = {
                        "storeId": store_id,
                        "content": args["content"]
                    }
                    result = send_suggestion(suggestion_data, store_id) 
                    return result  # 성공적으로 실행되었는지 확인

                except Exception as e:
                    return {"status": "error", "message": str(e)}

            elif function_name == "get_menu_image":
                try:
                    args = json.loads(arguments) if isinstance(arguments, str) else arguments
                    
                    """
                    image_data = {
                    "storeId": store_id,
                    "menuName": args["menuName"]
                    }"""


                    # 사진 요청 API 호출
                    result = show_menu_image(args["menuName"],store_id)

                    return result
                except Exception as e:
                    return {"status": "error", "message": str(e)}
            else:
                return f"❌ 알 수 없는 함수 호출: {function_name}"
        else:
            return "Assistant Response: 함수 호출이 되지 않습니다."

    except Exception as e:
        return f"❌ 함수 호출 처리 중 오류 발생: {e}"


# 함수: 주문 데이터를 서버로 전송
def post_order(final_order_data,user_token, store_id):
    """
    최종 주문 데이터를 POST 요청으로 서버에 전송합니다.
    요청 헤더에 sessionToken을 포함해야 함.
    """
    
    order_api_url= f"{api_url}/stores/{store_id}/orders"
    headers = {
        "sessionToken": user_token,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        
        response = requests.post(order_api_url, json=final_order_data,headers=headers)

        if response.status_code in [200, 201]:
            response_data = response.json()
            print("✅ 주문 성공!")
            return response_data
        else:
            print(f"❌ 주문 생성 실패: HTTP {response.status_code}") 
            return (response.json())
    except requests.exceptions.RequestException as e:
        return f"❌ 요청 실패: {e}"


# 함수: 요청 데이터를 서버로 전송

def send_request_notification(request_data, user_token):
    request_api_url = f"{api_url}/notification/new-request"
    headers = {
        "sessionToken": user_token,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(request_api_url, json=request_data, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            print("✅ 요청 사항 알림 전송 성공!")
            return response_data

        elif response.status_code == 400:
            print("❌ 요청 실패: 400 Bad Request (잘못된 요청)")
            return {"status": 400, "error": "Bad Request", "message": response.text}

        elif response.status_code == 404:
            print("❌ 요청 실패: 404 Not Found (API가 존재하지 않음)")
            return {"status": 404, "error": "Not Found", "message": response.text}

        else:
            print(f"❌ 요청 사항 알림 전송 실패: HTTP {response.status_code}")
            return {"status": response.status_code, "message": response.text}

    except requests.exceptions.Timeout:
        print("⏳ 요청 시간이 초과되었습니다.")
        return {"status": "error", "message": "Request timeout"}

    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 중 예외 발생: {e}")
        return {"status": "error", "message": str(e)}
    
#함수: 건의 데이터를 서버로 전송
def send_suggestion(suggestion_data, store_id):

    suggestion_api_url = f"{api_url}/stores/{store_id}/suggestions"
    try:
        response = requests.post(suggestion_api_url, json=suggestion_data)
        if response.status_code in [200, 201]:
            response_data = response.json()
            print("✅ 건의 사항 알림 전송 성공!")
            return response_data

        elif response.status_code == 400:
            print("❌ 요청 실패: 400 Bad Request (잘못된 요청)")
            return {"status": 400, "error": "Bad Request", "message": response.text}

        elif response.status_code == 404:
            print("❌ 요청 실패: 404 Not Found (API가 존재하지 않음)")
            return {"status": 404, "error": "Not Found", "message": response.text}

        else:
            print(f"❌ 건의 사항 알림 전송 실패: HTTP {response.status_code}")
            return {"status": response.status_code, "message": response.text}

    except requests.exceptions.Timeout:
        print("⏳ 요청 시간이 초과되었습니다.")
        return {"status": "error", "message": "Request timeout"}

    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 중 예외 발생: {e}")
        return {"status": "error", "message": str(e)}

# 함수: 메뉴 사진을 보여줌줌
def show_menu_image(menuName,store_id):
    """
    특정 가게(storeId)의 메뉴(menuName) 사진을 가져오는 함수.
    API 요청을 보내서 해당 메뉴의 사진 URL을 가져옴.
    """

    # 올바른 URL 형식 적용
    menu_image_api_url = f"{api_url}/stores/{store_id}/menu/img?menuName={menuName}"

    try:
        response = requests.get(menu_image_api_url)

        if response.status_code == 200:
            response_data = response.json()
            print("✅ 메뉴 사진 가져오기 성공!")
            return response_data  # 이미지 URL 포함
        elif response.status_code == 400:
            print("❌ 메뉴 사진 요청 실패: 400 Bad Request (잘못된 요청)")
            return {"status": 400, "error": "Bad Request", "message": response.text}
        elif response.status_code == 404:
            print("❌ 메뉴 사진 요청 실패: 404 Not Found (해당 메뉴 없음)")
            return {"status": 404, "error": "Not Found", "message": response.text}
        else:
            print(f"❌ 메뉴 사진 요청 실패: HTTP {response.status_code}")
            return {"status": response.status_code, "message": response.text}

    except requests.exceptions.Timeout:
        print("⏳ 요청 시간이 초과되었습니다.")
        return {"status": "error", "message": "Request timeout"}
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 중 예외 발생: {e}")
        return {"status": "error", "message": str(e)}



# 함수 호출을 지원하기 위한 함수 사양 정의
function_specifications = [
    {
        "name": "create_order",  # 함수 이름: create_order
        "description":"Processes the final confirmed order only when '최종 주문 내역은' is explicitly mentioned in the user input.",
        "parameters": {
            "type": "object",
            "properties": {
                "isTakeOut": { #테이크 타웃 관련 변수
                    "type": "boolean",
                    "description": "True if the order is for takeout, False if it is for dine-in."
                },
                "tableNumber": {
                    "type": "integer",
                    "description": "The table number where the order is placed."
                },
                "storeId": {
                    "type": "string",
                    "description": "The unique identifier of the store."
                },
                "finalOrderDetails": {  # 'finalOrderDetails' 최종 주문임
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "menuName": {
                                "type": "string",
                                "description": "Name of the menu item in 최종 주문 내역."
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "Quantity of the menu item in 최종 주문 내역."
                            }
                        },
                        "required": ["menuName", "quantity"]
                    },
                    "description": "List of menu items in the final confirmed order."
                }
            },
            "required": ["tableNumber", "storeId", "finalOrderDetails"]
        }
    },
    {
    "name": "create_request_notification", #함수: create_request_notification 요청 사항 호출
    "description": "Handles user requests such as temperature adjustments, music volume changes. If the assistant's response includes phrases like '요청 사항 내용', this function must be triggered.",
    "parameters": {
        "type": "object",
        "properties": {
            "tableNumber": {
                    "type": "integer",
                    "description": "The table number where the request was made."
                },
                "storeId": {
                    "type": "string",
                    "description": "The unique identifier of the store."
                },
            "content": {
                "type": "string",
                "description": "The request content describing the user's need."
            }
        },
        "required": ["tableNumber", "storeId", "content"]
        }   
    },
    {
    "name": "create_suggestion", #함수 이름:create_suggestion 건의 사항 전송
    "description": "Handles user suggestion. This function MUST be called ONLY IF the assistant's response includes the exact phrase '건의 사항 내용:'. Do NOT call this function based on user input alone.",
    "parameters": {
        "type": "object",
        "properties": {
            "storeId": {
                    "type": "string",
                    "description": "The unique identifier of the store."
                },
            "content": {
                "type": "string",
                "description": "The suggestion content describing the user's need."
            }
        },
        "required": ["storeId", "content"]
        }
    },
    {
    "name": "get_menu_image",
    "description": "Retrieves the menu image URL for a specific menu item in a store. If the assistant's response includes phrases like '사진 입니다', this function must be triggered.",
    "parameters": {
        "type": "object",
        "properties": {
            "storeId": {
                "type": "integer",
                "description": "The unique identifier of the store."
            },
            "menuName": {
                "type": "string",
                "description": "The name of the menu item for which the image URL is requested."
            }
        },
        "required": ["storeId", "menuName"]
    }
}

]



# 직접 실행 시 인터랙티브 모드 시작
if __name__ == '__main__':
    session_token="103948230972305" #임의로 세션토큰 지정
    store_id ="1"
    table_num= "2"

    print("안녕하세요.호우섬입니다.대화를 종료하려면 '종료'를 입력하세요.")
    while True:
        user_input = input("고객 > ")
        if user_input.lower() == '종료':
            break
        
        response = chat_with_gpt(client, user_input, session_token, store_id, table_num)
        print(f"챗오더 > {response['response']}")
        
        if response['function_call_result']:
            print(f"함수 호출 결과: {response['function_call_result']}")