# llm_pipeline
LLM pipeline with LangGraph for processing research papers

This pipeline processes academic research papers in the PDF format and extracts and structures key information, ultimately storing it in BigQuery for analysis. This pipeline contains the following:
● Use of LLM libraries like LangGraph for LLM orchestration
● Handle document processing of PDFs
● Implement structured data extraction
● Work with Google Cloud Platform

Document Ingestion
● Accept PDF research papers as input
● Extract raw text while maintaining document structure

Information Extraction:
● Extract basic metadata (title, authors, publication date, abstract)
● Identify and extract key research findings and methodology
● Generate structured summaries and keywords

Data Storage
● Design a BigQuery schema to store the extracted information
● Implement data loading to BigQuery


This project requires a working and active OPENAI API key. 

## Configuration
Create a `.streamlit/secrets.toml` file in the root directory with the following format:

```toml
OPENAI_API_KEY = "your_openai_api_key_here"
```


