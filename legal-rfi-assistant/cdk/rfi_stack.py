"""
CDK Stack for RFI Solution Infrastructure
"""
import os
import json
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CustomResource,
    custom_resources as cr,
    CfnResource,
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_logs as logs,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_elasticloadbalancingv2 as elbv2,
    aws_ecr_assets as ecr_assets,
    aws_bedrock as bedrock,
    aws_opensearchserverless as opensearchserverless,
    BundlingOptions,
    DockerImage,
    CfnOutput
)
from constructs import Construct


class RFIStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC with public and private subnets
        # PRIVATE_WITH_EGRESS automatically creates NAT Gateways for outbound internet access
        self.vpc = ec2.Vpc(
            self, "RFIVPC",
            max_azs=2,
            nat_gateways=2,  # One NAT Gateway per AZ for high availability
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="PrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )

        # VPC Endpoints for cost optimization (optional but recommended)
        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3
        )
        
        self.vpc.add_gateway_endpoint(
            "DynamoDBEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB
        )

        # S3 Bucket for document storage
        self.document_bucket = s3.Bucket(
            self, "DocumentBucket",
            bucket_name=f"rfi-documents-{self.account}-{self.region}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # OpenSearch Serverless Collection for Knowledge Base
        self.opensearch_collection = opensearchserverless.CfnCollection(
            self, "KnowledgeBaseCollection",
            name=f"rfi-kb-collection-{self.account}",
            type="VECTORSEARCH",
            description="OpenSearch Serverless collection for RFI Knowledge Base"
        )
        
        collection_name = self.opensearch_collection.name
        
        # Security policies using CfnResource (matching reference implementation)
        encryption_policy = CfnResource(
            self, "EncryptionPolicy",
            type="AWS::OpenSearchServerless::SecurityPolicy",
            properties={
                "Name": "rfi-kb-encryption-policy",
                "Type": "encryption",
                "Description": "Encryption policy for RFI Knowledge Base collection",
                "Policy": json.dumps({
                    "Rules": [{
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name}"]
                    }],
                    "AWSOwnedKey": True
                })
            }
        )
        
        network_policy = CfnResource(
            self, "NetworkPolicy",
            type="AWS::OpenSearchServerless::SecurityPolicy",
            properties={
                "Name": "rfi-kb-network-policy",
                "Type": "network",
                "Description": "Network policy for RFI Knowledge Base collection",
                "Policy": json.dumps([{
                    "Rules": [
                        {
                            "ResourceType": "collection",
                            "Resource": [f"collection/{collection_name}"]
                        },
                        {
                            "ResourceType": "dashboard",
                            "Resource": [f"collection/{collection_name}"]
                        }
                    ],
                    "AllowFromPublic": True
                }])
            }
        )
        
        # Collection depends on policies
        self.opensearch_collection.add_dependency(encryption_policy)
        self.opensearch_collection.add_dependency(network_policy)

        # IAM Role for Bedrock Knowledge Base
        self.kb_role = iam.Role(
            self, "KnowledgeBaseRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
            ]
        )

        # Data access policy will be created in the Knowledge Base section
        
        # Grant permissions for OpenSearch Serverless
        self.kb_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "aoss:APIAccessAll"
                ],
                resources=[self.opensearch_collection.attr_arn]
            )
        )

        # Grant S3 permissions for Knowledge Base
        self.document_bucket.grant_read(self.kb_role)

        # Create opensearch layer
        opensearch_layer = lambda_.LayerVersion(
            self, "OpensearchLayer",
            code=lambda_.Code.from_asset(
                "../code/layers/opensearch_layer",
                bundling=BundlingOptions(
                    image=DockerImage.from_registry("public.ecr.aws/sam/build-python3.11"),
                    command=[
                        "bash", "-c",
                        "mkdir -p /asset-output/python/lib/python3.11/site-packages && "
                        "pip install --platform manylinux2014_x86_64 --implementation cp --python-version 3.11 --only-binary=:all: --target /asset-output/python/lib/python3.11/site-packages -r requirements.txt"
                    ]
                )
            ),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="OpenSearch layer for Lambda"
        )
        
        # Create index Lambda role
        create_index_lambda_role = iam.Role(
            self, "CreateIndexLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        create_index_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["aoss:APIAccessAll"],
                resources=[self.opensearch_collection.attr_arn]
            )
        )
        
        # Data Access Policy using CfnResource
        data_access_policy = CfnResource(
            self, "DataAccessPolicy",
            type="AWS::OpenSearchServerless::AccessPolicy",
            properties={
                "Name": "rfi-kb-data-access-policy",
                "Type": "data",
                "Description": "Data access policy for RFI Knowledge Base",
                "Policy": json.dumps([{
                    "Description": "Access for Bedrock Knowledge Base",
                    "Rules": [
                        {
                            "ResourceType": "index",
                            "Resource": ["index/*/*"],
                            "Permission": ["aoss:*"]
                        },
                        {
                            "ResourceType": "collection",
                            "Resource": [f"collection/{collection_name}"],
                            "Permission": ["aoss:*"]
                        }
                    ],
                    "Principal": [
                        self.kb_role.role_arn,
                        create_index_lambda_role.role_arn
                    ]
                }])
            }
        )
        
        # Create index Lambda
        create_index_lambda = lambda_.Function(
            self, "CreateIndexLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset("../code/lambdas/create-index-lambda"),
            layers=[opensearch_layer],
            timeout=Duration.minutes(15),
            role=create_index_lambda_role,
            environment={
                "REGION_NAME": self.region,
                "COLLECTION_HOST": self.opensearch_collection.attr_collection_endpoint,
                "VECTOR_INDEX_NAME": "bedrock-knowledgebase-index",
                "VECTOR_FIELD_NAME": "bedrock-knowledge-base-default-vector"
            }
        )
        
        # Custom resource provider
        index_provider = cr.Provider(
            self, "IndexProvider",
            on_event_handler=create_index_lambda
        )
        
        # Custom resource
        index_resource = CustomResource(
            self, "IndexResource",
            service_token=index_provider.service_token,
            properties={
                "CollectionEndpoint": self.opensearch_collection.attr_collection_endpoint,
                "IndexName": "bedrock-knowledgebase-index",
                "Region": self.region
            }
        )
        
        # Dependencies
        index_resource.node.add_dependency(self.opensearch_collection)
        index_resource.node.add_dependency(data_access_policy)
        
        # Bedrock Knowledge Base
        self.knowledge_base = bedrock.CfnKnowledgeBase(
            self, "RFIKnowledgeBase",
            name="rfi-knowledge-base",
            description="Knowledge base for RFI document processing",
            role_arn=self.kb_role.role_arn,
            knowledge_base_configuration={
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"
                }
            },
            storage_configuration={
                "type": "OPENSEARCH_SERVERLESS",
                "opensearchServerlessConfiguration": {
                    "collectionArn": self.opensearch_collection.attr_arn,
                    "vectorIndexName": "bedrock-knowledgebase-index",
                    "fieldMapping": {
                        "vectorField": "bedrock-knowledge-base-default-vector",
                        "textField": "AMAZON_BEDROCK_TEXT_CHUNK",
                        "metadataField": "AMAZON_BEDROCK_METADATA"
                    }
                }
            }
        )
        
        # Knowledge Base depends on index being created
        self.knowledge_base.node.add_dependency(index_resource)

        # Data Source for Knowledge Base
        self.data_source = bedrock.CfnDataSource(
            self, "RFIDataSource",
            name="rfi-data-source",
            description="S3 data source for RFI documents",
            knowledge_base_id=self.knowledge_base.attr_knowledge_base_id,
            data_source_configuration={
                "type": "S3",
                "s3Configuration": {
                    "bucketArn": self.document_bucket.bucket_arn
                }
            },
            vector_ingestion_configuration={
                "chunkingConfiguration": {
                    "chunkingStrategy": "FIXED_SIZE",
                    "fixedSizeChunkingConfiguration": {
                        "maxTokens": 1000,
                        "overlapPercentage": 20
                    }
                }
            }
        )

        # DynamoDB table for document tracking
        self.documents_table = dynamodb.Table(
            self, "DocumentsTable",
            table_name="rfi-document-processor",
            partition_key=dynamodb.Attribute(
                name="document_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        # Add GSI for username queries
        self.documents_table.add_global_secondary_index(
            index_name="username-index",
            partition_key=dynamodb.Attribute(
                name="username",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Cognito User Pool
        self.user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name="rfi-user-pool",
            sign_in_aliases=cognito.SignInAliases(username=True, email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.DESTROY,
            custom_attributes={
                "role": cognito.StringAttribute(min_len=1, max_len=50, mutable=True)
            }
        )

        # Cognito User Pool Client
        self.user_pool_client = cognito.UserPoolClient(
            self, "UserPoolClient",
            user_pool=self.user_pool,
            user_pool_client_name="rfi-app-client",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            ),
            generate_secret=False
        )

        # Lambda execution role
        lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        # Add permissions for AWS services
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:Retrieve",
                    "bedrock:RetrieveAndGenerate"
                ],
                resources=["*"]
            )
        )

        # Grant DynamoDB permissions
        self.documents_table.grant_read_write_data(lambda_role)

        # Grant S3 permissions
        self.document_bucket.grant_read_write(lambda_role)

        # Document processing Lambda function
        self.document_processor = lambda_.Function(
            self, "DocumentProcessor",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="document_processor.handler",
            code=lambda_.Code.from_asset("../code/lambdas/document-processor-lambda"),
            timeout=Duration.minutes(15),
            memory_size=1024,
            role=lambda_role,
            environment={
                "DOCUMENTS_TABLE": self.documents_table.table_name,
                "DOCUMENT_BUCKET": self.document_bucket.bucket_name,
                "REGION": self.region,
                "KNOWLEDGE_BASE_ID": self.knowledge_base.attr_knowledge_base_id
            },
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        # API Gateway
        self.api = apigateway.RestApi(
            self, "RFIAPI",
            rest_api_name="rfi-api",
            description="API for RFI document processing",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # API Gateway Lambda integration
        lambda_integration = apigateway.LambdaIntegration(
            self.document_processor,
            request_templates={"application/json": '{"statusCode": "200"}'}
        )

        # API resources
        documents_resource = self.api.root.add_resource("documents")
        documents_resource.add_method("POST", lambda_integration)
        documents_resource.add_method("GET", lambda_integration)

        process_resource = self.api.root.add_resource("process")
        process_resource.add_method("POST", lambda_integration)

        # ECR Repository for Streamlit app
        self.ecr_repo = ecr.Repository(
            self, "StreamlitRepo",
            repository_name="rfi-streamlit-app",
            removal_policy=RemovalPolicy.DESTROY
        )

        # ECS Cluster
        self.ecs_cluster = ecs.Cluster(
            self, "RFICluster",
            vpc=self.vpc,
            cluster_name="rfi-cluster"
        )

        # ECS Task Role
        task_role = iam.Role(
            self, "StreamlitTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )

        # Grant permissions to AWS services
        self.documents_table.grant_read_write_data(task_role)
        self.document_bucket.grant_read_write(task_role)
        task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:Retrieve",
                    "bedrock:RetrieveAndGenerate",
                    "cognito-idp:*",
                    "textract:*"
                ],
                resources=["*"]
            )
        )

        # ECS Task Definition
        task_definition = ecs.FargateTaskDefinition(
            self, "StreamlitTaskDef",
            memory_limit_mib=2048,
            cpu=1024,
            task_role=task_role,
            execution_role=task_role,
            runtime_platform=ecs.RuntimePlatform(
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=ecs.CpuArchitecture.X86_64
            )
        )

        # Container Definition - Build Docker image from local directory
        container = task_definition.add_container(
            "StreamlitContainer",
            image=ecs.ContainerImage.from_asset(
                "../code/streamlit-app",
                platform=ecr_assets.Platform.LINUX_AMD64
            ),
            memory_limit_mib=2048,
            environment={
                "API_URI": self.api.url,
                "COGNITO_REGION": self.region,
                "COGNITO_USER_POOL_ID": self.user_pool.user_pool_id,
                "COGNITO_APP_CLIENT_ID": self.user_pool_client.user_pool_client_id,
                "KNOWLEDGE_BASE_ID": self.knowledge_base.attr_knowledge_base_id,
                "DOCUMENT_BUCKET": self.document_bucket.bucket_name
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="streamlit",
                log_retention=logs.RetentionDays.ONE_WEEK
            )
        )

        container.add_port_mappings(
            ecs.PortMapping(container_port=8501, protocol=ecs.Protocol.TCP)
        )

        # Application Load Balancer
        self.alb = elbv2.ApplicationLoadBalancer(
            self, "StreamlitALB",
            vpc=self.vpc,
            internet_facing=True,
            load_balancer_name="rfi-streamlit-alb"
        )

        # Target Group
        target_group = elbv2.ApplicationTargetGroup(
            self, "StreamlitTargetGroup",
            port=8501,
            protocol=elbv2.ApplicationProtocol.HTTP,
            vpc=self.vpc,
            target_type=elbv2.TargetType.IP,
            health_check=elbv2.HealthCheck(
                path="/_stcore/health",
                healthy_http_codes="200"
            )
        )

        # ALB Listener
        self.alb.add_listener(
            "StreamlitListener",
            port=80,
            default_target_groups=[target_group]
        )

        # ECS Service
        self.ecs_service = ecs.FargateService(
            self, "StreamlitService",
            cluster=self.ecs_cluster,
            task_definition=task_definition,
            desired_count=1,
            assign_public_ip=False,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            service_name="rfi-streamlit-service"
        )

        # Attach service to target group
        self.ecs_service.attach_to_application_target_group(target_group)

        # CloudFormation Outputs
        CfnOutput(
            self, "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID"
        )

        CfnOutput(
            self, "UserPoolClientId",
            value=self.user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID"
        )

        CfnOutput(
            self, "DocumentsTableName",
            value=self.documents_table.table_name,
            description="DynamoDB Documents Table Name"
        )

        CfnOutput(
            self, "DocumentBucketName",
            value=self.document_bucket.bucket_name,
            description="S3 Document Bucket Name"
        )

        CfnOutput(
            self, "APIEndpoint",
            value=self.api.url,
            description="API Gateway Endpoint URL"
        )

        CfnOutput(
            self, "Region",
            value=self.region,
            description="AWS Region"
        )

        CfnOutput(
            self, "ECRRepositoryURI",
            value=self.ecr_repo.repository_uri,
            description="ECR Repository URI"
        )

        CfnOutput(
            self, "LoadBalancerDNS",
            value=self.alb.load_balancer_dns_name,
            description="Application Load Balancer DNS Name"
        )

        CfnOutput(
            self, "StreamlitURL",
            value=f"http://{self.alb.load_balancer_dns_name}",
            description="Streamlit Application URL"
        )

        CfnOutput(
            self, "KnowledgeBaseId",
            value=self.knowledge_base.attr_knowledge_base_id,
            description="Bedrock Knowledge Base ID"
        )

        CfnOutput(
            self, "DataSourceId",
            value=self.data_source.attr_data_source_id,
            description="Bedrock Data Source ID"
        )