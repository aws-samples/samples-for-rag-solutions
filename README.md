# Samples for RAG Solutions

This repository is a repository of RAG(Retrieval Augmented Generation) based GenAI solutions to help solve real world use cases.

## Contents

- [Advanced RAG Assistant](advanced-rag-assistant) - Ideal for research use cases requiring advanced processing of complex graphs, images, and tables from documents. This solution utilizes advanced Retrieval Augmented Generation (RAG) features of [Amazon Bedrock Knowledge Bases](https://aws.amazon.com/bedrock/knowledge-bases/).

- [Advanced RAG Assistant with Hosted Streamlit App](advanced-rag-assistant-with-hosted-streamlit-app) - An enhancement to the Advanced RAG Assistant that includes a hosted Streamlit application on AWS with infrastructure as code for easy deployment to your AWS environment.

- [Legal RFI Solution](legal-rfi-assistant) - A Generative AI-powered application that automatically generates draft responses for Request for Information (RFI) and Request for Proposal (RFP) questions using Amazon Bedrock Knowledge Bases and RAG.

## Getting Started

To get started with the code examples, ensure you have access to [Amazon Bedrock](https://aws.amazon.com/bedrock/). Then clone this repo and navigate to one of the folders above. Detailed instructions are provided in each folder's README.

### Enable AWS IAM permissions for Bedrock

Your user or role must have sufficient [AWS IAM permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html) to call the Amazon Bedrock service.

To grant Bedrock access to your identity, you can:

- Open the [AWS IAM Console](https://us-east-1.console.aws.amazon.com/iam/home?#)
- Find your [Role](https://us-east-1.console.aws.amazon.com/iamv2/home?#/roles) (if using SageMaker or otherwise assuming an IAM Role), or else [User](https://us-east-1.console.aws.amazon.com/iamv2/home?#/users)
- Select *Add Permissions > Create Inline Policy* to attach new inline permissions, open the *JSON* editor and paste in the below example policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "BedrockFullAccess",
            "Effect": "Allow",
            "Action": ["bedrock:*"],
            "Resource": "*"
        }
    ]
}
```

For more information on the fine-grained action and resource permissions in Bedrock, check out the Bedrock Developer Guide.

## Contributing

We welcome community contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
