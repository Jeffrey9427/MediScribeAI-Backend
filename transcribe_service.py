import boto3
from sqlalchemy.orm import Session
import json
from settings import *
import time
from models import Transcription
from fastapi import HTTPException
import uuid







class TranscribeService:
        def __init__(self):
            self.client = boto3.client("transcribe",
            aws_access_key_id = AWS_ACCESS_KEY_ID,
            aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
            region_name ='ap-southeast-1')

            # self.s3Client = boto3.client('s3')

        def create_s3_name(self, file_name, doctor_id ):
            unique_id = str(uuid.uuid4())
            return f"{doctor_id}_{unique_id}_{file_name}-transcript"
             


        def start_job (self, audio_s3_key: int, db: Session):
                job_name = f"{audio_s3_key}_transcript"
                self.client.start_transcription_job(
                    TranscriptionJobName= job_name,
                    IdentifyMultipleLanguages=True,
                    LanguageOptions = [
                        'en-US', 'id-ID'
                    ],

                    LanguageIdSettings={
                    # 'en-US': {
                    #     'VocabularyName': 'my-en-US-vocabulary',
                    #     'VocabularyFilterName': 'my-en-US-vocabulary-filter',
                    #     'LanguageModelName': 'my-en-US-language-model'
                    #     },
                    'id-ID': {
                        'VocabularyName': 'MedicalVocab-ID'
                        }   
                    },

                    Media={
                        "MediaFileUri": f"s3://mediscribe/audios/{audio_s3_key}"
                    },

                    Settings = {
                        'ShowSpeakerLabels': True,
                        'MaxSpeakerLabels': 4
                    },
                    OutputBucketName = 'mediscribe',
                    OutputKey = f'transcriptions/{job_name}.json'     
                )
            
                job_record = Transcription(
                    audio_s3_key = audio_s3_key,
                    s3_key=job_name  # This is where the transcript will be stored in S3
                )

                # Commit the job record to the database
                db.add(job_record)
                db.commit()
                db.refresh(job_record)

            
       

        
        # def get_job_status(self, job_name: str, db: Session):
        #     # Long polling logic to wait for job completion
        #     while timeout > 0:
        #         response = self.client.get_transcription_job(TranscriptionJobName=job_name)
        #         job_status = response['TranscriptionJob']['TranscriptionJobStatus']

        #         if job_status == "COMPLETED":
        #             job_record = TranscriptionJob( 
        #             doctor_id = doctor_id,
        #             patient_name = patient_name
        #             file_name= file_name,
        #             s3_name=job_name,
        #             )
                
                    
        #             db.add(job_record)
        #             db.commit()
        #             db.refresh(job_record)  # Return the job record after it's saved
                    
        #             return {"status": "COMPLETED", "Data": job_record}
                
        #         elif job_status == "FAILED":
        #             raise HTTPException(status_code=500, detail=f"Transcription job failed: {response['TranscriptionJob']['FailureReason']}")
                
        #         timeout -= 1
        #         time.sleep(5)  # Wait for 5 seconds before checking again

        #     return {"status": "IN_PROGRESS"}
        
         

        def get_result(self, audio_s3_key: str, db: Session):

            transcript_inDb = db.query(Transcription).filter_by(audio_s3_key =audio_s3_key ).first()
            
            if not transcript_inDb:
                raise HTTPException(status_code=404, detail=f"Transcript for audio{audio_s3_key} not found in the database")
            
            s3_name = transcript_inDb.s3_key
            if transcript_inDb.status == 'COMPLETED':
                transcript_inS3 = boto3.client('s3').get_object(Bucket='mediscribe', Key=f'transcriptions/{s3_name}.json')
                transcript_json = json.loads(transcript_inS3["Body"].read().decode("utf-8"))
                        # Retrieve audio segments from results
                return transcript_json.get('results', {}).get('audio_segments', [])
            
            elif transcript_inDb.status == 'FAILED':

                # If the job failed, raise an exception with the failure reason
                raise HTTPException(status_code=500, detail=f"Transcription job failed")
            else:

                timeout = 60
                while timeout > 0:
                    response = self.client.get_transcription_job(TranscriptionJobName=s3_name)
                    job_status = response['TranscriptionJob']['TranscriptionJobStatus']
                    if job_status in ["COMPLETED", "FAILED"]:
                        transcript_inDb.status = job_status  # Update the status to COMPLETED or FAILED
                        db.commit()
                        if job_status == "COMPLETED":
                            transcript_data = boto3.client('s3').get_object(Bucket='mediscribe', Key=f'transcriptions/{s3_name}.json')
                            transcript_json = json.loads(transcript_data["Body"].read().decode("utf-8"))
                            
                         # Return the job record after it's saved
                                
                            # return {"status": "COMPLETED", "Data": job_record}

                            # Retrieve audio segments from results
                            return transcript_json.get('results', {}).get('audio_segments', [])
                            
                        break
                    elif job_status == "FAILED":
                        raise Exception(f"Transcription job failed: {response['TranscriptionJob']['FailureReason']}")
                    
                    timeout -= 1
                    time.sleep(5)
                # return {"status": "IN_PROGRESS"}
        
    
        # def get_result(transcript_uri):
          
        
           



# from __future__ import print_function
# import time
# import boto3
# transcribe = boto3.client('transcribe')
# job_name = "my-first-transcription-job"
# job_uri = "s3://DOC-EXAMPLE-BUCKET/my-input-files/my-media-file.flac"
# transcribe.start_transcription_job(
#     TranscriptionJobName = job_name,
#     Media = {
#         'MediaFileUri': job_uri
#     },
#     OutputBucketName = 'DOC-EXAMPLE-BUCKET',
#     OutputKey = 'my-output-files/', 
#     MediaFormat='flac',
#     IdentifyLanguage=True,  (or IdentifyMultipleLanguages=True)
#     LanguageOptions = [
#         'en-US', 'hi-IN'
#     ],
#     LanguageIdSettings={
#         'en-US': {
#             'VocabularyName': 'my-en-US-vocabulary',
#             'VocabularyFilterName': 'my-en-US-vocabulary-filter',
#             'LanguageModelName': 'my-en-US-language-model'
#         },
#         'hi-IN': {
#             'VocabularyName': 'my-hi-IN-vocabulary',
#             'VocabularyFilterName': 'my-hi-IN-vocabulary-filter'
#         }   
#     }
# )

