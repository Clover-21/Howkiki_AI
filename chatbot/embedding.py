import os
import faiss
import numpy as np
import pickle
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings  # ✅ import 수정

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY가 설정되지 않았습니다! `.env` 파일을 확인하세요.")

class FAISSIndexer:
    def __init__(self, text_file="data/haosum.txt", index_path="data/faiss_index/index.faiss", vector_path="data/faiss_index/vectors.pkl"):
        self.text_file = text_file
        self.index_path = index_path
        self.vector_path = vector_path
        self.embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)  # ✅ API 키 직접 전달
        self.index = None

    def load_text(self):
        """haosum.txt 파일을 불러오기"""
        with open(self.text_file, "r", encoding="utf-8") as f:
            return f.readlines()  # 한 줄씩 리스트로 저장

    def create_index(self):
        """텍스트를 벡터화하여 FAISS에 저장"""
        docs = self.load_text()
        doc_vectors = np.array(self.embeddings.embed_documents(docs)).astype("float32")

        self.index = faiss.IndexFlatL2(doc_vectors.shape[1])
        self.index.add(doc_vectors)

        # 저장
        faiss.write_index(self.index, self.index_path)
        with open(self.vector_path, "wb") as f:
            pickle.dump(docs, f)

        print(f"✅ FAISS 인덱스 저장 완료: {self.index_path}")

# 실행
if __name__ == "__main__":
    indexer = FAISSIndexer()
    indexer.create_index()
