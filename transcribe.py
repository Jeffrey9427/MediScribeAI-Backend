
import boto3
from fastapi import APIRouter, FastAPI
from s3 import get_s3
from transcribe_service import TranscribeService
# from schemas import TranscriptionRequest

from database import get_db

router = APIRouter(
    prefix="/transcribe",
    tags=["transcribe"]
)

s3 = get_s3()
transcribe = TranscribeService()
@router.post("/transcibe")
async def start_job(file_name):
    transcribe.start_job(
            file_name= file_name
        )
    job = transcribe.get_result(job_name=f"{file_name}-transcript", db =get_db())

    return job
    
   

    

