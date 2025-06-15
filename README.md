# 🤖 하우키키
> 고객의 상황을 반영한 응대와 주문 결제 자동화를 제공하는 휴먼터치 AI 챗오더
<br>

### 🎙️ [캡스톤디자인 프로젝트 23팀] 하우키키 AI 레포지토리입니다.
- 본 AI 레포지토리는 고객 대화를 이해하고, 주문 및 매장 정보 등을 자동 응답하는 AI 챗오더 서버를 구현한 코드입니다.
- GPT-4o 기반 자연어 처리 모델과 RAG 구조를 활용하여 매장 정보를 반영한 응대를 제공하며, Function Calling으로 주문 및 요청 자동화를 처리합니다.
- Redis를 이용한 세션 관리, MongoDB 기반 벡터 검색, Flask 기반 REST API, EC2 + GitHub Actions 기반 CI/CD 자동 배포 환경을 구축하였습니다.

---
## 🔧 기술 스택
### 📌 Language & Framework
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)

### 📌 LLM & RAG
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-4B8BBE?style=for-the-badge&logoColor=white)

### 📌 Database
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)

### 📌 Server & Web
![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)

### 📌 DevOps & Deployment
![AWS EC2](https://img.shields.io/badge/AWS_EC2-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![AWS CodeDeploy](https://img.shields.io/badge/AWS_CodeDeploy-6DB33F?style=for-the-badge&logo=amazonaws&logoColor=white)

### 📌 Version Control
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)


### 🔎 기술 디테일

- **Language:** Python 3.10  
- **Framework:** Flask  
- **LLM Model:** OpenAI GPT-4o  
- **Embedding & RAG:** LangChain + MongoDB
- **Database:** MongoDB, Redis
- **Server 구성:** Gunicorn + Nginx (HTTPS + 리버스 프록시)  
- **Deployment:** AWS EC2 + GitHub Actions & AWS CodeDeploy 기반 CI/CD
---
# 1. 프로젝트 구조 및 주요 Source code 설명

📁 프로젝트 구조
```bash
Howkiki_AI/
├── chatbot/                # GPT 챗오더 및 RAG 관련 로직
│   ├── __init__.py
│   ├── bot.py              # 사용자 질문을 처리하고 GPT 응답 생성 (Function Calling 포함)
│   ├── embedding.py        # 매장 정보 벡터화 및 MongoDB 저장
│   ├── retriever.py        # 유사 문장 검색을 위한 벡터 검색 모듈 (RAG)
├── api/                    # Flask API 라우트 및 서버 구성
│   ├── __init__.py
│   ├── routes.py           # /chat 라우트: 사용자 질문을 받아 GPT 응답 반환
│   ├── config.py           # 환경 변수 또는 고정 설정 정보 (Redis, OpenAI, MongoDB 설정 등)
│   ├── redis_client.py     # Redis 클라이언트 초기화 및 세션 기반 대화 기록 저장/조회/삭제
├── data/
│   ├── housum.txt          # 매장 정보 텍스트 (샘플 데이터, 추후 교체 가능)
├── scripts/                # 서버 실행/중지/배포 스크립트
│   ├── start.sh
│   ├── stop.sh
│   ├── deploy.sh
├── app.py                  # Flask 실행 진입점
├── requirements.txt        # 의존성 목록
├── .gitignore              # git 추적 제외 파일 목록
├── appspec.yml
└── README.md
```
📁 주요 Source code 설명

