import os
import time
import datetime
import boto3
import streamlit as st
import json
from audio_recorder_streamlit import audio_recorder

st.set_page_config(layout="wide")
st.title("Summarize & Analyze Sentiment of Audio Conversations Using Amazon Bedrock")

# tab1, tab2 = st.tabs(["Record Audio", "Upload Audio"])
file_name = ''
s3_client = boto3.client('s3', region_name='us-east-1')

# Replace with your SQS queue URL
sqs_client = boto3.client('sqs')
queue_url = "https://sqs.us-east-1.amazonaws.com/058264094555/audioSummary"

def save_audio_file(audio_bytes, file_extension):
    """
    Save audio bytes to a file with the specified extension.

    :param audio_bytes: Audio data in bytes
    :param file_extension: The extension of the output audio file
    :return: The name of the saved audio file
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"audio_{timestamp}-dialog.{file_extension}"

    with open(file_name, "wb") as f:
        f.write(audio_bytes)

    return file_name

def upload_file(file_name):
    # st.markdown('Inside upload_file')
    bucket_name = 'audiofilebucketdlai'
    # st.write('file_name', file_name)
    try:
        # Upload file to an S3 object from the specified local path
        s3_client.upload_file(file_name, bucket_name, file_name)
        # st.markdown(f"Object '{file_name}' uploaded to bucket '{bucket_name}'")
        st.markdown(f"Successfully uploaded the file!!! 😃", unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f"Error: {str(e)}")

# def download_file(file_name):
    # st.markdown('Inside download_file')
    # bucket_name = 'transcribedandprocessedtextfilebucket'
    # key = 'transcription-job-' + file_name.split('.')[0] + '-transcript-results.txt'
    # st.write('key from download_file: ', key)
    # try:
    #     # Download the object from S3 to the specified local path
    #     # s3_client.download_file(bucket_name, object_key, f"./{object_key}")
    #     object_response = s3_client.get_object(
    #         Bucket=bucket_name,
    #         Key=key
    #     )

    #     st.markdown(f"Downloaded '{key}' from bucket '{bucket_name}'")
    #     return object_response
    
    # except Exception as e:
    #     st.markdown(f"Error: {str(e)}")


# Implement logic to check for summary in SQS (separate function)
def check_for_summary():
    # st.write("Inside check_for_summary()")
    st.markdown(f"Waiting for Summary and Sentiment Analysis... 😬", unsafe_allow_html=True)
    while True:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            WaitTimeSeconds=10  # Adjust wait time as needed
        )
        messages = response.get('Messages', [])
        if messages:
            for message in messages:
                print(message)
                message_body = json.loads(message['Body'])
                print('message_body: ', message_body)

                # Parse the JSON string to access the data
                summary_data = json.loads(message_body)
                print('summary_data: ', summary_data)

                # Extract sentiment and summary
                sentiment = summary_data['sentiment']
                summary_text = summary_data['summary']

                # st.write('sentiment: ', sentiment)
                # st.write('summary_text: ', summary_text)


                if sentiment == 'Positive' or sentiment == 'positive':
                    st.markdown(f"Sentiment: <span style='color:#33FF71'>{sentiment.upper()}</span>", unsafe_allow_html=True)
                elif sentiment == 'negative':
                    st.markdown(f"Sentiment: <span style='color:#FF6433'>{sentiment.upper()}</span>", unsafe_allow_html=True)
                elif sentiment == 'sad':
                    st.markdown(f"Sentiment: <span style='color:#FFDD33'>{sentiment.upper()}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"Sentiment: <span style='color:#33DAFF'>{sentiment.upper()}</span>", unsafe_allow_html=True)

                # st.write('Sentiment: ', .upper())
                # st.write('Sentiment: ', sentiment)   
                st.text_area('Summary: ', summary_text)
                
                # Delete the message from the queue
                sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
                break  # Exit the loop when a message is received
            return  # Exit the function after processing the message


# Upload Audio tab
audio_file = st.file_uploader("Upload Audio", type=["mp3"])
if audio_file:
    audio_bytes = None
    file_extension = audio_file.type.split('/')[1]
    file_name = save_audio_file(audio_file.read(), "mp3")

# Record Audio tab
audio_bytes = audio_recorder()
if audio_bytes:
    audio_file = None
    st.audio(audio_bytes, format="audio/wav")
    file_name =save_audio_file(audio_bytes, "mp3")

# Transcribe button action
if audio_bytes or audio_file:
    if st.button("Transcribe"):
        # Find the newest audio file
        # audio_file_path = max(
        #     [f for f in os.listdir(".") if f.startswith("audio")],
        #     key=os.path.getctime,
        # )

        # st.markdown(file_name)
        upload_file(file_name)
        check_for_summary()
