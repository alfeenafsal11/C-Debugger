```markdown
# A1_Submission

## Description

A1_Submission is a comprehensive code analysis and evaluation system designed to automate the assessment of academic coding assignments. It integrates advanced language models, semantic similarity techniques, and static code analysis to provide detailed feedback, detect bugs, and evaluate submission correctness. The system processes student submissions in various formats, compares them against expected outputs, and offers explanations for identified issues.

## Key Features

- **Code Parsing Agent**: Extracts and parses code from multiple input formats such as PDFs and text files.
- **MCP Retrieval Agent**: Retrieves relevant contextual information from a knowledge base using semantic search.
- **Static Bug Detection**: Identifies common programming errors without executing the code.
- **LLM Explanation Agent**: Generates human-readable explanations for detected issues or suggestions for improvement.
- **Accuracy Calculation**: Compares student outputs with expected results to compute performance metrics.
- **Vector Storage & Embedding Model**: Leverages pre-trained Sentence Transformers for semantic understanding and retrieval.

## Technologies Used

- **Python** – Core programming language for all modules.
- **LangChain / LLMs** – For natural language processing and explanation generation.
- **Sentence Transformers** – Pre-trained model for embedding extraction (specifically `bge-base-en-v1.5`).
- **MCP (Model Communication Protocol)** – Enables interaction with external services and agents.
- **PyPDF2 / pdfplumber** – For parsing PDF-based code submissions.
- **FastAPI / Flask** – Web server framework for exposing APIs.
- **ChromaDB / FAISS** – Vector stores used for semantic search and retrieval.
- **pytest** – Testing framework for unit testing each component.

## How to Run/Install

### Prerequisites

Ensure you have Python 3.8 or higher installed on your system.

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd A1_Submission
   ```

2. **Create Virtual Environment (Recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download Embedding Model (if not present)**
   The embedding model (`bge-base-en-v1.5`) is included in the repository under `server/embedding_model`. If missing, it will be downloaded automatically during runtime if HuggingFace is accessible.

5. **Run Tests (Optional but Recommended)**
   ```bash
   python -m pytest Code/
   ```

6. **Start the MCP Server (If Required)**
   ```bash
   python server/mcp_server.py
   ```

7. **Execute Pipeline**
   To run the full pipeline:
   ```bash
   python Code/pipeline.py
   ```

### Sample Input Files

- `samples.csv`: Contains sample student submissions for testing purposes.
- `output.csv`: Output file where results are written after processing.

### Directory Structure Overview

```
.
├── output.csv
├── README.md
├── requirements.txt
├── samples.csv
├── Code/
│   ├── Academic_Transcript.pdf
│   ├── calculate_accuracy.py
│   ├── code_parsing_agent.py
│   ├── config.py
│   ├── llm_explanation_agent.py
│   ├── mcp_retrieval_agent.py
│   ├── pipeline.py
│   ├── static_bug_detector.py
│   ├── test_code_parsing_agent.py
│   ├── test_mcp_connection.py
│   ├── test_mcp_retrieval_agent.py
│   └── test_static_bug_detector.py
└── server/
    ├── mcp_server.py
    └── embedding_model/
        └── [model files]
    └── storage/
        └── [vector store and document storage files]
```

### Example Usage

To process a new submission:

1. Place your `.pdf` or `.txt` file inside the `Code/` directory.
2. Update `samples.csv` with paths or identifiers for the new submission.
3. Run:
   ```bash
   python Code/pipeline.py
   ```
4. Check `output.csv` for final results and explanations.

```