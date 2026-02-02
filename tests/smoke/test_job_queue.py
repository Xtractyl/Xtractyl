# tests/smoke/test_job_queue.py
import uuid

import redis


def test_job_queue_is_alive(redis_host, redis_port):
    r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

    # 1) ping
    assert r.ping() is True

    # 2) minimal read/write roundtrip
    key = f"smoke:{uuid.uuid4()}"
    r.set(key, "ok", ex=30)
    assert r.get(key) == "ok"
