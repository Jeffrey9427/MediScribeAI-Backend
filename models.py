from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base
from datetime import datetime



class AudioFile(Base):
    __tablename__ = "audiofiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)  # User-friendly file name
    s3_name = Column(String(255), nullable=False)  # Unique name in S3
    doctor_id = Column(String, nullable=False)
    patient_name = Column(String, nullable=False)
    created_at = Column(String, default=str(datetime.now().isoformat))  # Timestamp of audio file creation

    # Relationship to transcription
    transcriptions = relationship("Transcription", back_populates="audiofile")


class Transcription(Base):
    __tablename__ = "transcription"

    id = Column(Integer, primary_key=True, autoincrement=True)
      # Foreign key to the AudioFile table
    audio_id = Column(Integer, ForeignKey("audiofiles.id"), nullable=False)
    file_name = Column(String(255), nullable=False)  # Transcription file name
    s3_name = Column(String(255), nullable=False)  # S3 key for transcription file
    status = Column(String, default='IN_PROGRESS')  # 'IN_PROGRESS', 'COMPLETED', or 'FAILED'
    created_at = Column(String, default=str(datetime.now().isoformat))  # Timestamp of transcription creation

    # Relationship back to AudioFile
    audiofile = relationship("AudioFile", back_populates="transcriptions")