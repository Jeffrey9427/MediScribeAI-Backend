from sqlalchemy.orm import Session, Query
from sqlalchemy.sql import extract
import models
import schemas
from datetime import date, datetime, timedelta
from typing import Optional, Union

def get_AudioFiles(db:Session):
    return db.query(models.AudioFile).filename, db.query(models.AudioFile).created_at   # for frontend, also the duration

def get_AudioFile_by_id(id: int, db: Session):
    return db.query(models.AudioFile).filter(models.AudioFile.id == id).first()

def get_AudioFile_s3name_by_id(id: int, db: Session) -> str:
    return get_AudioFile_by_id(id=id, db=db).s3_key

def get_AudioFile_filename_by_id(id: int, db: Session) -> str:
    return get_AudioFile_by_id(id=id, db=db).file_name

def delete_AudioFile(id: int, db: Session):
    db_audio = get_AudioFile_by_id(id=id, db=db)
    db.delete(db_audio)
    return db


def new_AudioFile(doctor_id,patient_name,s3_name,filename, db: Session):
    audio_file_record = models.AudioFile(
        doctor_id=doctor_id,
        file_name=filename,
        s3_key=s3_name,
        patient_name=patient_name
    )
    db.add(audio_file_record)
    db.commit()
    db.refresh(audio_file_record)  # Return the newly added record

    return audio_file_record