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
logger.propagate = False  # 중복 로그 방지

# 핸들러가 이미 없을 때만 추가
if not logger.handlers:
    file_handler = logging.FileHandler(log_file_path)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# Redis 클라이언트 초기화
redis_client = None

def get_redis_client():
    """Redis 클라이언트 반환 또는 재연결 시도"""
    global redis_client
    try:
        if redis_client and redis_client.ping():
            return redis_client
        else:
            redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                password=Config.REDIS_PASSWORD,
                decode_responses=True
            )
            redis_client.ping()
            logger.info("[Redis] 연결(또는 재연결) 성공")
            return redis_client
    except redis.RedisError as e:
        logger.error(f"[Redis 연결 실패]: {e}")
        return None

def get_conversation(user_token):
    """ 사용자 토큰을 기반으로 대화 기록 조회 """
    key = f"conversation:{user_token}"
    client = get_redis_client()
    if not client:
        return []
    try:
        conversation = client.get(key)
        return json.loads(conversation) if conversation else []
    except (redis.RedisError, json.JSONDecodeError) as e:
        logger.error(f"[Redis Error] get_conversation: {e}")
        return []

def save_conversation(user_token, conversation, ttl=3600):
    """ 사용자 토큰을 키로 대화 기록을 Redis에 저장 (TTL 1시간 기본) """
    key = f"conversation:{user_token}"
    client = get_redis_client()
    if not client:
        return
    try:
        serialized = json.dumps(conversation)
        client.set(key, serialized, ex=ttl)
    except (redis.RedisError, TypeError, ValueError) as e:
        logger.error(f"[Redis Error] save_conversation: {e}")

def clear_conversation(user_token):
    """ 특정 사용자의 대화 기록을 삭제 """
    key = f"conversation:{user_token}"
    client = get_redis_client()
    if not client:
        return
    try:
        client.delete(key)
    except redis.RedisError as e:
        logger.error(f"[Redis Error] clear_conversation: {e}")