| 경로 | 설명 |
| --- | --- |
| **`app.py`** | Flask 애플리케이션을 실행하는 메인 진입점 |
| **`chatbot/bot.py`** | 사용자의 질문을 GPT에게 전달하고, 필요 시 Function Calling을 통해 동작 수행 (예: 주문 처리) |
| **`chatbot/embedding.py`** | `housum.txt` 파일에서 줄 단위 문장을 추출하여 OpenAI 임베딩 후 MongoDB에 저장 (`embedding`, `text`, `user_id`, `timestamp` 포함) |
| **`chatbot/retriever.py`** | 쿼리 문장을 임베딩하고, MongoDB에서 동일한 `user_id`를 갖는 문서들과 코사인 유사도를 계산하여 상위 `top_k` 문서를 반환 |
| **`api/routes.py`** | `/chat` 라우트를 통해 사용자의 질문을 수신하고, GPT 응답을 생성하여 JSON으로 반환 (유효성 검사 및 로그 기록 포함) |
| **`api/redis_client.py`** | Redis 클라이언트를 초기화하며, 사용자 토큰 기반의 대화 기록 저장, 조회, 삭제 기능을 제공 (세션 유지에 사용) |
| **`api/config.py`** | Redis, MongoDB, OpenAI API 키 등의 설정 정보를 관리 |
| **`data/housum.txt`** | 매장 정보가 포함된 텍스트 파일, RAG 검색을 위한 벡터 인덱싱 대상 |
---
# 2. How to build and install

### 1. AI 레포지토리 Clone

```bash
git clone https://github.com/Clover-21/Howkiki_AI.git
cd Howkiki_AI  # 클론 후 해당 프로젝트로 이동
```
### 2. 가상환경 구성 (선택 사항)
```bash
python -m venv venv
source venv/bin/activate  # (Windows의 경우: venv\Scripts\activate)
```
### 3. 의존성 설치
```bash
pip install -r requirements.txt
```
### 4. 환경 변수 설정 (.env)

프로젝트 루트 디렉토리에 `.env` 파일을 생성한 후, 아래와 같은 형식으로 환경 변수를 작성합니다:

```env
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# 백엔드 API URL
api_url=your_backend_api_url

# Redis 설정
REDIS_HOST=your_redis_host
REDIS_PORT=your_redis_port
REDIS_DB=0
REDIS_PASSWORD=your_redis_password

# MongoDB 설정
MONGODB_URI=your_mongodb_url
```
>⚠️ .env 파일은 보안상 GitHub에 포함되지 않습니다.
><br>필요한 키 값은 교수님께 이메일로 별도 전달드렸습니다.

### 5. (선택) 초기화: 벡터 임베딩 등록
>⚠️ 이 작업은 데이터 초기화나 매장 정보 수정 시에만 필요합니다.

`data/housum.txt` 파일을 기반으로 매장 정보를 임베딩하여 MongoDB 벡터 DB에 저장하려면 다음 명령어를 실행하세요:
```bash
python chatbot/embedding.py
```
해당 명령어는 다음 작업을 수행합니다:
- data/housum.txt의 각 줄을 문서로 간주하고 임베딩 생성
- MongoDB의 howkiki.store 컬렉션에 user_id, text, embedding, timestamp 필드로 저장
- 기존 데이터는 초기화됨 (drop() 처리)
---
# 3. How to test

챗오더 AI 서버는 두 가지 방식으로 테스트할 수 있습니다:

1. **Postman**을 이용한 HTTP 요청 테스트
2. **터미널에서 인터랙티브 모드 실행**

이 중 인터랙티브 모드가 더 빠르고 편리하게 테스트할 수 있습니다.

서버는 기본적으로 `http://localhost:5000`에서 실행됩니다.

### 방법 1. Postman을 이용한 테스트

먼저 서버를 실행합니다:

```bash
# 아래 중 하나를 사용하세요
flask run
# 또는
python app.py
```
Postman에서 다음과 같이 요청을 보냅니다:

- **URL**: `http://127.0.0.1:5000/api/chat`
- **Method**: `POST`
- **Body (JSON)**:

```json
{
  "question": "여기에 사용자 입력 작성",
  "storeId": "1",
  "tableNum": "1",
  "token": "123456789"
}
```
응답 예시:
```json
{
  "function_call_result": "Assistant Response: 함수 호출이 되지 않습니다.",
  "response": "건물 내 주차장은 3시간 기본 무료로 이용할 수 있어요. 😊 추가로 궁금하신 사항이 있다면 언제든지 말씀해 주세요!",
  "storeId": "1",
  "tableNum": "1",
  "token": "123456789"
}
```
> 각 필드 설명:
> 
> - `function_call_result`: 함수 호출이 감지되었는지 여부 (테스트용)
> - `response`: 사용자 질문에 대한 응답
> - `storeId`, `tableNum`, `token`: 요청에서 입력한 값 그대로 반환됨
<br>

