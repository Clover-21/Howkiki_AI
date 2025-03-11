import os
from dotenv import load_dotenv

load_dotenv() #.env 파일 로드

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    order_api_url=os.getenv("order_api_url")
    request_api_url=os.getenv("request_api_url")
    suggestion_api_url=os.getenv("suggestion_api_url")
    menu_image_api_url=os.getenv("menu_image_api_url")


#환경 변수 검증
config = Config()
required_env_vars= {
    "OPENAI_API_KEY": config.OPENAI_API_KEY ,
    "order_api_url": config.order_api_url,
    "request_api_url": config.request_api_url,
    "suggestion_api_url": config.suggestion_api_url,
    "menu_image_api_url": config.menu_image_api_url
}
for var_name, var_value in required_env_vars.items():
    if not var_value:
        raise ValueError(f"환경 변수 {var_name}가 설정되어 있지 않습니다.")