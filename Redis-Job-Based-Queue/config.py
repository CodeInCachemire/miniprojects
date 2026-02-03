import os
import logging

#Logging configuration
logging.basicConfig(
    level = logging.INFO,
    format ='%(levelname)s - %(message)s - %(name)s - %(asctime)s'

)
logger = logging.getLogger(__name__)
#Redis config
REDIS_HOST = os.getenv("REDIS_HOST","localhost")
REDIS_PORT = os.getenv("REDIS_PORT",6379)
REDIS_DB = os.getenv("REDIS_DB", 0)
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD",None)

#Job config 
QUEUE_KEY = os.getenv("QUEUE_KEY","job:queue")
JOB_TTL_SECONDS = os.getenv("JOB_TTL_SECONDS", 60*60)

REDIS_POOL_MIN_SIZE = int(os.getenv("REDIS_POOL_MIN_SIZE", 5))
REDIS_POOL_MAX_SIZE = int(os.getenv("REDIS_POOL_MAX_SIZE", 20))
REDIS_SOCKET_TIMEOUT = int(os.getenv("REDIS_SOCKET_TIMEOUT", 5))
REDIS_SOCKET_CONNECT_TIMEOUT = int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", 5))

# Worker configuration
WORKER_TIMEOUT = int(os.getenv("WORKER_TIMEOUT", 300))  # 5 minutes

# API configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
logger.info(f"Configuration loaded - Redis: {REDIS_HOST}:{REDIS_PORT}")