### 방법 2. 인터랙티브 모드 (터미널 실행)

터미널에서 아래 명령어를 실행하세요:
```bash
python chatbot/bot.py
```
예시:
```bash
안녕하세요. 호우섬입니다. 대화를 종료하려면 '종료'를 입력하세요.
고객 > 안녕
챗오더 > 안녕하세요! 😊 무엇을 도와드릴까요? 주문하시거나 궁금한 사항이 있다면 언제든지 말씀해 주세요.
함수 호출 결과: Assistant Response: 함수 호출이 되지 않습니다.
```
- 고객 >: 사용자가 입력하는 부분입니다.
- 대화 종료: `종료` 입력 또는 `Ctrl + C`
- 함수 호출 결과는 테스트용으로 함께 출력됩니다.

*Postman을 사용하지 않아도 대부분의 기능은 인터랙티브 모드에서 간편하게 테스트할 수 있습니다.

---

# 4. Sample Data 및 데이터베이스 구성

### 📁 샘플 데이터 설명
- `data/housum.txt` 파일은 기본 테스트용 샘플 매장 정보를 포함합니다.
- 각 줄은 하나의 문서로 간주되며, 임베딩 처리되어 MongoDB(`howkiki.store` 컬렉션)에 저장됩니다.
- 이 데이터는 챗오더가 질의에 답변할 수 있도록 정보 검색(RAG) 기반으로 사용됩니다.
> 실제 서비스 전환 시, `housum.txt` 파일을 실제 매장 정보로 교체합니다.

### 🗃️ 데이터베이스 설명

- **MongoDB**:
  - 사용 목적: 매장 정보의 벡터 저장 및 유사도 기반 검색
  - 사용 컬렉션: `howkiki.store`
  - 주요 필드:
    - `user_id`: 매장을 식별하는 ID
    - `text`: 원본 텍스트
    - `embedding`: OpenAI 임베딩 벡터
    - `timestamp`: 생성 시간

- **Redis**:
  - 사용 목적: 실시간 세션 데이터, 주문 요청 결과 저장 및 공유
  - 기본 DB: 0번 (변경 시 `REDIS_DB` 환경 변수로 설정)
  - 저장 예시: 토큰 기반 대화 기록, 주문 요청 결과 등
---
# 5. Open Source Used

본 프로젝트는 다음 오픈소스 라이브러리를 기반으로 개발되었습니다:

- [LangChain](https://www.langchain.com/)  
  - 목적: 문서 임베딩, Retriever 구성, LLM 인터페이스 통합에 사용

- [OpenAI API (openai-python)](https://platform.openai.com/docs/overview)  
  - 목적: GPT-4o 기반 응답 생성을 위한 LLM 연동에 사용되며, Function Calling 기능을 활용하여 주문 처리 등의 자동화를 지원

- [Flask](https://flask.palletsprojects.com)  
  - 목적: RESTful API 서버 구현에 사용되며, 라우팅 및 요청/응답 처리를 담당

- [pymongo](https://pymongo.readthedocs.io)
	- 목적: MongoDB와의 데이터 입출력 및 연결 관리를 위해 사용

- [redis-py](https://redis.io/docs/clients/python/)  
  - 목적: Redis 기반의 세션 관리 및 상태 정보 공유에 사용  

- [NumPy](https://numpy.org)  
  - 목적: 벡터 연산 및 코사인 유사도 계산 등에 활용
 
---

## ✏️ SW 구조도
![하우키키_SW구조도](https://github.com/user-attachments/assets/de43cbfc-c65b-4474-8839-6574c2ba3b6b)


## 🎬 하우키키 DEMO
[![YouTube](https://img.shields.io/badge/YouTube-FF0000?logo=youtube&logoColor=white&style=flat)](https://www.youtube.com/watch?v=7vHkNP8n9T8)
