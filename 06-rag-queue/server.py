from fastapi import FastAPI, Query
from .queue.connection import queue
from .queue.worker import process_query
app = FastAPI()


@app.get('/')
def root():
    return {"status":'Server is up and running'}

@app.post('/chat')
def chat(
    query: str = Query(..., description="Chat Message")
):
    #put query in queue
    job = queue.enqueue(process_query,query)
    #tell user your query is queued
    return {"statuc":'queued',"job_id":job.id}
    