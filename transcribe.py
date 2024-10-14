
import boto3
from fastapi import APIRouter, FastAPI, Depends, HTTPException
from s3 import get_s3
from transcribe_service import TranscribeService
# from schemas import TranscriptionRequest
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(
    prefix="/transcribe",
    tags=["transcribe"]
)

s3 = get_s3()
transcribe = TranscribeService()

@router.post("/transcribe")
async def start_job(audio_s3_key: str, db: Session = Depends(get_db)):
    try:
        job = transcribe.start_job( audio_s3_key =  audio_s3_key, db=db)
        # Optionally, you can save the job information in the database here
        return {"status": "Job started successfully", "job": job}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting transcription job: {str(e)}")


@router.post("/get_transcription")
async def get_transcription(audio_s3_key:str, db: Session = Depends(get_db)):
    try:
        transcription = transcribe.get_result( audio_s3_key=audio_s3_key ,db=db)  # Adjust parameters as needed
        return transcription
    except HTTPException as e:
        # Raise the HTTP exception if it's an expected error (like not found)
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving transcription: {str(e)}")

    

