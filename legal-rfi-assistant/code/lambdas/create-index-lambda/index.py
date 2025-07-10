from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import os
import boto3
import json
import logging
import cfnresponse
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Event: {json.dumps(event)}")
    
    session = boto3.Session()
    creds = session.get_credentials()
    
    collection_host = os.environ.get('COLLECTION_HOST')
    index_name = os.environ.get('VECTOR_INDEX_NAME')
    region = os.environ.get('REGION_NAME')
    
    if not collection_host:
        logger.error("COLLECTION_HOST environment variable is not set")
        cfnresponse.send(event, context, cfnresponse.FAILED, {})
        return
    
    host = collection_host.split("//")[1] if "//" in collection_host else collection_host
    service = "aoss"
    status = cfnresponse.SUCCESS
    response = {}
    
    try:
        auth = AWSV4SignerAuth(creds, region, service)
        
        client = OpenSearch(
            hosts=[{"host": host, "port": 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            pool_maxsize=20,
        )
        
        if event["RequestType"] == "Create":
            logger.info(f"Creating index: {index_name}")
            
            index_body = {
                "settings": {
                    "index.knn": True,
                    "index.knn.algo_param.ef_search": 512,
                },
                "mappings": {
                    "properties": {
                        "bedrock-knowledge-base-default-vector": {
                            "type": "knn_vector",
                            "dimension": 1024,
                            "method": {
                                "space_type": "innerproduct",
                                "engine": "faiss",
                                "name": "hnsw",
                                "parameters": {
                                    "m": 16,
                                    "ef_construction": 512,
                                },
                            },
                        },
                        "AMAZON_BEDROCK_METADATA": {"type": "text", "index": False},
                        "AMAZON_BEDROCK_TEXT_CHUNK": {"type": "text"},
                        "id": {"type": "text"},
                    }
                },
            }
            
            response = client.indices.create(index=index_name, body=index_body)
            logger.info(f"Response: {response}")
            
            # Wait for index to be ready
            logger.info("Waiting 60 seconds for index creation")
            time.sleep(60)
            
        elif event["RequestType"] == "Delete":
            logger.info(f"Deleting index: {index_name}")
            try:
                response = client.indices.delete(index=index_name)
                logger.info(f"Response: {response}")
            except:
                logger.info("Index already deleted or doesn't exist")
        else:
            logger.info("No action required")
            
    except Exception as e:
        logger.error(f"Exception: {str(e)}", exc_info=True)
        status = cfnresponse.FAILED
    
    finally:
        cfnresponse.send(event, context, status, response)
    
    return {
        "statusCode": 200,
        "body": json.dumps("Create index lambda completed")
    }