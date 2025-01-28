import streamlit as st
import boto3
import json
import base64
import random
import string
import time

#Replace below value with actual DynamoDb Table name and invokeAgentLambdaFunctionName created by your CloudFormation template
table_name = 'agent_interactions'
invokeAgentLambdaFunctionName = 'InvokeBedrockAgentFunction'

region = boto3.Session().region_name
session = boto3.Session(region_name=region)
lambda_client = session.client('lambda')
#Create DynamoDB client
dynamodb_client = boto3.resource('dynamodb')

table = dynamodb_client.Table(table_name)

# Function to store citation information in DynamoDB
def store_citation_information(question,display_text, urls):
    #item_id = str(uuid.uuid4())
    item = {
        #'item_id': item_id,
        'session_id': st.session_state.session_id,
        'timestamp': int(time.time()),
        'question': question,
        'display_text': display_text,
        'urls': urls
    }
    print(f"item:{item}")
    table.put_item(Item=item)


def session_generator():
    # Generate random characters and digits
    digits = ''.join(random.choice(string.digits) for _ in range(4))  # Generating 4 random digits
    chars = ''.join(random.choice(string.ascii_lowercase) for _ in range(3))  # Generating 3 random characters
    
    # Construct the pattern (1a23b-4c)
    pattern = f"{digits[0]}{chars[0]}{digits[1:3]}{chars[1]}-{digits[3]}{chars[2]}"
    print("Session ID: " + str(pattern))

    return pattern

def create_download_link(file,filename):
    with open(file, "rb") as f:
        bytes = f.read()
        b64 = base64.b64encode(bytes).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Doc Download Link</a>'
        return href

# Add a function that will download the S3 file based on s3 url
def download_s3_file(s3_uri):
    s3 = boto3.client('s3')
    bucket_name, key = s3_uri.split('/', 2)[-1].split('/', 1)
    local_file_name = key.split('/')[-1]
    s3.download_file(bucket_name, key, local_file_name)
    return local_file_name


st.title("Smart Agentic RAG Chatbot Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize the agent session id
if 'session_id' not in st.session_state:
    st.session_state.session_id = session_generator()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])



# React to user input
if prompt := st.chat_input("What is up?"):

    # Display user input in chat message container
    question = prompt
    st.chat_message("user").markdown(question)

    # Call lambda function to get response from the model
    payload = json.dumps({"question":prompt,"sessionId": st.session_state.session_id})
    print(payload)
    result = lambda_client.invoke(
                FunctionName=invokeAgentLambdaFunctionName,
                Payload=payload
            )

    result = json.loads(result['Payload'].read().decode("utf-8"))
    print(f"result in streamlit:{result}")

    bytes =[]
    citations = []

    for chunk in result['body']['return_stream']:
        print(f"chunk:{chunk}")
        #Check if 'chunk is present in chunk['chunk'] and 'bytes' in chunk['chunk']
        if 'chunk' in chunk and 'bytes' in chunk['chunk']:
            bytes.append(chunk['chunk']['bytes'])
            # Check is attribution is present in chunk['chunk']
            if 'attribution' in chunk['chunk'] and 'citations' in chunk['chunk']['attribution']:
                for citation in chunk['chunk']['attribution']['citations']:
                    citations.append(citation)

    # Add user input to chat history
    st.session_state.messages.append({"role": "user", "content": question})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        urls = []
        # Loop over the citations list and display each citation in a separate chat message
        #Check if citations is not empty
        if citations:
            for citation in citations:
                display_text = citation['generatedResponsePart']['textResponsePart']['text']
                st.markdown(display_text)
                display_link=''
                for reference in citation['retrievedReferences']:
                    #increment count variable
                    url = reference['location']['s3Location']['uri']
                    help_text=reference['content']['text']
                    s3_download = download_s3_file(url)
                    download_url = create_download_link(s3_download, s3_download.split('/')[-1])
                    st.markdown(download_url, unsafe_allow_html=True, help=help_text)
                    urls.append(url)
        else:
            st.markdown(bytes[0])
        store_citation_information(question,bytes[0], urls)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": bytes[0]})
