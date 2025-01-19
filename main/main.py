import streamlit as st
from datetime import datetime
from data_processor import extract_text_from_pdf, process_pdfs, classify_topic, extract_keywords
from langgraph_workflow import build_langgraph_workflow
from data_downloader import download_papers_from_google_scholar
from langchain_core.messages import HumanMessage
from google.cloud import bigquery


# To be Completed

def store_in_bigquery(dataset_id, table_id, data):
    """
    Store structured data in BigQuery.
    Args:
        dataset_id (str): The BigQuery dataset ID.
        table_id (str): The BigQuery table ID.
        data (dict): The data to insert into BigQuery.
    """
    client = bigquery.Client()

    table_ref = f"{client.project}.{dataset_id}.{table_id}"

    # Add a timestamp for when the data is inserted
    data["created_at"] = datetime.utcnow().isoformat()

    # Insert rows into BigQuery
    errors = client.insert_rows_json(table_ref, [data])

    if errors:
        print(f"Error inserting data into BigQuery: {errors}")
    else:
        print("Data successfully inserted into BigQuery.")


def process_with_selected_tasks(text, selected_tasks):
    """
    Process the text based on the selected tasks and store results in BigQuery.
    """
    workflow = build_langgraph_workflow()
    if workflow is None:
        return {"Error": "Workflow timed out. Please try again."}

    state = {"messages": [HumanMessage(content=text)]}
    final_state = workflow.invoke(state)

    results = {}
    if "Summary" in selected_tasks:
        results["Summary"] = final_state.get("summary", "No summary generated.")
    if "Metadata Extraction" in selected_tasks:
        metadata = final_state.get("metadata", {})
        results["Metadata"] = {
            "Title": metadata.get("title", "N/A"),
            "Authors": metadata.get("authors", []),
            "Publication Date": metadata.get("publication_date", "N/A"),
            "Abstract": metadata.get("abstract", "N/A"),
        }
    if "Sentiment Analysis" in selected_tasks:
        results["Sentiment"] = final_state.get("sentiment", "Unknown")
    if "Entity Recognition" in selected_tasks:
        results["Entities"] = final_state.get("entities", {})

    # Prepare data for BigQuery
    bigquery_data = {
        "document_id": hash(text),  # Use hash of the text as a unique document ID
        "title": results["Metadata"].get("Title", "N/A"),
        "authors": results["Metadata"].get("Authors", []),
        "publication_date": results["Metadata"].get("Publication Date", "N/A"),
        "abstract": results["Metadata"].get("Abstract", "N/A"),
        "summary": results.get("Summary", "N/A"),
        "sentiment": results.get("Sentiment", "Unknown"),
        "entities": results.get("Entities", {}),
    }

    # Send data to BigQuery

    #store_in_bigquery("llm_metadata", "documents", bigquery_data)

    return results


def main():
    st.title("Document Processing and Paper Search")

    # Tab layout
    tab1, tab2 = st.tabs(["Upload PDF", "Search Google Scholar"])

    # Task Selection Options
    task_options = [
        "Summary",
        "Metadata Extraction",
        "Sentiment Analysis",
        "Entity Recognition",
    ]

    # Tab 1: Upload PDF
    with tab1:
        st.header("Upload and Process a PDF")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        selected_tasks = st.multiselect(
            "Select tasks to perform for the uploaded PDF",
            task_options,
            default=["Summary"],
            key="upload_tasks",
        )

        if uploaded_file is not None:
            # Save the uploaded file to disk
            with open("uploaded_file.pdf", "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("File uploaded successfully!")

            # Extract text from the uploaded PDF
            text = extract_text_from_pdf("uploaded_file.pdf", max_pages=10)
            st.text_area("Extracted Text", text, height=300)

            # Process with LangGraph based on selected tasks
            if st.button("Process Uploaded PDF"):
                results = process_with_selected_tasks(text, selected_tasks)
                for task, output in results.items():
                    if task == "Metadata":
                        st.subheader(task)
                        st.write(f"**Title**: {output.get('Title', 'N/A')}")
                        st.write(f"**Authors**: {', '.join(output.get('Authors', []))}")
                        st.write(f"**Publication Date**: {output.get('Publication Date', 'N/A')}")
                        st.write(f"**Abstract**: {output.get('Abstract', 'N/A')}")
                    else:
                        st.subheader(task)
                        st.write(output)

    # Tab 2: Search Google Scholar
    with tab2:
        st.header("Search and Process Papers")
        query = st.text_input("Enter search query")
        num_papers = st.number_input("Number of papers to download", min_value=1, max_value=10, value=3)
        selected_tasks = st.multiselect(
            "Select tasks to perform for downloaded papers",
            task_options,
            default=["Summary"],
            key="search_tasks",
        )

        if st.button("Search and Process"):
            if query:
                # Download papers
                st.write(f"Searching for '{query}' and downloading {num_papers} papers...")
                base_folder = "data/"
                download_papers_from_google_scholar(query, base_folder, num_results=num_papers)
                topic_folder = os.path.join(base_folder, query.replace(" ", "_"))
                
                # Check if files exist
                if not os.path.exists(topic_folder) or not os.listdir(topic_folder):
                    st.error(f"No PDFs were downloaded for the query: {query}")
                else:
                    st.success("Papers downloaded successfully!")

                    # Process the downloaded PDFs
                    st.write("Processing downloaded papers...")
                    processed_texts = process_pdfs(base_folder, query, max_pages=10, num_files=num_papers)

                    # Display results for each document
                    for i, text in enumerate(processed_texts, 1):
                        st.subheader(f"Document {i}")
                        results = process_with_selected_tasks(text, selected_tasks)
                        for task, output in results.items():
                            if task == "Metadata":
                                st.subheader(f"{task} (Document {i})")
                                st.write(f"**Title**: {output.get('Title', 'N/A')}")
                                st.write(f"**Authors**: {', '.join(output.get('Authors', []))}")
                                st.write(f"**Publication Date**: {output.get('Publication Date', 'N/A')}")
                                st.write(f"**Abstract**: {output.get('Abstract', 'N/A')}")
                            else:
                                st.write(f"**{task}**: {output}")


if __name__ == "__main__":
    main()
