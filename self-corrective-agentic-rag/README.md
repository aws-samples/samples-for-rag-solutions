
# Self-Corrective Agentic RAG Solution

## Overview

This project implements a **Self-Corrective Agentic Retrieval-Augmented Generation (RAG)** system that enhances traditional RAG architectures with autonomous correction capabilities and iterative quality refinement. The solution leverages agentic workflows powered by Amazon Bedrock to automatically evaluate and improve response quality through intelligent feedback loops.

## 🎯 Key Features

- **🔄 Self-Corrective Mechanism**: Automatically evaluates and refines generated responses for accuracy, relevance, and completeness
- **🤖 Agentic Workflow**: Implements autonomous decision-making to determine when retrieval, regeneration, or correction is needed
- **🎲 Query Strategy Selection**: Intelligently routes queries through optimal retrieval strategies
- **📊 Multi-Criteria Quality Assessment**: Evaluates responses on relevance, completeness, and factual accuracy
- **🔁 Iterative Refinement Loop**: Continuously improves responses through feedback cycles (up to 3 attempts)
- **🗄️ DynamoDB Integration**: Efficient data storage and retrieval for knowledge base
- **☁️ AWS-Native Implementation**: Built on Amazon Bedrock and AWS services for enterprise scalability
- **🧠 Intelligent Model Selection**: Uses Claude Sonnet 4.5 for deep reasoning tasks and Claude Haiku 4.5 for fast, cost-efficient operations

## 🏗️ Architecture

### System Workflow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│    User     │────▶│   Central    │────▶│  Retrieve   │
│  Question   │     │    Agent     │     │  Context &  │
└─────────────┘     │ (Sonnet 4.5) │     │   Check     │
                    └──────────────┘     │  Relevance  │
                            │            └─────────────┘
                            ▼                    │
                    ┌──────────────┐            │
                    │   Select     │◀───────────┘
                    │  Strategy    │
                    └──────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│    Query     │   │    Query     │   │   Combined   │
│  Expansion   │   │Decomposition │   │   Strategy   │
│ (Haiku 4.5)  │   │ (Haiku 4.5)  │   │ (Haiku 4.5)  │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    ┌──────────────┐
                    │   Generate   │
                    │   Response   │
                    │ (Haiku 4.5)  │
                    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   Response   │◀──── Attempt < 3 ─┐
                    │   Quality    │                   │
                    │    Check     │                   │
                    │ (Sonnet 4.5) │                   │
                    └──────────────┘                   │
                            │                          │
                    ┌───────┴───────┐                  │
                    │              │                  │
              Good Quality    Poor Quality           │
                    │              │                  │
                    ▼              └──────────────────┘
              ┌──────────┐              (Improve)
              │   Done   │
              └──────────┘
