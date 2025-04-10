import os
import boto3
import random
import string 
from boto3 import client
from botocore.config import Config

config = Config(read_timeout=1000,
    connect_timeout=1000,
    retries={"max_attempts": 10}
)


boto3_session = boto3.session.Session()
region = boto3_session.region_name



# get knowledge base id from environment variable
kb_id = os.environ.get("KNOWLEDGE_BASE_ID")
#print (kb_id)

# declare model id for calling RetrieveAndGenerate API

# Add value of model_id from environment variable
if os.environ.get("MODEL_ID"):
    model_id = os.environ.get("MODEL_ID")
else:
    model_id = "amazon.nova-pro-v1:0"

model_arn = f'arn:aws:bedrock:{region}::foundation-model/{model_id}'
bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime', config=config)

print(f"model_id:{model_id}, model_arn:{model_arn}")

def retrieveAndGenerate(input, kbId, model_arn, sessionId):
    try:
    #print(input, kbId, model_arn, sessionId)
        if sessionId != "":
            return bedrock_agent_runtime_client.retrieve_and_generate(
                input={
                    'text': input
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': kbId,
                        'modelArn': model_arn,
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': 50, 
                                'overrideSearchType': 'HYBRID'
                            }
                        }
                    }
                        
                },
                sessionId=sessionId
            )
        else:
            return bedrock_agent_runtime_client.retrieve_and_generate(
                input={
                    'text': input
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': kbId,
                        'modelArn': model_arn
                    }
                }
            )
    except Exception as e:
        # Display an error message if an exception occurs
        print(f"ERROR: Exception when calling retrieveAndGenerate: {e}")
    
def lambda_handler(event, context):
    # create a boto3 bedrock client
    query = event["question"]
    sessionId = event["sessionId"]
    response = retrieveAndGenerate(query, kb_id, model_arn, sessionId)
    generated_text = response['output']['text']
    sessionId = response['sessionId']
    citations = response['citations']
    print (generated_text)
    print (sessionId)
    bedrock_agent_runtime_client.close()

    return {
        'statusCode': 200,
        'body': {"question": query.strip(), "answer": generated_text.strip(), "sessionId":sessionId, "citations":citations}
    }
    
