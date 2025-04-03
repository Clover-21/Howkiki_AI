import os
from dotenv import load_dotenv

load_dotenv() #.env 파일 로드

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    api_url=os.getenv("api_url")


#환경 변수 검증
config = Config()
required_env_vars= {
    "OPENAI_API_KEY": config.OPENAI_API_KEY ,
    "api_url": config.api_url
    
}
for var_name, var_value in required_env_vars.items():
    if not var_value:
        raise ValueError(f"환경 변수 {var_name}가 설정되어 있지 않습니다.")