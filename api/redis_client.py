import redis
import json
from api.config import Config



# Redis 클라이언트 생성
redis_client = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=Config.REDIS_DB,
    password=Config.REDIS_PASSWORD,
    decode_responses=True
)

def get_conversation(user_token):
    """ 사용자 토큰을 기반으로 대화 기록 조회 """
    key = f"conversation:{user_token}"
    try:
        conversation = redis_client.get(key)
        return json.loads(conversation) if conversation else []
    except (redis.RedisError, json.JSONDecodeError) as e:
        print(f"[Redis Error] get_conversation: {e}")
        return []


def save_conversation(user_token, conversation):
    """ 사용자 토큰을 키로 대화 기록을 Redis에 저장 """
    key = f"conversation:{user_token}"
    try:
        redis_client.set(key, json.dumps(conversation))
    except (redis.RedisError, TypeError) as e:
        print(f"[Redis Error] save_conversation: {e}")


def clear_conversation(user_token):
    """ 특정 사용자의 대화 기록을 삭제 """
    key = f"conversation:{user_token}"
    try:
        redis_client.delete(key)
    except redis.RedisError as e:
        print(f"[Redis Error] clear_conversation: {e}")