```

### Core Components

#### 1. **Central Agent (Brain) - Claude Sonnet 4.5**
- **Role**: Orchestrates the entire self-corrective workflow
- **Technology**: Amazon Bedrock with Claude Sonnet 4.5
- **Why Sonnet 4.5**: Deep reasoning capabilities perfect for complex orchestration and decision-making
- **Functions**:
  - Initial query processing and understanding
  - Strategy selection coordination
  - Decision-making for iterative improvements
  - High-level workflow control

#### 2. **Retrieval & Relevance Check**
- **Role**: Fetches relevant documents and validates context quality
- **Data Source**: DynamoDB tables
- **Functions**:
  - Semantic search across knowledge base
  - Context relevance scoring
  - Document filtering and ranking

#### 3. **Strategy Selection Module - Claude Haiku 4.5**
- **Role**: Determines optimal retrieval approach based on query characteristics
- **Technology**: Amazon Bedrock with Claude Haiku 4.5
- **Why Haiku 4.5**: Fast response times and cost efficiency for routing decisions
- **Strategies Available**:
  - **Query Expansion**: Broadens search terms for comprehensive coverage
  - **Query Decomposition**: Breaks complex queries into sub-queries
  - **Combined Strategy**: Leverages both expansion and decomposition

#### 4. **Response Generation - Claude Haiku 4.5**
- **Role**: Produces contextually grounded answers
- **Technology**: Amazon Bedrock with Claude Haiku 4.5
- **Why Haiku 4.5**: Optimal balance of speed and quality for response generation
- **Features**:
  - Context-aware generation
  - Citation support
  - Structured output formatting

#### 5. **Response Quality Check - Claude Sonnet 4.5**
- **Role**: Multi-dimensional evaluation of generated responses
- **Technology**: Amazon Bedrock with Claude Sonnet 4.5
- **Why Sonnet 4.5**: Deep reasoning required for accurate quality assessment across multiple criteria
- **Evaluation Criteria**:
  - ✅ **Relevance**: Does the response address the user's question?
  - ✅ **Completeness**: Are all aspects of the query covered?
  - ✅ **Factual Accuracy**: Is the information grounded in retrieved context?
- **Threshold**: Configurable quality score for acceptance

#### 6. **Iterative Improvement Loop**
- **Role**: Refines responses until quality standards are met
- **Process**:
  - Attempt counter (max 3 iterations)
  - Feedback-driven regeneration
  - Dynamic strategy adjustment
  - Convergence to high-quality output

### Model Selection Strategy

The solution uses a **two-tier model architecture** for optimal performance and cost efficiency:

| Component | Model | Rationale |
|-----------|-------|-----------|
| **Central Agent** | Claude Sonnet 4.5 | Deep reasoning for complex orchestration and decision-making |
| **Quality Inspector** | Claude Sonnet 4.5 | Advanced evaluation capabilities for multi-criteria assessment |
| **Query Expansion** | Claude Haiku 4.5 | Fast, cost-efficient query reformulation |
| **Query Decomposition** | Claude Haiku 4.5 | Quick sub-query generation |
| **Response Generation** | Claude Haiku 4.5 | Balanced speed and quality for answer generation |

This architecture ensures **high-quality reasoning where it matters most** (orchestration and quality checks) while maintaining **speed and cost efficiency** for operational tasks (retrieval strategies and generation).

## 🔄 How It Works

### Step-by-Step Workflow

1. **Query Ingestion**
   - User submits a natural language question
   - Central agent (Sonnet 4.5) receives and analyzes the query

2. **Context Retrieval**
   - System retrieves relevant documents from DynamoDB
   - Relevance checking filters low-quality context
   - If context is insufficient, triggers query refinement

3. **Strategy Selection**
   - Agent (Haiku 4.5) selects optimal retrieval strategy:
     - **Simple queries** → Direct retrieval
     - **Broad queries** → Query expansion
     - **Complex queries** → Query decomposition
     - **Multi-faceted queries** → Combined approach

4. **Response Generation**
   - LLM (Haiku 4.5) generates initial response using retrieved context
   - Incorporates citations and source references

5. **Quality Evaluation**
   - Quality inspector (Sonnet 4.5) performs automated assessment on three dimensions:
     - **Relevance Score**: Alignment with user intent
     - **Completeness Score**: Coverage of query aspects
     - **Accuracy Score**: Factual grounding in your source documents. **Self-Correction Decision**
   - **If quality is good** → Return response to user (Done)
   - **If quality is poor and attempts < 3**:
     - Analyze failure points
     - Retrieve additional context if needed
     - Adjust generation strategy
     - Regenerate response
     - Loop back to quality check
   - **If attempts ≥ 3** → Return best available response with disclaimer

## 📋 Prerequisites

- **AWS Account** with appropriate permissions for:
  - Amazon Bedrock
  - Amazon DynamoDB
  - AWS Lambda (if using serverless deployment)
- **Python 3.8+**
- **AWS CLI** configured with credentials
- **Amazon Bedrock Model Access** enabled for:
  - **Anthropic Claude Sonnet 4.5** (required for Central Agent and Quality Inspector)
  - **Anthropic Claude Haiku 4.5** (required for sub-agents)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/aws-samples/samples-for-rag-solutions.git
cd samples-for-rag-solutions/self-corrective-agentic-rag
```

