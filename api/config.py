import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일 로드

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    api_url = os.getenv("api_url")

    # Redis 관련 환경 변수
    REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# 환경 변수 검증
config = Config()
required_env_vars = {
    "OPENAI_API_KEY": config.OPENAI_API_KEY,
    "api_url": config.api_url,
    "REDIS_HOST": config.REDIS_HOST,
    "REDIS_PORT": config.REDIS_PORT,
    "REDIS_DB": config.REDIS_DB,
    "REDIS_PASSWORD": config.REDIS_PASSWORD,
}

for var_name, var_value in required_env_vars.items():
    if var_value is None:
        raise ValueError(f"환경 변수 {var_name}가 설정되어 있지 않습니다.")
