from api.config import Config
from pymongo import MongoClient
from langchain_openai import OpenAIEmbeddings
import numpy as np

class MongoDBRetriever:
    def __init__(self, db_name="howkiki", collection_name="store", top_k=3, user_id="default_user"):
        self.embeddings = OpenAIEmbeddings(openai_api_key=Config.OPENAI_API_KEY)
        self.client = MongoClient(Config.MONGODB_URI)
        self.collection = self.client[db_name][collection_name]
        self.top_k = top_k
        self.user_id = user_id  # 사용자 필터링을 위한 ID

    def cosine_similarity(self, a, b):
        # 두 벡터 간 코사인 유사도 계산
        a = np.array(a)
        b = np.array(b)
        if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
            return 0
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def search(self, query):
        # 쿼리 임베딩
        query_vec = self.embeddings.embed_documents([query])[0]

        # MongoDB에서 해당 user_id 문서만 조회
        docs = list(self.collection.find({"user_id": self.user_id}))

        if not docs:
            print("❌ 해당 사용자의 문서가 존재하지 않습니다.")
            return []

        # 각 문서와 쿼리 간 코사인 유사도 계산
        scored_docs = [
            (doc["text"], self.cosine_similarity(doc["embedding"], query_vec))
            for doc in docs
        ]

        # 유사도 상위 top_k 문서 반환
        top_docs = sorted(scored_docs, key=lambda x: x[1], reverse=True)[:self.top_k]
        return [doc[0] for doc in top_docs]
