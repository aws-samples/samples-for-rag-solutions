import streamlit as st
import boto3
import json
import os
import base64

region = boto3.Session().region_name
session = boto3.Session(region_name=region)
lambda_client = session.client('lambda')

#Replace with your Lambda function that will be invoking Bedrock Knowledge bases
lambda_function = "InvokeKnowledgeBaseFunction"

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


st.title("RAG Chatbot Assistant")

sessionId = ""
#sessionId = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
print(sessionId)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize session id
if 'sessionId' not in st.session_state:
    st.session_state['sessionId'] = sessionId

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
    payload = json.dumps({"question":prompt,"sessionId": st.session_state['sessionId']})
    print(payload)
    result = lambda_client.invoke(
                FunctionName=lambda_function,
                Payload=payload
            )

    result = json.loads(result['Payload'].read().decode("utf-8"))
    print(result)

    answer = result['body']['answer']
    sessionId = result['body']['sessionId']
    #Add citations
    citations = result['body']['citations']

    st.session_state['sessionId'] = sessionId

    # Add user input to chat history
    st.session_state.messages.append({"role": "user", "content": question})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        # Loop over the citations list and display each citation in a separate chat message
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

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": answer})
