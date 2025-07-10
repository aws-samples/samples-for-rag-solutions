"""
Lambda function for document processing
"""
import json
import os
import boto3
import uuid
from datetime import datetime
from typing import Dict, Any

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
bedrock_client = boto3.client('bedrock-runtime')

# Environment variables
DOCUMENTS_TABLE = os.environ['DOCUMENTS_TABLE']
DOCUMENT_BUCKET = os.environ['DOCUMENT_BUCKET']
REGION = os.environ['REGION']

table = dynamodb.Table(DOCUMENTS_TABLE)


def handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda handler for document processing requests
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        if http_method == 'POST' and 'process' in path:
            return process_document(event)
        elif http_method == 'POST' and 'documents' in path:
            return upload_document(event)
        elif http_method == 'GET' and 'documents' in path:
            return get_documents(event)
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }


def upload_document(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle document upload
    """
    try:
        body = json.loads(event.get('body', '{}'))
        file_name = body.get('fileName')
        file_content = body.get('fileContent')  # Base64 encoded
        username = body.get('username', 'anonymous')
        
        if not file_name or not file_content:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'fileName and fileContent are required'})
            }
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        s3_key = f"documents/{document_id}/{file_name}"
        
        # Upload to S3
        import base64
        file_bytes = base64.b64decode(file_content)
        s3_client.put_object(
            Bucket=DOCUMENT_BUCKET,
            Key=s3_key,
            Body=file_bytes,
            ContentType='application/octet-stream'
        )
        
        s3_url = f"s3://{DOCUMENT_BUCKET}/{s3_key}"
        
        # Update DynamoDB
        timestamp = datetime.now().isoformat()
        table.put_item(
            Item={
                'document_id': document_id,
                'file_name': file_name,
                's3_url': s3_url,
                'status': 'uploaded',
                'timestamp': timestamp,
                'username': username
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'document_id': document_id,
                's3_url': s3_url,
                'status': 'uploaded'
            })
        }
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }


def process_document(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle document processing with Bedrock
    """
    try:
        body = json.loads(event.get('body', '{}'))
        document_id = body.get('document_id')
        
        if not document_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'document_id is required'})
            }
        
        # Get document from DynamoDB
        response = table.get_item(Key={'document_id': document_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Document not found'})
            }
        
        document = response['Item']
        
        # Update status to processing
        table.update_item(
            Key={'document_id': document_id},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'processing'}
        )
        
        # Here you would implement the actual document processing logic
        # For now, we'll simulate processing
        
        # Update status to completed
        table.update_item(
            Key={'document_id': document_id},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'completed'}
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'document_id': document_id,
                'status': 'completed',
                'message': 'Document processed successfully'
            })
        }
        
    except Exception as e:
        print(f"Processing error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }


def get_documents(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get document history
    """
    try:
        query_params = event.get('queryStringParameters') or {}
        username = query_params.get('username')
        
        if username:
            # Filter by username using GSI
            response = table.query(
                IndexName='username-index',
                KeyConditionExpression='username = :username',
                ExpressionAttributeValues={':username': username},
                ScanIndexForward=False  # Sort by timestamp descending
            )
            items = response.get('Items', [])
        else:
            # Scan all documents
            response = table.scan()
            items = response.get('Items', [])
            # Sort by timestamp descending
            items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'documents': items
            })
        }
        
    except Exception as e:
        print(f"Get documents error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }