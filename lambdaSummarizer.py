import boto3
import json 
from jinja2 import Template
# print(jinja2.__version)

print('Fine!!!!!')

s3_client = boto3.client('s3')
bedrock_runtime = boto3.client('bedrock-runtime')
sqs_client = boto3.client('sqs')
queue_url = "https://sqs.us-east-1.amazonaws.com/058264094555/audioSummary"

def lambda_handler(event, context):
    print('inside lambda_handler')
    
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    print('bucket: ', bucket)
    print('key: ', key)
    
    # One of a few different checks to ensure we don't end up in a recursive loop.
    if "-transcript.json" not in key: 
        print("This demo only works with *-transcript.json.")
        return
    
    try: 
        file_content = ""
        
        response = s3_client.get_object(Bucket=bucket, Key=key)
        
        file_content = response['Body'].read().decode('utf-8')
        
        transcript = extract_transcript_from_textract(file_content)

        print(f"Successfully read file {key} from bucket {bucket}.")

        print(f"Transcript: {transcript}")
        
        summary = bedrock_summarisation(transcript)
        print('summary: ', summary)
        
        message_body = json.dumps(summary)  # Encapsulate summary in JSON
        print('message_body: ', message_body)
        
        sqs_response = sqs_client.send_message(QueueUrl=queue_url, MessageBody=message_body)
        print(f"Summary sent to SQS queue: {queue_url}")
        print('sqs_response: ', sqs_response)
        
        result_key= key.split('.')[0] + '-' + 'results.txt'
        print('result_key: ', result_key)
        
        s3_client.put_object(
            Bucket=bucket,
            Key=result_key,
            Body=summary,
            ContentType='text/plain'
        )
        
    except Exception as e:
        print(f"Error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error occurred: {e}")
        }

    return {
        'statusCode': 200,
        'body': json.dumps(f"Successfully summarized {key} from bucket {bucket}. Summary: {summary}")
    }
    
    # return {
    #     'statusCode': 200,
    #     'body': json.dumps("Testing")
    # }
        
        
        
def extract_transcript_from_textract(file_content):
    print('inside extract_transcript_from_textract')

    transcript_json = json.loads(file_content)

    output_text = ""
    current_speaker = None

    items = transcript_json['results']['items']

    # Iterate through the content word by word:
    for item in items:
        speaker_label = item.get('speaker_label', None)
        content = item['alternatives'][0]['content']
        
        # Start the line with the speaker label:
        if speaker_label is not None and speaker_label != current_speaker:
            current_speaker = speaker_label
            output_text += f"\n{current_speaker}: "
        
        # Add the speech content:
        if item['type'] == 'punctuation':
            output_text = output_text.rstrip()  # Remove the last space
        
        output_text += f"{content} "
        
    return output_text
        

def bedrock_summarisation(transcript):
    print('inside bedrock_summarisation')
    
    with open('prompt_template.txt', "r") as file:
        template_string = file.read()

    data = {
        'transcript': transcript,
    }
    
    template = Template(template_string)
    prompt = template.render(data)
    
    print(prompt)
    
    kwargs = {
        "modelId": "amazon.titan-text-express-v1",
        "contentType": "application/json",
        "accept": "*/*",
        "body": json.dumps(
            {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 500,
                    "stopSequences": [],
                    "temperature": 0,
                    "topP": 0.9
                }
            }
        )
    }
    
    response = bedrock_runtime.invoke_model(**kwargs)

    summary = json.loads(response.get('body').read()).get('results')[0].get('outputText')    
    return summary
