import os
from dotenv import load_dotenv
import openai
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from chatbot.retriever import FAISSRetriever  # RAG 적용 (FAISS 검색)

load_dotenv()  # .env 파일에서 환경 변수 로드

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")

# API 키 설정 (공식 라이브러리 사용 방식)
openai.api_key = OPENAI_API_KEY

#전체 시스템 프롬프트 정의
system_prompt='''
당신은 음식점의 고객 서비스 챗봇 역할을 수행하는 AI 어시스턴트입니다. 다음의 역할과 정보를 기반으로 고객 요청에 응답하세요.:
현재 너는 테이블 5번의 주문을 받는 상황이야. - "tableNumber": 5

1. **주문 지원**:
   - 손님이 주문하고자 하는 메뉴와 수량을 파악하여 최종 주문 내역을 출력합니다.
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
   - 사용자가 "어, o, 주문할게" 등의 긍정의 답을 하면 "포장인가요, 매장 식사인가요?"라고 묻고,
     사용자의 답변에 따라 식사 방법('포장', '매장 식사')을 포함하여 출력하세요.

     예시:
     GPT:{최종 주문 내역은 다음과 같습니다:
     - 라구짜장: 1개
     - 양장피: 1개
     식사 방법: 포장
     주문하신 메뉴는 곧 준비될 예정입니다. 감사합니다! 추가로 필요한 사항이나 궁금한 점이 있으시면 언제든지 말씀해 주세요.}

   - 최종 주문 내역 출력 후 또 주문할 경우, 이전 최종 주문 내역은 출력하지 않고 새 주문만 처리하세요.
     예:
     GPT:{최종 주문 내역은 다음과 같습니다:
     - 라구짜장: 1개
     - 양장피: 1개
     식사 방법: 포장장
     주문하신 내용은 곧 준비될 예정입니다. 감사합니다! 추가로 필요한 사항이나 궁금한 점이 있으시면 언제든지 말씀해 주세요.}

     **최종 주문 출력 이후 사용자가 "양장피 하나 추가" 또는 "양장피 하나 주문" 이라고 하면:
     GPT: {양장피 1개 주문하겠습니다. 현재 주문 내역은 다음과 같습니다:
     - 양장피: 1개
     주문을 확정해도 될까요?}
    
   

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
    - 요청 사항은 **반드시 최종 주문이 내역이 있을 시시**에만 처리할 수 있습니다.
    - 최종 주문이 없는는 상태에서 요청 사항이 들어오면, 아래와 같이 응답하세요:
      - "최종 주문을 하지않아 요청을 처리할 수 없습니다. 먼저 주문을 해 주시겠어요? 😊"
      (단, 주문 요청(예: 음료 주문, 음식 주문 등)은 행동 요청과 다르다는 점을 고려하여, 주문 요청 사항은 최종 주문이 완료와 상관 없이 항상 수락락한다.) 

    - 사용자가 주문을 확정한 이후에는 요청 사항을 다음과 같이 처리합니다:
      - 블랙 하가우 테이크아웃 요청, 음악 소리 조절, 에어컨 온도 조정, 접시 치우기, 사장님 호출 등과 같은 요청사항이 들어오면 다음과 같이 응답하세요:
        - "해당 요청을 사장님께 전달해 드릴까요?"
        - 사용자가 '응', 'o' 등 긍정을 하면 "요청을 전달해드렸어요."라고 응답하세요.

6. **최종 주문 완료 상태 확인**:
   - 최종 주문 완료 여부를 확인하려면 **대화 기록에 '최종 주문 내역은 다음과 같습니다.' 문장이 포함되었는지 확인하세요.**
   - 이 문장이 포함된 경우, 최종 주문이 완료된 상태로 간주하고 요청 사항을 처리하세요.
   - 요청 사항이 들어오면 **"해당 요청을 사장님께 전달해 드릴까요?"**라고 묻고, 사용자가 긍정하면 요청을 수행하세요.
   - 건의 사항(예: 서비스 개선 의견 등)은 **"건의 사항으로 남길까요?"**라고 물어보세요.

7. **최종 주문 상태 예시**:
    - **최종 주문을 한번이라도 하지 않았을 때** (대화 기록에 '최종 주문 내역은 다음과 같습니다.' 문장이 없을 시)
      - 사용자: "에어컨 좀 꺼주세요."
      - GPT: "최종 주문을 하지지 않아 요청을 처리할 수 없습니다. 먼저 주문을 해 주시겠어요? 😊"

    - **최종 주문이 있을 때때**: 대화 기록에 '최종 주문 내역은 다음과 같습니다.' 문장이 있을 시)
      - **이전 대화 기록에 다음과 같은 이력이 있으면 요청 사항을 수락합니다.**
        {최종 주문 내역은 다음과 같습니다:
        - 소롱포: 3개
        - 식사 방법: 매장 식사
        주문하신 메뉴는 곧 준비될 예정입니다. 감사합니다! 추가로 필요한 사항이나 궁금한 점이 있으시면 언제든지 말씀해 주세요. 😊}
        
      - 사용자: "에어컨 좀 꺼주세요." "음악 소리 좀 줄여줘" 등등
      - GPT: "해당 요청을 사장님께 전달해 드릴까요?"
      - 사용자: "응"
      - GPT: "에어컨을 꺼달라는 요청을 전달해드렸어요." (사용자 요청 사항을 언급하며 응답한다.)

8. **메뉴 사진 제공 처리**
   고객이 "메뉴를 보여줘"라고 요청하면 메뉴 사진을 제공합니다.

   메뉴 사진은 **직접 표시**되도록 작성합니다.

   사용자가 "메뉴를 보여줘"라고 요청하면 다음과 같이 응답하세요:

   사용자: "메뉴를 보여줘"
   GPT:
   "여기 음식점의 메뉴 사진입니다! 😊

   [파이썬 코드로 메뉴 사진 보여주기]

   추가로 궁금한 메뉴나 추천 메뉴를 알고 싶으시면 말씀해 주세요! 🍽️"

9. **건의 사항 처리**:
   - 사용자가 서비스 개선점(예: 음악 소리가 크다, 테이블이 좁다 등)을 말하면 "건의 사항으로 남길까요?"라고 묻습니다.
   - 사용자가 긍정적인 답을 하면 "건의 사항으로 남겼습니다."라고 응답하세요.
   - 건의 사항은 기록으로 남기고 필요 시 사장님께 전달된다는 점을 안내하세요.

10. **접근성**:
   - 대화 흐름을 간단하고 직관적으로 유지하여 모든 연령대와 기술 수준의 고객이 쉽게 사용할 수 있도록 합니다.

11. **요구사항과 건의 사항 구별 처리**:
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

    # 검색된 정보가 있을 경우, 시스템 프롬프트에 추가
    if retrieved_info:
        system_prompt_with_context = f"""
        당신은 음식점 고객 서비스 챗봇입니다. 다음의 검색된 정보를 참고하여 답변하세요:

        --- 검색된 정보 ---
        {retrieved_info}
        -------------------

        고객의 질문에 대해 관련 정보만 제공하고, 확인되지 않은 내용은 '확인되지 않은 정보입니다.'라고 답하세요.
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
    #conversation_history.append({"role": "assistant", "content": assistant_reply})

    return assistant_reply


### 📌 **RAG 기반으로 사용자와 대화하는 함수**
def chat_with_gpt(client,session_token):
    """RAG 기반 챗봇 실행"""
    print("호우섬에 오신 것을 환영합니다! 😊")
    print("주문 또는 궁금한 점을 입력하세요. 대화를 종료하려면 '종료' 또는 '그만'을 입력하세요.\n")

    while True:
        question = input("작성해주세요: ")

        if question.lower() in ["종료", "그만"]:
            print("프로그램을 종료합니다.")
            break

        # RAG 기반 응답 생성
        response = get_rag_response(client, question)
        print(response)
        if conversation_history=="최종 주문 내역은 다음과 같습니다.":
            conversation_history=[{"role": "system", "content": system_prompt}]
        else:
            conversation_history.append({"role": "assistant", "content": response})

        # 추가적인 GPT 함수 호출 처리 (필요 시)
        gpt_functioncall(client, response,session_token)
        print("-------------------------------------------------------")

### 📌 **메뉴 사진을 보여주는 함수**
def show_menu_image():
    """메뉴 사진 출력 (추후 구현)"""
    print("여기 음식점의 메뉴 사진입니다! 😊")
    # 실제 이미지 표시 기능 추가 예정

### 📌 **GPT 기반 행동 요청 처리 함수**
def gpt_functioncall(client, response,session_token):
    """GPT 응답 기반으로 특정 행동 처리 """
     
    function_prompt = '''
    You are a helpful assistant for table 5. 사용자의 최종 주문만을 정리하고 처리하세요.
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
            function_name = gpt_response.choices[0].message.function_call.name
            arguments = gpt_response.choices[0].message.function_call.arguments

            # 함수 호출이 주문 생성일 경우
            if function_name == "create_order":
                #print("create_order 호출함")
                import json
                args = json.loads(arguments)
                #print("json 파싱 성공")
                final_order_data = {
                    "isTakeOut": args["isTakeOut"],  # 사용자 입력 반영
                    "tableNumber": 5, #테이블 5로 설정
                    "finalOrderDetails": [
                        {"menuName": item["menuName"], "quantity": item["quantity"]}
                        for item in args["finalOrderDetails"]
                    ]
                }
                #주문 API 호출(세션 토근 포함함)
                #print("🔹 최종 주문 데이터:", final_order_data)  # 추가 디버깅
                result = post_order(final_order_data,session_token)
                return result
            else:
                return f"❌ 알 수 없는 함수 호출: {function_name}"
        else:
            return "Assistant Response: 함수 호출이 되지 않습니다."

    except Exception as e:
        #print("❌ JSON 파싱 오류 발생:", e)
        #print("❌ 문제의 arguments 값:", arguments)
        return f"❌ 함수 호출 처리 중 오류 발생: {e}"


