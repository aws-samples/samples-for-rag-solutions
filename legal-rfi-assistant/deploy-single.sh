#!/bin/bash

# Single script deployment using CDK's built-in Docker building

set -e

echo "🚀 Starting RFI Solution deployment with CDK Docker building..."

# Check prerequisites
if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK is not installed. Please install it first:"
    echo "npm install -g aws-cdk"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Create Python virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install CDK dependencies
echo "📥 Installing CDK dependencies..."
pip install -r cdk/requirements-cdk.txt

# Change to CDK directory
cd cdk

# Bootstrap CDK
echo "🏗️  Bootstrapping CDK..."
cdk bootstrap

# Deploy the stack - CDK will automatically build and push Docker image
echo "🚀 Deploying RFI Stack (CDK will build Docker image automatically)..."
cdk deploy --require-approval never

echo "✅ Deployment completed successfully!"
echo ""
echo "🔍 To get the application URL:"
echo "aws cloudformation describe-stacks --stack-name RFIStack --query 'Stacks[0].Outputs[?OutputKey==\`StreamlitURL\`].OutputValue' --output text"