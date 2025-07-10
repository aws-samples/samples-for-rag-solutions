# RFI Solution

A Generative AI-powered application that automatically generates draft responses for Request for Information (RFI) and Request for Proposal (RFP) questions using Amazon Bedrock Knowledge Bases and Retrieval Augmented Generation (RAG).

## Problem Statement

Responding to RFI/RFP documents is a time and effort-intensive task that involves:
- Searching through prior submissions and reference materials
- Extracting correct answers in the right context
- Manual collation, tagging, and searching of organizational knowledge
- Risk of generating inaccurate or outdated responses
- Significant time investment that could save thousands of hours and hundreds of thousands of dollars

## Solution Overview

This solution automates the draft generation of RFI/RFP responses using Generative AI, allowing organizations to:
1. **Upload RFI/RFP documents** and automatically extract questions using foundation models
2. **Generate contextual responses** by querying prior submissions stored in Amazon Bedrock Knowledge Bases
3. **Accelerate response generation** by leveraging RAG (Retrieval Augmented Generation) to find relevant information
4. **Maintain transparency** with source attribution to minimize hallucinations

## How It Works

### Document Processing Pipeline:
1. **Question Extraction**: Foundation models extract questions from uploaded RFI/RFP documents
2. **Knowledge Base Query**: Each question is sent to Amazon Bedrock Knowledge Base for contextual responses
3. **RAG Implementation**: 
   - Prior submissions stored in Amazon S3 are converted to vector embeddings
   - Questions are matched against the vector database for relevant context
   - Foundation models generate responses augmented with retrieved context
4. **Response Generation**: Users receive draft responses with source attribution for final compilation

### Knowledge Base Architecture:
- **Data Storage**: Prior RFI/RFP submissions stored in Amazon S3
- **Vector Database**: Amazon OpenSearch Serverless for embedding storage
- **Embedding Model**: Amazon Titan for converting documents to numerical representations
- **Foundation Models**: Amazon Bedrock Claude models for question extraction and response generation

## Project Structure

```
rfi-solution/
├── cdk/                    # CDK Infrastructure code
│   ├── app.py             # CDK app entry point
│   ├── rfi_stack.py       # Main CDK stack
│   ├── cdk.json           # CDK configuration
│   └── requirements-cdk.txt
├── code/
│   ├── lambdas/           # Lambda functions
│   │   ├── create-index-lambda/     # OpenSearch index creation
│   │   └── document-processor-lambda/ # Document processing
│   └── streamlit-app/     # Streamlit application
│       ├── app.py         # Main Streamlit app
│       ├── Dockerfile     # Container configuration
│       └── requirements.txt
├── deploy-single.sh       # Single command deployment
└── README.md
```

## Architecture

### Core AI/ML Services:
- **Amazon Bedrock Knowledge Bases** - Managed RAG implementation for contextual response generation
- **Amazon Bedrock Foundation Models** - Claude models for question extraction and response generation
- **Amazon OpenSearch Serverless** - Vector database for embedding storage and similarity search
- **Amazon Titan Embeddings** - Convert documents and queries to numerical representations

### Application Infrastructure:
- **Amazon VPC** - Network isolation with public/private subnets and NAT Gateways
- **Amazon ECS Fargate** - Containerized Streamlit application in private subnets
- **Application Load Balancer** - Public access to Streamlit app
- **Amazon Cognito** - User authentication and role-based access control
- **Amazon DynamoDB** - Document metadata and processing history tracking
- **Amazon S3** - Document storage for RFI/RFP uploads and knowledge base data
- **AWS Lambda** - Document processing and API backend
- **Amazon API Gateway** - REST API for document operations

## Prerequisites

- AWS CLI configured with appropriate permissions
- Docker installed and running
- Node.js and npm (for AWS CDK)
- Python 3.8+
- AWS CDK CLI installed (`npm install -g aws-cdk`)

## Quick Start

**Single Command Deployment:**
```bash
./deploy-single.sh
```

