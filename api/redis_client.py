import redis
import json
import os
import logging
from api.config import Config

# 로그 디렉토리와 파일 경로 설정
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, 'redis.log')

# 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(log_file_path)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Redis 클라이언트 생성 (예외 처리 포함)
try:
    redis_client = redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=Config.REDIS_DB,
        password=Config.REDIS_PASSWORD,
        decode_responses=True
    )
    redis_client.ping()
    logger.info(" Redis 연결 성공")
except redis.RedisError as e:
    logger.error(f"[Redis 연결 실패]: {e}")
    redis_client = None

def get_conversation(user_token):
    """ 사용자 토큰을 기반으로 대화 기록 조회 """
    key = f"conversation:{user_token}"
    try:
        conversation = redis_client.get(key)
        return json.loads(conversation) if conversation else []
    except (redis.RedisError, json.JSONDecodeError) as e:
        logger.error(f"[Redis Error] get_conversation: {e}")
        return []


def save_conversation(user_token, conversation):
    """ 사용자 토큰을 키로 대화 기록을 Redis에 저장 """
    key = f"conversation:{user_token}"
    try:
        redis_client.set(key, json.dumps(conversation))
    except (redis.RedisError, TypeError) as e:
        logger.error(f"[Redis Error] save_conversation: {e}")

def clear_conversation(user_token):
    """ 특정 사용자의 대화 기록을 삭제 """
    key = f"conversation:{user_token}"
    try:
        redis_client.delete(key)
    except redis.RedisError as e:
        logger.error(f"[Redis Error] clear_conversation: {e}")