import requests, json
#주문 API URL
order_api_url = "http://15.164.233.144:8080/stores/1/orders" #가게1로 설정

# 요청 사항 API URL
request_api_url = "http://15.164.233.144:8080/notification/new-request"

# 함수: 주문 데이터를 서버로 전송
def post_order(final_order_data,session_token):
    #rint("post_order 호출함")
    """
    최종 주문 데이터를 POST 요청으로 서버에 전송합니다.
    요청 헤더에 sessionToken을 포함해야 함.
    """
    headers = {
        "sessionToken": session_token,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        
        response = requests.post(api_url, json=final_order_data,headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            print("✅ 주문 생성 성공!")
            #print(json.dumps(response_data, indent=4, ensure_ascii=False))
        else:
            print(f"❌ 주문 생성 실패: HTTP {response.status_code}")
            print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 실패: {e}")


# 함수 호출을 지원하기 위한 함수 사양 정의
function_specifications = [
    {
        "name": "create_order",  # 함수 이름: create_order
        "description":"Processes the final confirmed order only when '최종 주문 내역은' is explicitly mentioned in the user input.",
        "parameters": {
            "type": "object",
            "properties": {
                "isTakeOut": { #테이크 타웃 관련 변수수
                    "type": "boolean",
                    "description": "True if the order is for takeout, False if it is for dine-in."
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
            "required": ["finalOrderDetails"]
        }
    }
]

# 직접 실행 시 인터랙티브 모드 시작
if __name__ == '__main__':
    session_token="1235" #임의로 세션토큰 지정
    chat_with_gpt(client,session_token)

