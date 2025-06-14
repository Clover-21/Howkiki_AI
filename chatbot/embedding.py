import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from api.config import Config
from pymongo import MongoClient
from langchain_openai import OpenAIEmbeddings
from datetime import datetime  # timestamp용 추가

class MongoDBIndexer:
    def __init__(self, text_file="data/haosum.txt", db_name="howkiki", collection_name="store", user_id="default_user"):
        self.text_file = text_file
        self.embeddings = OpenAIEmbeddings(openai_api_key=Config.OPENAI_API_KEY)
        self.client = MongoClient(Config.MONGODB_URI)
        self.collection = self.client[db_name][collection_name]
        self.user_id = user_id  # 사용자 ID(= 매장 id)

    def load_text(self):
        # 텍스트 파일을 줄 단위로 읽고 빈 줄 제거
        try:
            with open(self.text_file, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print("❌ 텍스트 파일이 존재하지 않습니다.")
            return []

    def create_index(self):
        docs = self.load_text()
        if not docs:
            print("❌ 문서 없음. 인덱싱 중단.")
            return

        vectors = self.embeddings.embed_documents(docs)

        self.collection.drop()  # 기존 데이터 삭제

        for doc, vec in zip(docs, vectors):
            self.collection.insert_one({
                "text": doc,                       # 원본 텍스트
                "embedding": vec,                  # 벡터 리스트
                "timestamp": datetime.utcnow(),    # 현재 시간 저장
                "user_id": self.user_id            # 사용자 ID (= 매장 id)
            })

        print(f"✅ MongoDB에 {len(docs)}개 문서 임베딩 저장 완료")

if __name__ == "__main__":
    indexer = MongoDBIndexer()
    indexer.create_index()
