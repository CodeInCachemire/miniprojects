import json
import uuid
import redis
import logging
from fastapi import FastAPI
from schemas import (SubmitRequest, ResponseRequest)
from config import (
    QUEUE_KEY, JOB_TTL_SECONDS, REDIS_DB,    REDIS_PORT,
    REDIS_HOST, REDIS_PASSWORD, REDIS_POOL_MAX_SIZE, REDIS_POOL_MIN_SIZE,
    REDIS_SOCKET_CONNECT_TIMEOUT, REDIS_SOCKET_TIMEOUT
)

logger = logging.getLogger(__name__)

app = FastAPI()
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
logger.info(f"Redis connection pool initialized with max_connections={REDIS_POOL_MAX_SIZE}")

@app.get("/")
def health():
    logger.debug(f"Health endpoint is called.")
    return {"msg": "Alive"}


@app.post("/submit",response_model = ResponseRequest)
def submit_job(req: SubmitRequest):
    job_id = str(uuid.uuid4())
    logger.info(f"Job created: {job_id} - Task: {req.task}")
    
    #define a job
    job = {
        "job_id": job_id,
        "task" : req.task,
        "payload" : req.payload,
    }
    
    try:
        r.set(f"job:{job_id}:status","queued", ex=JOB_TTL_SECONDS) #fast access of the values of each job
        logger.info(f"Job {job_id} status set to queued")
        r.rpush(QUEUE_KEY,json.dumps(job)) #push to tail of job queue
        logger.info(f"Job {job_id} pushed to queue: {QUEUE_KEY}")
    except redis.RedisError as e:
        logger.exception(f"Redis error while submitting job {job_id}: {str(e)}")
        raise  
    return ResponseRequest(
        job_id= job_id,
        status= "queued",
        )

@app.get("/submit/{job_id}")
def get_status(job_id: str):
    logger.info(f"Status check requested for job: {job_id}")
    
    try:
        status = r.get(f"job:{job_id}:status")
        
        if status is None:
            logger.warning(f"Job {job_id} not found - status: unknown")
            return ResponseRequest(job_id = job_id, status = "unknown")
        
        if status == "done":
            logger.info(f"Job {job_id} completed successfully")
            result = r.get(f"job:{job_id}:result")
            return ResponseRequest(job_id= job_id, status = status, result= json.loads(result) if result else None)
        
        if status == "failed":
            logger.error(f"Job {job_id} failed")
            err = r.get(f"job:{job_id}:error")
            return ResponseRequest(job_id= job_id, status = status, error = json.loads(err) if err else None)
        
        logger.info(f"Job {job_id} status: {status}")
        return ResponseRequest(job_id= job_id, status = status)
    except redis.RedisError as e:
        logger.exception(f"Redis error while getting status for job {job_id}: {str(e)}")
        raise