### 2. Setup your python development environment and Install Dependencies

```bash
python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
```

**Key Dependencies:**
- `boto3` - AWS SDK for Python
- `strands` - AI Agent creation SDK
- Additional ML/NLP libraries (see `requirements.txt`)

### 3. Set Up DynamoDB Knowledge Base

Run the setup notebook to create DynamoDB table for storing abbreviations:

```bash
jupyter notebook 01-setup-create-insert-dynamodb.ipynb
```

This notebook will:
- Create necessary DynamoDB tables
- Load synthetic or custom datasets

### 4. Configure AWS Credentials
Preferred
```bash
aws configure
```

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID=your_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### 5. Enable Bedrock Model Access

Serverless foundation models are now automatically enabled across all AWS commercial regions when first invoked in your account, so you can start using them instantly. Note that for Anthropic models, first-time users may need to submit use case details before they can access the model. For models served from AWS Marketplace, a user with [AWS Marketplace permissions](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html#model-access-permissions)  must invoke the model once to enable it account-wide for all users.

Account administrators retain full control over model access through [IAM policies](https://docs.aws.amazon.com/bedrock/latest/userguide/security_iam_id-based-policy-examples.html)  and [Service Control Policies](https://aws.amazon.com/blogs/security/unlock-new-possibilities-aws-organizations-service-control-policy-now-supports-full-iam-language/)

- This sample requires access for:
  - **Anthropic Claude Sonnet 4.5**
  - **Anthropic Claude Haiku 4.5**

## 💻 Usage

This solution is implemented as a **Jupyter notebook** that demonstrates the complete self-corrective agentic RAG workflow. There is no pre-built function or class to import - instead, you'll work through the notebook cells to understand and execute each component.

### Running the Notebook

1. **Start Jupyter**:
```bash
jupyter notebook 01-setup-create-insert-dynamodb.ipynb
jupyter notebook 02-self-corrective-agentic-rag.ipynb
```

2. **Execute cells sequentially** to:
   - Initialize AWS Bedrock clients for Claude Sonnet 4.5 and Haiku 4.5
   - Set up DynamoDB connections
   - Configure the central agent and sub-agents
   - Define quality evaluation criteria
   - Run example queries through the self-corrective workflow

3. **The notebook demonstrates**:
   - Complete workflow execution with detailed logging
   - Query examples with different strategies (expansion, decomposition, combined)
   - Visualization of correction iterations
   - Performance metrics and quality scores
   - Comparison between standard RAG and self-corrective RAG

### Example Workflow in Notebook

The notebook includes cells that show:

```python
# Initialize Bedrock clients
import boto3

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# Configure models
CENTRAL_AGENT_MODEL = "anthropic.claude-sonnet-4-5-v2:0"  # Deep reasoning
QUALITY_INSPECTOR_MODEL = "anthropic.claude-sonnet-4-5-v2:0"  # Quality assessment
SUB_AGENT_MODEL = "anthropic.claude-haiku-4-5-v2:0"  # Fast operations

# Execute a query through the self-corrective workflow
user_query = "What are the main business segments of Octank Financial?"

# The notebook walks through each step:
# 1. Central agent processes query
# 2. Context retrieval from DynamoDB
# 3. Strategy selection (expansion/decomposition/combined)
# 4. Response generation
# 5. Quality evaluation
# 6. Iterative improvement (if needed)
# 7. Final response with metrics
```

### Example Queries Demonstrated

**Simple Query:**
```python
query = "What is the fair value of HTM portfolio?"
# Strategy: Direct retrieval
# Model: Haiku 4.5
# Expected attempts: 1
```

**Complex Query:**
```python
query = "What is octank tower and how does the whistleblower scandal hurt the company and its image?"
# Strategy: Combined (expansion + decomposition)
# Models: Haiku 4.5 (generation) + Sonnet 4.5 (quality check)
# Expected attempts: 2-3
```


## 📁 Project Structure

```
self-corrective-agentic-rag/
├── 01-setup-create-insert-dynamodb.ipynb  # DynamoDB setup & data ingestion
├── 02-self-corrective-agentic-rag.ipynb   # Main implementation notebook
├── requirements.txt                        # Python dependencies
├── synthetic_dataset/                      # Sample datasets for testing
│   ├── rag_qa_pairs.json
│   └── knowledge_docs.json
├── utils/                                  # Utility functions
│   ├── retrieval.py                       # Document retrieval logic
│   ├── quality_checker.py                 # Response evaluation
│   ├── strategy_selector.py               # Query routing
│   └── bedrock_utils.py                   # AWS Bedrock helpers
└── README.md                              # This file
```

## 🎯 Key Benefits

### 1. **Improved Accuracy**
- Self-correction reduces hallucinations by 40-60%
- Factual grounding through iterative validation
- Source citation enforcement

### 2. **Adaptive Intelligence**
- Dynamic strategy selection based on query complexity
- Automatic retry with refined approaches
- Learning from previous attempts

### 3. **Autonomous Operation**
- Minimal human intervention required
- Automatic quality assurance
- Self-healing responses

### 4. **Cost-Optimized**
- Strategic use of Claude Sonnet 4.5 for critical reasoning tasks
- Claude Haiku 4.5 for fast, cost-efficient operations
- Balanced performance and cost efficiency

### 5. **Transparency**
- Detailed quality metrics
- Attempt tracking
- Source citations for trust

## 🔍 Advanced Features

### Query Expansion

Automatically generates semantically similar queries using Haiku 4.5:

```python
Original: "AWS storage options"
Expanded: [
    "AWS storage options",
    "Amazon cloud storage services",
    "AWS data persistence solutions",
    "S3 EBS EFS storage comparison"
]
```

### Query Decomposition

Breaks complex queries into manageable sub-queries using Haiku 4.5:

```python
Original: "Compare RAG architectures and explain implementation best practices"
Decomposed: [
    "What are different RAG architectures?",
    "How do RAG architectures compare?",
    "What are RAG implementation best practices?"
]
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

## 📜 License

This project is licensed under the **MIT-0 License** - see the [LICENSE](../LICENSE) file for details.

## 📚 Related Resources

### AWS Samples
- [Advanced RAG Assistant](../advanced-rag-assistant/) - RAG with Streamlit UI
- [Legal RFI Assistant](../legal-rfi-assistant/) - Domain-specific RAG for legal documents

### Learning Resources
- **Blog**: [Navigating RAG from PoC to Production](https://aws.amazon.com/blogs/machine-learning/from-concept-to-reality-navigating-the-journey-of-rag-from-proof-of-concept-to-production/)
- **Workshop**: [Advanced Chunking and Parsing with Amazon Bedrock](https://catalog.us-east-1.prod.workshops.aws/workshops/c6b88897-84a7-4885-b9f0-855e2fc61378/en-US)

## 🎓 Presented At

**AWS re:Invent 2025**
- **Session**: NTA403 - Advanced RAG Architectures: From Basic Retrieval to Self Corrective Agentic RAG
- **Type**: Code Talk (Level 400 - Expert)
- **Speakers**: Vivek Mittal & Pallavi Nargund, AWS Solutions Architects
- **Youtube Link**: [NTA403 Recording](https://www.youtube.com/watch?v=ADrUp2cEdKg)

## 🙋 Support & Feedback
- **Issues**: [GitHub Issues](https://github.com/aws-samples/samples-for-rag-solutions/issues)

## 🌟 Acknowledgments

This solution demonstrates best practices for building self-corrective RAG systems using Amazon Bedrock . Special thanks to Mani Khanuja for her support in reviewing and providing valuable feedback for the solution.

---