from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
from typing import TypedDict, List
from openai import OpenAI
import streamlit as st



# Define the state schema using TypedDict
class StateSchema(TypedDict):
    messages: List[HumanMessage]
    summary: str
    metadata: dict  
    sentiment: str
    entities: dict


client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])

def summarization_node(state: StateSchema):
    """Summarize document content using the latest OpenAI API."""
    content = state["messages"][-1].content

    # Call OpenAI GPT to generate a summary
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes text."},
            {"role": "user", "content": f"Summarize the following text:\n\n{content}"}
        ],
        temperature=0.7,
        max_tokens=300,  # Adjust this to control the length of the summary
        n=1,             # Generate a single summary
        stop=None        # Allow the summary to stop naturally
    )

    summary = response.choices[0].message.content.strip()
    state["summary"] = summary

    return state

import re

def metadata_extraction_node(state: StateSchema):
    """Extract metadata (title, authors, publication date, abstract) using OpenAI API."""
    content = state["messages"][-1].content

    # Call OpenAI GPT to extract metadata
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an assistant specialized in extracting metadata from research papers. "
                           "Your output should strictly follow this format:\n"
                           "**Title:** <title>\n"
                           "**Authors:** <author1>, <author2>, ...\n"
                           "**Publication Date:** <date>\n"
                           "**Abstract:** <abstract>"
            },
            {"role": "user", "content": f"Extract the metadata from the following text:\n\n{content}"}
        ],
        temperature=0.7,
        max_tokens=500,
        n=1,
        stop=None
    )

    metadata_response = response.choices[0].message.content.strip()
    print(f"Metadata Extraction Response:\n{metadata_response}")

    # Initialize metadata dictionary
    metadata = {
        "title": "N/A",
        "authors": [],
        "publication_date": "N/A",
        "abstract": "N/A",
    }

    # Extract metadata fields using regex
    title_match = re.search(r"\*\*Title:\*\*\s*(.+)", metadata_response)
    authors_match = re.search(r"\*\*Authors:\*\*\s*(.+)", metadata_response)
    date_match = re.search(r"\*\*Publication Date:\*\*\s*(.+)", metadata_response)
    abstract_match = re.search(r"\*\*Abstract:\*\*\s*(.+)", metadata_response, re.DOTALL)

    if title_match:
        metadata["title"] = title_match.group(1).strip()
    if authors_match:
        authors = authors_match.group(1).strip()
        metadata["authors"] = [author.strip() for author in authors.split(",")]
    if date_match:
        metadata["publication_date"] = date_match.group(1).strip()
    if abstract_match:
        metadata["abstract"] = abstract_match.group(1).strip()

    # Store the parsed metadata in the state
    state["metadata"] = metadata
    return state


def sentiment_analysis_node(state: StateSchema):
    """Perform sentiment analysis."""
    summary = state["summary"]
    state["sentiment"] = "positive" if "good" in summary.lower() else "neutral"
    return state


def entity_recognition_node(state: StateSchema):
    """Extract entities."""
    summary = state["summary"]
    state["entities"] = {
        "names": ["Alice"] if "Alice" in summary else [],
        "dates": ["2025-01-01"] if "2025" in summary else [],
        "amounts": ["$1000"] if "$1000" in summary else [],
    }
    return state


import signal

class TimeoutException(Exception):
    pass

import concurrent.futures
from langgraph.graph import StateGraph


import concurrent.futures

def run_with_timeout(func, args=(), timeout=30):
    """
    Run a function with a timeout using concurrent.futures.
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func, *args)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            print(f"Function {func.__name__} timed out after {timeout} seconds.")
            return None


def build_langgraph_workflow():
    """
    Build a LangGraph workflow with metadata extraction.
    """
    def build_workflow():
        graph_builder = StateGraph(state_schema=StateSchema)

        # Add nodes with unique names
        graph_builder.add_node("summarization", summarization_node)
        graph_builder.add_node("metadata_extraction", metadata_extraction_node)  # Renamed from 'metadata'
        graph_builder.add_node("sentiment_analysis", sentiment_analysis_node)
        graph_builder.add_node("entity_recognition", entity_recognition_node)

        # Define task order
        graph_builder.add_edge("summarization", "metadata_extraction")  # Updated edge
        graph_builder.add_edge("metadata_extraction", "sentiment_analysis")
        graph_builder.add_edge("sentiment_analysis", "entity_recognition")

        # Set entry and exit points
        graph_builder.set_entry_point("summarization")
        graph_builder.set_finish_point("entity_recognition")

        return graph_builder.compile()

    return run_with_timeout(build_workflow, timeout=30)



