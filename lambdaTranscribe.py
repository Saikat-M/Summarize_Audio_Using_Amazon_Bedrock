import json
import boto3
import uuid
import os

s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')

def lambda_handler(event, context):
    # Extract the bucket name and key from the incoming event
    print('event: ', event)
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    print('key: ', bucket)
    print('key: ', key)
    
    # One of a few different checks to ensure we don't end up in a recursive loop.
    if "-dialog.mp3" not in key: 
        print("This demo only works with *-dialog.mp3.")
        return

    try:
        
        job_name = 'transcription-job-' + key.split('.')[0] # Needs to be a unique name
        print('job_name: ', job_name)
        print('Text_Bucket_Nam: ', os.environ['S3BUCKETNAMETEXT'])
        OutputKey_name = job_name +'-transcript.json'

        response = transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': f's3://{bucket}/{key}'},
            MediaFormat='mp3',
            LanguageCode='en-US',
            OutputBucketName= os.environ['S3BUCKETNAMETEXT'],  # specify the output bucket
            OutputKey=OutputKey_name,
            Settings={
                'ShowSpeakerLabels': True,
                'MaxSpeakerLabels': 10
            }
        )
        print('response: ', response)
        
    except Exception as e:
        print(f"Error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error occurred: {e}")
        }

    return {
        'statusCode': 200,
        'body': json.dumps(f"Submitted transcription job for {key} from bucket {bucket}.")
    }