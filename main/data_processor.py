import os
import fitz  # PyMuPDF
from random import sample
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path, max_pages=10):
    """Extract text from the first `max_pages` pages of a PDF."""
    text = ""
    try:
        with fitz.open(pdf_path) as pdf:
            for page_num in range(min(max_pages, len(pdf))):
                text += pdf[page_num].get_text()
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    return text


def get_random_pdf_paths(folder_path, num_files):
    """Return a list of random PDF file paths from the given folder."""
    pdf_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.pdf')]
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in folder: {folder_path}")
    return sample(pdf_files, min(num_files, len(pdf_files)))


def is_valid_pdf(file_path):
    """Check if the file is a valid PDF."""
    try:
        with fitz.open(file_path) as pdf:
            return pdf.page_count > 0  # Ensure the PDF has at least one page
    except Exception as e:
        print(f"Invalid PDF: {file_path}, Error: {e}")
        return False


def process_pdfs(base_folder, topic, max_pages=10, num_files=1):
    """
    Process multiple PDFs by extracting text.
    """
    topic_folder = os.path.join(base_folder, topic.replace(" ", "_"))
    if not os.path.exists(topic_folder) or not os.listdir(topic_folder):
        raise FileNotFoundError(f"No PDF files found in folder: {topic_folder}")

    pdf_paths = [
        f for f in os.listdir(topic_folder) if f.endswith(".pdf") and is_valid_pdf(os.path.join(topic_folder, f))
    ]
    if not pdf_paths:
        raise FileNotFoundError(f"No valid PDF files found in folder: {topic_folder}")

    # Select random PDFs to process
    pdf_paths = pdf_paths[:num_files]
    processed_texts = []
    for pdf_path in pdf_paths:
        try:
            text = extract_text_from_pdf(os.path.join(topic_folder, pdf_path), max_pages=max_pages)
            processed_texts.append(text)
            print(f"Processed: {pdf_path}")
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")

    return processed_texts



# Load NLP models
nlp = spacy.load("en_core_web_sm")  # For NER
sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
#sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", device=-1)



def extract_keywords(text, top_n=5):
    """
    Extract the top_n keywords from the text using TF-IDF.
    """
    vectorizer = TfidfVectorizer(stop_words="english", max_features=top_n)
    tfidf_matrix = vectorizer.fit_transform([text])
    keywords = vectorizer.get_feature_names_out()
    return list(keywords)


def classify_topic(text):
    """
    Classify the topic based on specific keywords or phrases.
    """
    if "machine learning" in text.lower() or "ai" in text.lower():
        return "Artificial Intelligence"
    elif "finance" in text.lower() or "economy" in text.lower():
        return "Finance"
    elif "biology" in text.lower() or "health" in text.lower():
        return "Biology/Health"
    else:
        return "General"


def analyze_sentiment(text):
    """
    Perform sentiment analysis using a pre-trained model.
    """
    result = sentiment_model(text[:512])  # Limit to 512 characters for transformer models
    return result[0]["label"]


def extract_entities(text):
    """
    Extract entities (names, dates, amounts) using spaCy.
    """
    doc = nlp(text)
    entities = {
        "names": [ent.text for ent in doc.ents if ent.label_ == "PERSON"],
        "dates": [ent.text for ent in doc.ents if ent.label_ == "DATE"],
        "amounts": [ent.text for ent in doc.ents if ent.label_ in ["MONEY", "CARDINAL"]],
    }
    return entities
