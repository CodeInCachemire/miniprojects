import os
import time
import redis
import json
import fibonacci


r = redis.Redis(host="localhost",port=6379,db=0,decode_responses=True)

QUEUE_KEY = "job:queue"
JOB_TTL_SECONDS = 60 * 60 #1 hour
  
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
    
    


def main():
    worker_pid = os.getpid()
    print(f"Worker started (PID: {worker_pid}). Waiting for jobs...")
    
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
            print(f"Error parsing job: {e}")
            continue
        
        #mark job as running 
        r.set(f"job:{job_id}:status","running",ex=JOB_TTL_SECONDS)
        
        try:
            start_compute = time.time()
            result = execute_task(task,payload)
            compute_time = time.time() - start_compute
            #store result
            r.set(f"job:{job_id}:result",json.dumps(result),ex=JOB_TTL_SECONDS)
            #store status
            r.set(f"job:{job_id}:status","done",ex=JOB_TTL_SECONDS)
            print(f"[PID: {os.getpid()}] Job {job_id} is done in {compute_time:.3f}s. Result: {result}")
        except Exception as e:
            r.set(
                f"job:{job_id}:error",
                json.dumps({"message": str(e)}),
                ex=JOB_TTL_SECONDS
            )
            r.set(f"job:{job_id}:status","failed",ex=JOB_TTL_SECONDS)
            print(f"[PID: {os.getpid()}] Job {job_id} has failed: {str(e)}")
        
if __name__ == "__main__":
    main()        
        
    
    






if __name__ == "__main__":
    main()