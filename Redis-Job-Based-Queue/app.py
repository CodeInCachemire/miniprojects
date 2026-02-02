import json
from typing import Optional, Any
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
import redis

app = FastAPI()
r = redis.Redis(host="localhost", port = 6379, decode_responses=True)
QUEUE_KEY = "job:queue"
JOB_TTL_SECONDS = 60*60 #hour

class SubmitRequest(BaseModel):
    task: str
    payload: dict

class ResponseRequest(BaseModel):
    job_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[Any] = None
    
@app.get("/health")
def health():
    return {"msg": "Alive"}


@app.post("/submit",response_model = ResponseRequest)
def submit_job(req: SubmitRequest):
   
    job_id = str(uuid.uuid4())
    
    #define a job
    job = {
        "job_id": job_id,
        "task" : req.task,
        "payload" : req.payload,
    }
    
    r.set(f"job:{job_id}:status","queued", ex=JOB_TTL_SECONDS) #fast access of the values of each job
    
    r.rpush(QUEUE_KEY,json.dumps(job)) #push to tail of job queue
    
    return ResponseRequest(
        job_id= job_id,
        status= "queued",
        )

@app.get("/submit/{job_id}")
def get_status(job_id: str):
    status = r.get(f"job:{job_id}:status")
    if status is None:
        return ResponseRequest(job_id = job_id, status = "unknown")
    if status == "done":
        result = r.get(f"job:{job_id}:result")
        return ResponseRequest(job_id= job_id, status = status, result= json.loads(result) if result else None)
    if status == "failed":
        err = r.get(f"job:{job_id}:error")
        return ResponseRequest(job_id= job_id, status = status, error = json.loads(err) if err else None)
    
    return ResponseRequest(job_id= job_id, status = status)


