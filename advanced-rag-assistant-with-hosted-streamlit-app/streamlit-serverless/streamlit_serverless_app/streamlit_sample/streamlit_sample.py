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

# Add a function to create S3 presigned URL for a S3 object file based on S3 path
#Change below function to just accept S3 URI and expiration date
def create_presigned_url(s3_uri, expiration=3600):
    s3 = boto3.client('s3')
    bucket_name, key = s3_uri.split('/', 2)[-1].split('/', 1)
    response = s3.generate_presigned_url('get_object',
                                          Params={'Bucket': bucket_name,
                                                  'Key': key},
                                          ExpiresIn=expiration)
    return response


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
    #st.chat_message("user").markdown(question)
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
            # Display the value in display_text such that new lines are also printed as actual new line          
            #st.markdown(display_text)
            st.markdown(display_text.replace('\n', '<br>'), unsafe_allow_html=True)
            #st.text(display_text)
            #st.markdown(f"<pre>{display_text}</pre>", unsafe_allow_html=True)
            #formatted_text = display_text.replace(' ', '&nbsp;').replace('\n', '<br>')
            #st.markdown(formatted_text, unsafe_allow_html=True)
            # Replace line 94 with:
            #st.markdown(f"<pre style='white-space: pre-wrap;'>{display_text}</pre>", unsafe_allow_html=True)




            display_link=''
            for reference in citation['retrievedReferences']:
                #increment count variable
                url = reference['location']['s3Location']['uri']
                image = None
                #If reference['content'] is empty check, get the value of image object from reference[metadata][x-amz-bedrock-kb-byte-content-source]
                if 'text' not in reference['content']:
                    image = reference['metadata']['x-amz-bedrock-kb-byte-content-source']
                    help_text=reference['metadata']['x-amz-bedrock-kb-description']
                    # Generate presigned url for image S3 object stored in image variable
                    image = create_presigned_url(image)

                else:
                    help_text=reference['content']['text']
                
                #s3_download = download_s3_file(url)
                #download_url = create_download_link(s3_download, s3_download.split('/')[-1])
                presigned_url = create_presigned_url(url);
                download_url = f"[Doc download link]({presigned_url})"

                #Show image if image object is not empty
                if image:
                    image_help = "![Image](" + image + ")" 
                    st.markdown(download_url, unsafe_allow_html=True, help=image_help)
                else:
                    st.markdown(download_url, unsafe_allow_html=True, help=help_text)
                

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": answer})

