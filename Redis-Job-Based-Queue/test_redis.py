import redis
import pytest 

class Test_Redis:

    def test_redis(self):
        r = redis.Redis(
            host="localhost",
            port = 6379,
            decode_responses= True               
                        )

        assert r.ping() is True, "REDIS does not respond to PING"
        r.set("test_key","BrOsEf")
        value = r.get("test_key")
        assert value == "BrOsEf" , f"Did not recieve expected value: {value}"
        r.delete("test_key")
        assert r.get("test_key") is None