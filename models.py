from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base
from datetime import datetime



class AudioFile(Base):
    __tablename__ = "audiofiles"

    s3_key = Column(String(255), primary_key=True, nullable=False)  # Unique name in S3
    file_name = Column(String(255), nullable=False)  # User-friendly file name
    doctor_id = Column(String, nullable=False)
    patient_name = Column(String, nullable=False)
    created_at = Column(String, default=str(datetime.now().isoformat()))  # Timestamp of audio file creation
    # Relationship to transcription
    transcriptions = relationship("Transcription", back_populates="audiofile")



class Transcription(Base):
    __tablename__ = "transcription"
      # Foreign key to the AudioFile table
    s3_key = Column(String(255),  primary_key=True, nullable=False)  # S3 key for transcription file
    audio_s3_key = Column(Integer, ForeignKey("audiofiles.s3_key"), nullable=False)
    status = Column(String, default='IN_PROGRESS')  # 'IN_PROGRESS', 'COMPLETED', or 'FAILED'
    created_at = Column(String, default=str(datetime.now().isoformat()))  # Timestamp of transcription creation
 
    # Relationship back to AudioFile
    audiofile = relationship("AudioFile", back_populates="transcriptions")