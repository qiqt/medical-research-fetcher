# Medical Research Data Fetcher

A Python tool for fetching and processing medical research papers from PubMed and other academic sources. This tool provides a way to search, download, and organize scientific articles along with their metadata.

## Features

- Advanced search capabilities using PubMed's E-utilities
- PDF download support with automatic retry mechanism
- Comprehensive metadata extraction (authors, references, MeSH terms, etc.)
- Built-in rate limiting to respect API guidelines

## Prerequisites

- Python 3.8 or higher
- A registered email address for PubMed E-utilities

## Installation

1. Clone the repository:
```bash
git clone https://github.com/qiqt/medical-research-fetcher.git
cd medical-research-fetcher
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create environment configuration:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings:
```plaintext
PUBMED_EMAIL=your.email@example.com
PUBMED_TOOL=YourToolName
STORAGE_PATH=./data
PDF_STORAGE_PATH=./data/pdfs
REQUEST_DELAY=0.34
MAX_RETRIES=3
```

Required settings:
- `PUBMED_EMAIL`: Your email address (required by PubMed)
- `PUBMED_TOOL`: Name of your tool/application

Optional settings:
- `STORAGE_PATH`: Base path for storing data (default: ./data)
- `PDF_STORAGE_PATH`: Path for PDF storage (default: ./data/pdfs)
- `REQUEST_DELAY`: Delay between API requests in seconds (default: 0.34)
- `MAX_RETRIES`: Maximum retry attempts for failed requests (default: 3)

## Usage

### Basic Example

```python
from medical_research_fetcher import ArticleProcessor, load_config
from medical_research_fetcher.fetchers.pubmed import PubMedClient
from medical_research_fetcher.storage import LocalStorage

async def main():
    config = load_config()
    
    client = PubMedClient(config.get_pubmed_config())
    storage = LocalStorage(config.storage_path)
    processor = ArticleProcessor(client, storage)
    
    results = await processor.search_and_process(
        query="cancer immunotherapy",
        max_results=10
    )
    
    print(f"Found {results['total_articles_found']} articles")
    print(f"Successfully processed: {results['successfully_processed']}")
```

### Directory Structure

After running, the tool creates the following directory structure:
```
data/
├── pdfs/                 # Downloaded PDF files
├── metadata/
│   ├── xml/             # Article XML metadata
│   ├── summary/         # Article summaries
│   └── searches/        # Search results and summaries
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
