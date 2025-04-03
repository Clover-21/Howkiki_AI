import os
import openai
import sys
import requests, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from chatbot.retriever import FAISSRetriever  # RAG 적용 (FAISS 검색)
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

   1). **주문 수정**:
   - 고객이 "라구짜장 1개는 빼줘"와 같은 요청을 하면 해당 항목의 수량을 줄이고, 수량이 0이 되면 삭제하세요.
   - 고객이 "양장피 하나 추가해줘"라고 말하면 해당 메뉴의 수량을 늘리세요.
   - 변경된 주문 내역을 항상 최신 상태로 유지하세요.
   - 수정된 주문을 답하고, "주문을 확정해도 될까요?"라는 질문을 마지막에 같이 하세요.
   -주문 확정 후 식사 방법을 항상 물어보고 최종 주문을 확정하세요.

   2). **주문 출력**:
    - 사용자가 주문을 입력하면 "현재 주문 내역은 다음과 같습니다."라는 멘트를 작성하세요.
  
   예시:
     사용자: "라구짜장 5개 주문"
     GPT: {현재 주문 내역은 다음과 같습니다:
     - 라구짜장: 5개
     주문을 확정해도 될까요?}

     사용자: "블랙 허가우 하나랑 통새우 쇼마이 하나, 라구짜장 도삭면 하나, 마늘칩 꿔바육 하나, 공심채 볶음 하나 시켜줘"
     GPT: {현재 주문 내역은 다음과 같습니다:
     - 블랙 하가우: 1개
     - 통새우 쇼마이: 1개
     - 라구짜장 도삭면: 1개
     - 마늘칩 꿔바육: 1개
     - 공심채 볶음: 1개
     주문을 확정해도 될까요? 🤗}

   - 최종 주문 내역을 파악한 후 "최종 주문은 다음과 같습니다."라는 멘트를 작성하세요.
   - 사용자가 "어, o, 주문할게" 등의 긍정의 답을 하면 
    "포장인가요, 매장 식사인가요?"라고 묻고,
     사용자의 답변에 따라 식사 방법('포장', '매장 식사')을 포함하여 출력하세요.

     예시:
     GPT:{최종 주문 내역은 다음과 같습니다:
     - 라구짜장: 1개
     - 양장피: 1개
     식사 방법: 포장
     주문하신 메뉴는 곧 준비될 예정입니다. 감사합니다! 추가로 필요한 사항이나 궁금한 점이 있으시면 언제든지 말씀해 주세요.}
       

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

4. **컴플레인 처리**:
   - 음식, 청결 등에 대한 컴플레인이 들어오면 공감/사과 → 대응 계획 → 추가 도움 제공의 단계를 따릅니다.

