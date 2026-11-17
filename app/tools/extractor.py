import io
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader



def extract_html(url: str):
    """
    Extract readable article content from an HTML webpage.
    """

    response = requests.get(
        url,
        timeout=15,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove unnecessary webpage elements
    for element in soup([
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "aside",
        "form",
        "button"
    ]):
        element.decompose()

    # Prefer the main article/paper content
    content = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_="ltx_page_main")
        or soup.body
    )

    if not content:
        return ""

    text = content.get_text(
        separator=" ",
        strip=True
    )

    # Clean excessive whitespace
    text = " ".join(text.split())

    return text

def extract_pdf(url: str):
    """
    Download a PDF and extract its text.
    """

    response = requests.get(
        url,
        timeout=20,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    pdf_file = io.BytesIO(response.content)

    reader = PdfReader(pdf_file)

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)

def normalize_url(url: str):
    """
    Convert known problematic URLs into more extractable versions.
    """

    # arXiv PDF -> arXiv HTML
    if "arxiv.org/pdf/" in url:

        paper_id = url.split("/pdf/")[1]

        # Remove .pdf
        paper_id = paper_id.replace(".pdf", "")

        return f"https://arxiv.org/html/{paper_id}"

    return url

def extract_content(url: str):

    url_lower = url.lower()

    print(f"Attempting extraction: {url}")

    # Prefer HTML version for arXiv papers
    if "arxiv.org" in url_lower:

        if "/html/" in url_lower:
            return extract_html(url)

        if "/pdf/" in url_lower:
            html_url = url.replace(
                "https://arxiv.org/pdf/",
                "https://arxiv.org/html/"
            ).replace(".pdf", "")

            try:
                content = extract_html(html_url)
                if content:
                    return content
                print(f"HTML extraction returned empty content: {html_url}")
            except Exception as e:
                print(f"HTML extraction failed: {e}")
            try:
                return extract_pdf(url)
            except Exception as e:
                print(f"PDF extraction failed: {e}")
                return ""

        if "/abs/" in url_lower:
            html_url = url.replace(
                "https://arxiv.org/abs/",
                "https://arxiv.org/html/"
            )

            try:
                return extract_html(html_url)
            except Exception:
                return extract_html(url)

    # Normal PDF
    if ".pdf" in url_lower:
        return extract_pdf(url)

    # Normal webpage
    return extract_html(url)

if __name__ == "__main__":

    url = "https://arxiv.org/html/2409.05335v1"

    content = extract_content(url)

    print("\nExtracted content:\n")
    print(content[:5000])
