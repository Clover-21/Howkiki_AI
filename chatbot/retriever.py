import os
import faiss
import numpy as np
import pickle
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings  # ✅ 최신 버전 사용

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY가 설정되지 않았습니다! `.env` 파일을 확인하세요.")

class FAISSRetriever:
    def __init__(self, index_path="data/faiss_index/index.faiss", vector_path="data/faiss_index/vectors.pkl"):
        self.index_path = index_path
        self.vector_path = vector_path
        self.embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)  # ✅ API 키 직접 전달!
        self.index = None
        self.texts = None
        self.load_index()

    def load_index(self):
        """FAISS 인덱스 로드"""
        try:
            self.index = faiss.read_index(self.index_path)
            with open(self.vector_path, "rb") as f:
                self.texts = pickle.load(f)  # 원본 텍스트 로드
        except FileNotFoundError:
            print("❌ FAISS 인덱스 파일이 없습니다. `embedding.py`를 먼저 실행하세요.")

    def search(self, query, top_k=3):
        """질문을 벡터화하여 FAISS에서 검색"""
        query_vector = np.array(self.embeddings.embed_documents([query])).astype("float32")
        D, I = self.index.search(query_vector, top_k)
        results = [self.texts[i] for i in I[0] if i >= 0]  # 검색된 문장 반환
        return results