5. **행동 요청 처리**:
    - 사용자의 요청 사항을 다음과 같이 처리합니다:
      - 블랙 하가우 테이크아웃 요청, 음악 소리 조절, 에어컨 온도 조정, 접시 치우기, 사장님 호출 등과 같은 요청사항이 들어오면 다음과 같이 응답하세요:
        - "해당 요청을 사장님께 전달해 드릴까요?"
        - 사용자가 '응', 'o' 등 긍정을 하면 "(사용자 요청 사항을 재업근하면서) 요청을 전달해드렸어요."라고 응답하세요.
        예를 들어,
        {사용자: 블랙 하가우 테이크아웃 할 수 있을까요?
        GPT: 해당 사항을 사장님께 전달해 드릴까요?
        사용자: 응
        GPT: 
        -요청 사항 내용:블랙 하가우 테이크아웃
        요청을 전달해드렸어요. 블랙 하가우 테이크아웃을 할 수 있도록 하겠습니다. 😊 추가로 필요한 사항이나 궁금한 점이 있으시면 언제든지 말씀해 주세요!}
        ,{사용자: 음악 소리 좀 줄여줘.
        GPT: 해당 사항을 사장님께 전달해 드릴까요?
        사용자: 네
        GPT: 
        -요청 사항 내용: 음악 소리 좀 줄여줘
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


7. **메뉴 사진 제공 처리**
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

8. **건의 사항 처리**:
   - 사용자가 서비스 개선점(예: 음악 소리가 크다, 테이블이 좁다 등)을 말하면 "건의 사항으로 남길까요?"라고 묻습니다.
   - 사용자가 긍정적인 답을 하면 "건의 사항으로 남겼습니다."라고 응답하세요.
   - 건의 사항은 기록으로 남기고 필요 시 사장님께 전달된다는 점을 안내하세요.
   예를 들어,
   {사용자: 테이블이 너무 좁아
    GPT: "해당 사항을 전달할까요?
    사용자: o
    GPT: 
    -건의 사항 내용: 테이블이 너무 좁아요.
    건의 사항으로 남겼습니다.  소중한 의견 감사합니다. 😊  고객님들의 편안한 식사를 위해 테이블 배치를 조정하는 방안을 내부적으로 논의해 보겠습니다!},
    {사용자: 실내가 너무 추워요
    GPT: "해당 사항을 전달할까요?
    사용자: 네
    GPT: 
    -건의 사항 내용: 실내가 너무 추워요.
    건의 사항으로 남겼습니다. 소중한 의견 감사합니다. 😊 앞으로 실내 온도 관리를 더욱 신경 쓰겠습니다!}

9. **접근성**:
   - 대화 흐름을 간단하고 직관적으로 유지하여 모든 연령대와 기술 수준의 고객이 쉽게 사용할 수 있도록 합니다.

10. **요구사항과 건의 사항 구별 처리**:
   - 요구사항(예: 에어컨 꺼주세요, 남은 음식 포장해주세요 등)은 "해당 요청을 사장님께 전달해 드릴까요?"라고 묻습니다.
   - 사용자가 긍정적인 답을 하면 "(사용자 요청 사항을 재언급하면서) 요청을 전달해드렸어요."라고 응답하세요.
   - 건의 사항(예: 음악 소리가 너무 크다, 서비스가 느리다 등)은 "건의 사항으로 남길까요?"라고 묻습니다.
   - 사용자가 긍정적인 답을 하면 "(사용자 건의 사항을 재언급하면서)건의 사항으로 남겼습니다."라고 응답하세요.

당신의 궁극적인 목표는 고객의 요구를 효율적으로 충족시키고 음식점의 고품질 서비스를 반영하여 매끄럽고 즐거운 경험을 제공하는 것입니다.'''

# client는 openai 모듈 자체를 사용.
client = openai

# FAISS 검색 인스턴스 생성 (RAG 적용)
retriever = FAISSRetriever()

# 전역 대화 이력 (주의: 동시 요청/다중 사용자 환경에서는 별도 관리 필요)
conversation_history = [{"role": "system", "content": system_prompt}]


### 📌 **RAG 기반 GPT 응답 생성 함수**
def get_rag_response(client, question):
    """RAG 기반 GPT 응답 생성"""
    retrieved_info = retriever.search(question)  # FAISS 검색된 내용 가져오기

    # 최종 주문 내역이 있는지 확인
    final_order_phrase = "최종 주문 내역은 다음과 같습니다"
    is_final_order = any(final_order_phrase in msg["content"] for msg in conversation_history if msg["role"] == "assistant")
    
    # 최종 주문이 감지되면 대화 기록 초기화
    if is_final_order:
        conversation_history.clear()
        conversation_history.append({"role": "system", "content": system_prompt})
        conversation_history.append({"role": "system", "content": "최종 주문 내역 있음"})

    # 검색된 정보가 있을 경우, 시스템 프롬프트에 추가
    if retrieved_info:
        system_prompt_with_context = f"""
        당신은 음식점 고객 서비스 챗봇입니다. 다음의 검색된 정보를 참고하여 답변하세요:

        --- 검색된 정보 ---
        {retrieved_info}
        -------------------

        고객의 질문에 대해 관련 정보만 제공하고, --검색된 정보-- 및 대화기록을 바탕으로 답하세요.
        제공되지 않은 정보에 대해서는 '제공되지 않은 정보입니다. '라고 말한 후 대화를 이어나가세요.
        """
    else:
        system_prompt_with_context = system_prompt

    # 대화 기록 업데이트
    conversation_history.append({"role": "system", "content": system_prompt_with_context})
    conversation_history.append({"role": "user", "content": question})

    # GPT-4o 응답 생성
    completion = client.chat.completions.create(
        model="gpt-4o-mini", messages=conversation_history
    )
    assistant_reply = completion.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": assistant_reply})

    return assistant_reply


### 📌 **RAG 기반으로 사용자와 대화하는 함수**
def chat_with_gpt(client,question,session_token, store_id, table_num):
    """RAG 기반 챗봇 실행"""
    #print(f"📌 [DEBUG] chat_with_gpt() 내부 store_id: {store_id}, table_num: {table_num}")  # 디버깅 추가
    #print("호우섬에 오신 것을 환영합니다! 😊")
    #print("주문 또는 궁금한 점을 입력하세요. 대화를 종료하려면 '종료' 또는 '그만'을 입력하세요.\n")
    # RAG 기반 응답 생성
    response = get_rag_response(client, question)

    # 최종 주문 내역 확인
    final_order_check = "최종 주문 내역 있음"
    has_final_order = any(final_order_check in msg["content"] for msg in conversation_history if msg["role"] == "system")

    function_call_result = None

    if "해당 요청을 사장님께 전달해 드릴까요?" in response:
        
        if has_final_order:
            function_call_result = gpt_functioncall(client, response, session_token,store_id, table_num)
        else:
            response = "\n최종 주문 내역이 없으므로, 주문을 먼저 해주세요. 😊"

    function_call_result = gpt_functioncall(client, response, session_token, store_id, table_num)
    # JSON 형태로 프론트엔드에 반환
    return {
        "response": response,
        "function_call_result": function_call_result
    }


### 📌 **GPT 기반 행동 요청 처리 함수**
def gpt_functioncall(client, response,session_token, store_id, table_num):
    """GPT 응답 기반으로 특정 행동 처리 """
     
    function_prompt = '''
    You are a helpful assistant for table 5. 
    사용자의 최종 주문을 정리하여 처리하고, 요청 사항 내용도 감지하여 처리하고, 건의 사항 내용, 사진 요청도 감지하여 처리하세요. 

    ***다음과 같이 '요청 사항 내용'이 입력되면 반드시 함수('send_request_notification')를 호출하세요.***
    **건의 사항이 입력되면 반드시 함수 ("send_suggestion")을 호출하세요.**
    **사진 요청이 입력되면 반드시 함수 ("get_menu_image")을 호출하세요.""
    
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
            #print("함수 호출 감지")
            #print(f"🛠 table_num: {table_num}, store_id: {store_id}")
            function_name = gpt_response.choices[0].message.function_call.name
            arguments = gpt_response.choices[0].message.function_call.arguments

            # 함수 호출이 주문 생성일 경우
            if function_name == "create_order":
                #print("create_order 호출함")
                
                args = json.loads(arguments)
                #print("json 파싱 성공")
                final_order_data = {
                    "isTakeOut": args["isTakeOut"],  # 사용자 입력 반영
                    "tableNumber": int(table_num), #from frontend
                    "storeId": store_id,
                    "finalOrderDetails": [
                        {"menuName": item["menuName"], "quantity": item["quantity"]}
                        for item in args["finalOrderDetails"]
                    ]
                }
                #주문 API 호출(세션 토근 포함함)
                print("🔹 최종 주문 데이터:", final_order_data)  # 추가 디버깅
                result = post_order(final_order_data,session_token, store_id)
                return result
            
            #요청 사항 생성 함수
            elif function_name == "create_request_notification":
                #print("✅ create_request_notification 호출됨")  # 🛠 확인 로그 추가
                #print(f" [DEBUG] function_call.arguments: {gpt_response.choices[0].message.function_call.arguments}")
                #print(f" [DEBUG] arguments 타입: {type(arguments)}")

                # JSON 파싱 확인
                try:
                    if isinstance(arguments, str):
                        #print("🔹 [DEBUG] arguments는 문자열이므로 JSON 변환 시도")
                        args = json.loads(arguments)  # JSON 파싱
                    else:
                        #print("🔹 [DEBUG] arguments는 이미 JSON이므로 그대로 사용")
                        args = arguments

                    #print("✅ [DEBUG] json.loads() 성공:", args)  # JSON 변환 성공 확인

                    # 요청 데이터 생성
                    request_data = {
                        "tableNumber":int(table_num),
                        "storeId": store_id,
                        "content": args["content"]
                    }
                    #print(f"🔹 [DEBUG] request_data 생성 완료: {request_data}")  # 요청 데이터 확인

                    # 🚀 send_request_notification 실행 전 로그 추가
                    #print("🚀 [DEBUG] send_request_notification 실행 시도...")
                    result = send_request_notification(request_data, session_token)  # 여기서 멈추는지 확인
                    #print(f"✅ [DEBUG] send_request_notification 실행 완료, 반환값: {result}")

                    return result  # 성공적으로 실행되었는지 확인

                except Exception as e:
                    #print(f"❌ [DEBUG] JSON 변환 또는 함수 실행 중 오류 발생: {e}")
                    return {"status": "error", "message": str(e)}

            #건의의 사항 생성 함수  
            elif function_name =="create_suggestion":
                #print("create_suggestion 호출됨")
                # JSON 파싱 확인
                try:
                    if isinstance(arguments, str):
                        #print("🔹 [DEBUG] arguments는 문자열이므로 JSON 변환 시도")
                        args = json.loads(arguments)  # JSON 파싱
                    else:
                        print("🔹 [DEBUG] arguments는 이미 JSON이므로 그대로 사용")
                        args = arguments

                    #print("✅ [DEBUG] json.loads() 성공:", args)  # JSON 변환 성공 확인

                    # 요청 데이터 생성
                    suggestion_data = {
                        "storeId": store_id,
                        "content": args["content"]
                    }
                    #print(f"🔹 [DEBUG] suggestion_data 생성 완료: {suggestion_data}")  # 요청 데이터 확인

                    # 🚀 send_suggestion 실행 전 로그 추가
                    #print("🚀 [DEBUG] send_suggestion 실행 시도...")
                    result = send_suggestion(suggestion_data, store_id)  # 여기서 멈추는지 확인
                    #print(f"✅ [DEBUG] send_suggestion 실행 완료, 반환값: {result}")

                    return result  # 성공적으로 실행되었는지 확인

                except Exception as e:
                    #print(f"❌ [DEBUG] JSON 변환 또는 함수 실행 중 오류 발생: {e}")
                    return {"status": "error", "message": str(e)}

            elif function_name == "get_menu_image":
                #print("✅ get_menu_image 호출됨")

                try:
                    args = json.loads(arguments) if isinstance(arguments, str) else arguments
                    image_data = {
                    "storeId": store_id,
                    "menuName": args["menuName"]
                    }


                    # 사진 요청 API 호출
                    result = show_menu_image(image_data, store_id)
                    #result = show_menu_image(args["menuName"])

                    return result
                except Exception as e:
                    #print(f"❌ [DEBUG] JSON 변환 또는 함수 실행 중 오류 발생: {e}")
                    return {"status": "error", "message": str(e)}

        
            else:
                return f"❌ 알 수 없는 함수 호출: {function_name}"
        else:
            return "Assistant Response: 함수 호출이 되지 않습니다."

    except Exception as e:
        #print("❌ JSON 파싱 오류 발생:", e)
        #print("❌ 문제의 arguments 값:", arguments)
        return f"❌ 함수 호출 처리 중 오류 발생: {e}"


# 함수: 주문 데이터를 서버로 전송
def post_order(final_order_data,session_token, store_id):
    #print("post_order 호출함")
    #print(f"🛠 store_id: {store_id}")
    """
    최종 주문 데이터를 POST 요청으로 서버에 전송합니다.
    요청 헤더에 sessionToken을 포함해야 함.
    """
    
    order_api_url= f"{api_url}/stores/{store_id}/orders"
    #print(f"🌐 [DEBUG] API 요청 URL: {order_api_url}")
    headers = {
        "sessionToken": session_token,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        
        response = requests.post(order_api_url, json=final_order_data,headers=headers)

        if response.status_code in [200, 201]:
            response_data = response.json()
            print("✅ 주문 성공!") 
            #return (json.dumps(response_data, indent=4, ensure_ascii=False))
            return response_data
        else:
            print(f"❌ 주문 생성 실패: HTTP {response.status_code}") 
            return (response.json())
    except requests.exceptions.RequestException as e:
        return f"❌ 요청 실패: {e}"


# 함수: 요청 데이터를 서버로 전송

def send_request_notification(request_data, session_token):
    #print("✅ send_request_notification 호출됨 - 요청을 서버로 전송합니다.")
    request_api_url = f"{api_url}/notification/new-request"
    headers = {
        #"Authorization": f"Bearer {session_token}",  # Bearer 형식 확인
        "sessionToken": session_token,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    #print(f"🔹 [DEBUG] 전송 데이터: {json.dumps(request_data, indent=4, ensure_ascii=False)}")
    #print(f"🔹 [DEBUG] API 요청 URL: {request_api_url}")
    #print(f"🔹 [DEBUG] 요청 헤더: {headers}")  

    try:
        #print("🚀 [DEBUG] 서버로 요청을 보냅니다...")
        response = requests.post(request_api_url, json=request_data, headers=headers, timeout=10)
        
        #print("✅ [DEBUG] 요청이 실행됨!")  # 이 로그가 찍히는지 확인!!
        #print(f"🔍 [DEBUG] 응답 코드: {response.status_code}")
        #print(f"🔹 [DEBUG] 응답 본문: {response.text}")

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
    #print("✅ send_request_notification 호출됨 - 건의를를 서버로 전송합니다.")

    suggestion_api_url = f"{api_url}/stores/{store_id}/suggestions"
    #print(f"🔹 [DEBUG] 전송 데이터: {json.dumps(request_data, indent=4, ensure_ascii=False)}")
    #print(f"🔹 [DEBUG] API 요청 URL: {request_api_url}")
    #print(f"🔹 [DEBUG] 요청 헤더: {headers}")  

    try:
        #print("🚀 [DEBUG] 서버로 요청을 보냅니다...")
        response = requests.post(suggestion_api_url, json=suggestion_data)
        
        #print("✅ [DEBUG] 요청이 실행됨!")  # 이 로그가 찍히는지 확인!!
        #print(f"🔍 [DEBUG] 응답 코드: {response.status_code}")
        #print(f"🔹 [DEBUG] 응답 본문: {response.text}")

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
    #print("✅ show_menu_image 호출됨 - 메뉴 사진을 가져옵니다.")

    # 올바른 URL 형식 적용
    menu_image_api_url = f"{api_url}/stores/{store_id}/menu/img?menuName={menuName}"

    try:
        #print(f"🚀 [DEBUG] 요청 URL: {url}")
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
    "description": "Handles user suggestion. If the assistant's response includes phrases like '건의 사항 내용', this function must be triggered.",
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
    session_token="1235" #임의로 세션토큰 지정
    store_id =" 1"
    table_num="2"
    chat_with_gpt(client,session_token, store_id, table_num)