This script will:
1. Set up Python virtual environment
2. Install CDK dependencies
3. Bootstrap CDK (if needed)
4. Build Docker image automatically
5. Deploy complete infrastructure with Knowledge Base
6. Output the application URL

## Get Application URL

After deployment:
```bash
aws cloudformation describe-stacks --stack-name RFIStack --query 'Stacks[0].Outputs[?OutputKey==`StreamlitURL`].OutputValue' --output text
```

## Configuration

### Cognito Users

Create users in the Cognito User Pool:

```bash
aws cognito-idp admin-create-user \
  --user-pool-id <USER_POOL_ID> \
  --username <USERNAME> \
  --user-attributes Name=email,Value=<EMAIL> \
  --temporary-password <TEMP_PASSWORD> \
  --message-action SUPPRESS
```

Set permanent password:
```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id <USER_POOL_ID> \
  --username <USERNAME> \
  --password <PERMANENT_PASSWORD> \
  --permanent
```

### Admin Users

To create admin users, add the custom:role attribute:

```bash
aws cognito-idp admin-update-user-attributes \
  --user-pool-id <USER_POOL_ID> \
  --username <USERNAME> \
  --user-attributes Name=custom:role,Value=admin
```

## Key Features

### AI-Powered Processing:
- **Automated Question Extraction** - Foundation models identify and extract questions from RFI/RFP documents
- **Contextual Response Generation** - RAG-based responses using organizational knowledge base
- **Source Attribution** - Transparent citations to minimize hallucinations and improve accuracy
- **Multi-Model Integration** - Claude for question extraction, Titan for embeddings, Knowledge Base for RAG

### Enterprise Features:
- **Secure Authentication** - Cognito-based user management with role-based access
- **Document Management** - Secure S3 storage with metadata tracking and processing history
- **User Roles** - Admin users see all documents, regular users see only their submissions
- **Audit Trail** - Complete tracking of document processing status and results
- **Scalable Architecture** - Containerized deployment with auto-scaling capabilities

### Knowledge Base Management:
- **Automated Ingestion** - S3-based data source with automatic vector indexing
- **Semantic Search** - Vector similarity matching for relevant context retrieval
- **Chunking Strategy** - Optimized text segmentation for better retrieval accuracy
- **Real-time Updates** - Dynamic knowledge base updates as new submissions are added

## Security

- All resources deployed in private subnets with NAT Gateway access
- S3 buckets have public access blocked
- DynamoDB tables use encryption at rest
- VPC endpoints for S3 and DynamoDB reduce costs and improve security
- Lambda functions use least-privilege IAM roles
- Cognito enforces strong password policies

## Cleanup

To remove all resources:

```bash
cdk destroy
```

## Business Impact

- **Time Savings**: Reduces RFI/RFP response time from days to hours
- **Cost Reduction**: Saves thousands of hours of manual effort and hundreds of thousands of dollars
- **Accuracy Improvement**: Leverages organizational knowledge base for consistent, accurate responses
- **Process Automation**: Eliminates manual searching and collation of prior submissions
- **Knowledge Retention**: Centralizes and makes organizational knowledge searchable and reusable

## Troubleshooting

1. **Docker Issues**: Ensure Docker is running before deployment
2. **CDK Bootstrap Issues**: Ensure your AWS credentials have sufficient permissions
3. **Region Mismatch**: The stack deploys to us-west-2 by default
4. **ECS Service Issues**: Check CloudWatch logs for container startup errors
5. **Knowledge Base Issues**: Ensure documents are uploaded to S3 and data source sync is completed

## Use Cases

- **Government Contractors**: Responding to federal RFI/RFP requirements
- **Consulting Firms**: Leveraging past proposal content for new opportunities
- **Enterprise Sales**: Accelerating RFP response processes
- **Regulatory Compliance**: Generating responses based on prior regulatory submissions
- **Knowledge Management**: Making organizational expertise searchable and reusable

## License

This project is licensed under the MIT License - see the LICENSE file for details.