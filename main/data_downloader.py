import os
import requests
from bs4 import BeautifulSoup
import hashlib


def search_google_scholar(query, num_results=5):
    """
    Search Google Scholar and return a list of PDF links.
    """
    search_url = f"https://scholar.google.com/scholar?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    links = []

    for result in soup.select(".gs_or_ggsm a"):
        href = result.get("href")
        if href and href.endswith(".pdf"):  # Ensure the link ends with ".pdf"
            links.append(href)
        if len(links) >= num_results:
            break

    # Log the extracted links for debugging
    print(f"Extracted links: {links}")
    return links



def download_pdf(url, save_path):
    """
    Download a PDF file from a given URL and save it locally.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, stream=True)

    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        return True
    else:
        print(f"Failed to download {url}: HTTP {response.status_code}")
        return False

def download_papers_from_google_scholar(query, base_folder, num_results=5):
    """
    Search for papers on Google Scholar and download PDFs to a specified folder.
    """
    # Create topic-specific folder
    topic_folder = os.path.join(base_folder, query.replace(" ", "_"))
    os.makedirs(topic_folder, exist_ok=True)

    # Search for PDF links
    pdf_links = search_google_scholar(query, num_results)
    if not pdf_links:
        print(f"No valid PDF links found for the query: {query}")
        return 0  # Return 0 to indicate no PDFs were downloaded

    # Log the extracted links
    print(f"Found {len(pdf_links)} PDF links: {pdf_links}")

    # Download the PDFs
    downloaded_count = 0
    for i, pdf_url in enumerate(pdf_links, start=1):
        try:
            # Create a unique file name based on the URL
            file_hash = hashlib.md5(pdf_url.encode()).hexdigest()
            file_name = f"paper_{i}_{file_hash}.pdf"
            save_path = os.path.join(topic_folder, file_name)

            # Skip if the file already exists
            if os.path.exists(save_path):
                print(f"File already exists: {file_name}")
                downloaded_count += 1
                continue

            print(f"Downloading PDF {i}: {pdf_url}")
            if download_pdf(pdf_url, save_path):
                print(f"Saved PDF {i} to {save_path}")
                downloaded_count += 1
            else:
                print(f"Failed to download: {pdf_url}")

        except Exception as e:
            print(f"Error downloading PDF {i}: {pdf_url}")
            print(f"Exception: {e}")

    return downloaded_count  # Return the count of successfully downloaded PDFs
