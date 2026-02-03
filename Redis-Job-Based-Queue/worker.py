import logging
import os
import time
import redis
import json
import signal
import sys
import fibonacci
from config import (
    QUEUE_KEY, JOB_TTL_SECONDS, REDIS_DB,    REDIS_PORT,
    REDIS_HOST, REDIS_PASSWORD, REDIS_POOL_MAX_SIZE, REDIS_POOL_MIN_SIZE,
    REDIS_SOCKET_CONNECT_TIMEOUT, REDIS_SOCKET_TIMEOUT
)

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    max_connections=REDIS_POOL_MAX_SIZE,
    socket_timeout=REDIS_SOCKET_TIMEOUT,
    socket_connect_timeout=REDIS_SOCKET_TIMEOUT,
    decode_responses=True
)
r = redis.Redis(connection_pool=redis_pool)
logger.info(f"Worker Redis connection pool initialized: {REDIS_HOST}:{REDIS_PORT}")

def execute_task(task: str, payload: dict):
    """Do fib if task is fibonacci payload times, and do tribonacci payload times then return result as {k,v} = 
    {fib or trib, actual current value of it at end of payload times }"""
    times = payload.get("times", 0)
    
    if task == "fibonacci":
        generator = fibonacci.fib()  # Create new generator each time
        task_key = "fibonacci"
    elif task == "tribonacci":
        generator = fibonacci.trib()
        task_key = "tribonacci"
    else:
        raise ValueError(f"Unknown task: {task}")
    
    # Iterate the generator 'times' times to get the final value
    result = None
    for _ in range(times):
        result = next(generator)
    
    return {task_key: result}
    
    


def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
    sys.exit(0)

def main():
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    worker_pid = os.getpid()
    logger.info(f"Worker started (PID: {worker_pid}). Waiting for jobs...")
   
    while True:
        try:
            #BLPOP blocks until an item is available, timeout=1 means wake up every second
            # This allows the worker to respond to shutdown signals (Ctrl+C, SIGTERM)
            # {"job:queue":[LIST OF JOBS which are appened by RPUSH]}
            item = r.blpop(QUEUE_KEY, timeout=1)
            if item is None:
                continue
            
            _, job_json = item
            job = json.loads(job_json)
            job_id = job["job_id"]
            task = job["task"]
            payload = job["payload"]
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing job JSON: {e}")
            continue
        
        logger.info(f"Job {job_id} picked up - Task: {task}")
        #mark job as running 
        r.set(f"job:{job_id}:status","running",ex=JOB_TTL_SECONDS)
        logger.info(f"Job {job_id} status updated to running")
        
        try:
            start_compute = time.time()
            logger.debug(f"Executing task {task} for job {job_id}")
            result = execute_task(task,payload)
            compute_time = time.time() - start_compute
            #store result
            r.set(f"job:{job_id}:result",json.dumps(result),ex=JOB_TTL_SECONDS)
            #store status
            r.set(f"job:{job_id}:status","done",ex=JOB_TTL_SECONDS)
            logger.info(f"Job {job_id} completed successfully in {compute_time:.3f}s. Result: {result}")
        except redis.RedisError as e:
            logger.exception(f"Redis error while processing job {job_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Job {job_id} failed with error: {str(e)}", exc_info=True)
            r.set(
                f"job:{job_id}:error",
                json.dumps({"message": str(e)}),
                ex=JOB_TTL_SECONDS
            )
            r.set(f"job:{job_id}:status","failed",ex=JOB_TTL_SECONDS)
            logger.info(f"Job {job_id} status updated to failed")
        
if __name__ == "__main__":
    main()        
