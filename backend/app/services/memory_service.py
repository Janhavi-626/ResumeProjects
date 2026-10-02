from collections import defaultdict, deque

from app.config.settings import get_settings

_local_memory: dict[str, deque] = defaultdict(lambda: deque(maxlen=12))


def append_message(session_id: str, role: str, content: str) -> None:
    safe_content = content[:4000]
    _local_memory[session_id].append({"role": role, "content": safe_content})
    url = get_settings().redis_url
    if url:
        try:
            from redis import Redis

            client = Redis.from_url(url, socket_timeout=1, decode_responses=True)
            client.rpush(f"conversation:{session_id}", f"{role}:{safe_content}")
            client.ltrim(f"conversation:{session_id}", -12, -1)
            client.expire(f"conversation:{session_id}", 86400)
        except Exception:
            pass


def get_history(session_id: str) -> list[dict[str, str]]:
    return list(_local_memory[session_id])