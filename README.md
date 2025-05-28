# FactCheck API - KG LLM Benchmark 

A Django-based REST API for the FactCheck benchmark, designed to evaluate Large Language Models (LLMs) capabilities in Knowledge Graph fact verification. This system provides access to dataset containing over 2 million documents.

- 📣 NEW! It's now available as a web service at [Factcheck-Api](https://factcheck-api.dei.unipd.it/).

For documentation, examples, and usage instructions, please refer to the sections below.

## 📚 Research Context

This API is part of the research paper **"Knowledge Graph Validation via Large Language Models"** and provides a standardized interface for:
- Evaluating LLM performance on KG fact verification
- Accessing curated datasets with gold-standard annotations
- Retrieving external evidence through Google SERP content
- Supporting reproducible benchmarking across different models

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Django 5.2+

### Installation

### 🐳 Docker Deployment -- Recommended

#### Using Docker Compose

For production deployment or if you prefer containerized setup, you can use Docker Compose:

```bash
# Clone the repository
git clone https://github.com/FactCheck-AI/factcheck-api.git
cd factcheck-api

# Run with custom environment variables
POSTGRES_DB=mydb POSTGRES_USER=myuser POSTGRES_PASSWORD=mypassword docker compose up
```

**Environment Variables:**
- `POSTGRES_DB`: Database name (default: `mockapi`)
- `POSTGRES_USER`: Database username (default: `postgres`)
- `POSTGRES_PASSWORD`: Database password (default: `mockapi`)
- `WEBPROXY_PORT`: External port for the web service (default: `8094`)

### Default Docker Setup

For quick testing with default settings:

```bash
docker compose up
```

This will start:
- **Backend API** on `http://localhost:8095`
- **PostgreSQL Database** with default credentials
- **Automatic migrations** and static file collection

### Database Backup and Restore

#### Restoring database from dump file

you can restore them using the provided script through the actual dump:

```bash
# Make the script executable
chmod +x db_restore.sh

# Restore database with your credentials
./db_restore.sh mydb myuser mypassword
```

**Script Parameters:**
- `mydb`: Target database name
- `myuser`: Database username
- `mypassword`: Database password

**Note:** The restore script download backup files in the `db/` directory. These files will be integrated and restored into the Docker PostgreSQL container.

#### How the Restore Process Works

1. **Fetch** the backup file from Google Drive -- [Link](https://drive.usercontent.google.com/download?id=1FDU5Wm8mHCBxlTMD-CptyyTqdSDkjfH5&confirm=t)
2. **Copies** the fetched backup into the Docker container
3. **Restores** the database using `pg-restore`
4. **Cleans up** temporary files

---
### 🛠️ Manual Installation -- Not recommend, use Docker instead

1. **Clone the repository**
```bash
git clone https://github.com/FactCheck-AI/factcheck-api.git
cd factcheck-api
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure database**
```bash
# Update mockapi/settings.py with your PostgreSQL credentials
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mockapi',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

4. **Run migrations**
```bash
python manage.py migrate
```

5. **Populate database (optional)**
```bash
python manage.py populate_db --clear
```

6. **Start the server**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

---

## 🔑 Authentication

All API endpoints require authentication via API key. Include your API key in the request headers:

```
X-API-Key: your-api-key-here
```

Or as a query parameter:
```
?api_key=your-api-key-here
```

## 📖 API Documentation

### Base URL
```
http://localhost:8000/api/
```

---

### 🔐 Authentication Endpoints

#### Create API Key
Generate a new API key for accessing the system.

**POST** `/api/create-key/`

**Request Body:**
```json
{
    "username": "researcher_name",
    "email": "researcher@example.com", 
    "key_name": "My Research Project"
}
```

**Response:**
```json
{
    "success": true,
    "api_key": "1a2b3c4d5e6f7g8h9i0j",
    "message": "API key created successfully!"
}
```

**Error Response:**
```json
{
    "error": "Username and email are required"
}
```

---

### 📊 Dataset Endpoints

#### List All Datasets
Retrieve information about available datasets.

**GET** `/api/datasets/`

**Headers:**
```
X-API-Key: your-api-key-here
```

**Response:**
```json
{
    "datasets": [
        {
            "name": "factbench",
            "description": "FactBench is a benchmark designed to evaluate fact validation algorithms.",
            "created_at": "2024-01-15T10:30:00Z"
        },
        {
            "name": "yago", 
            "description": "YAGO is a KG derived from Wikipedia, WordNet and GeoNames.",
            "created_at": "2024-01-15T10:30:00Z"
        },
        {
            "name": "dbpedia",
            "description": "DBPedia is a KG derived from structured information extracted from Wikipedia.",
            "created_at": "2024-01-15T10:30:00Z"
        }
    ],
    "count": 3
}
```

#### List Facts in Dataset
Get all facts within a specific dataset.

**GET** `/api/datasets/{dataset_name}/facts/`

**Parameters:**
- `dataset_name`: Name of the dataset (factbench, yago, dbpedia)

**Response:**
```json
{
    "dataset": "factbench",
    "facts": [
        {
            "fact_id": "correct_1",
            "created_at": "2024-01-15T10:30:00Z"
        },
        {
            "fact_id": "wrong_mix_domain_1", 
            "created_at": "2024-01-15T10:30:00Z"
        }
    ],
    "count": 2800
}
```

---

### ❓ Question Endpoints

#### Get Questions for Fact
Retrieve all fetchable questions for a specific fact, sorted by relevance score.

**GET** `/api/datasets/{dataset_name}/facts/{fact_id}/questions/`

**Parameters:**
- `dataset_name`: Name of the dataset
- `fact_id`: Unique identifier for the fact

**Response:**
```json
{
    "success": true,
    "dataset": "factbench",
    "fact_id": "correct_1", 
    "questions": [
        {
            "fetch_id": 0,
            "text": "Who received the Nobel Peace Prize in 1901?",
            "score": 0.95,
            "is_fetchable": true
        },
        {
            "fetch_id": 1,
            "text": "What award did Henry Dunant receive?",
            "score": 0.87,
            "is_fetchable": true
        }
    ],
    "count": 10
}
```

#### Get Question HTML Content and URLs
Access HTML content and available URLs for a specific question by rank.

**GET** `/api/datasets/{dataset_name}/facts/{fact_id}/questions/{question_rank}/`

**Parameters:**
- `dataset_name`: Name of the dataset
- `fact_id`: Unique identifier for the fact
- `question_rank`: Rank of the question (0-based index)

**Response:**
```json
{
    "success": true,
    "dataset": "factbench",
    "fact_id": "correct_1",
    "question_rank": 0,
    "question": {
        "text": "Who received the Nobel Peace Prize in 1901?",
        "score": 0.95,
        "is_fetchable": true
    },
    "html_content": {
        "content": "<html>...</html>"
    },
    "available_urls": [
        {
            "url": "https://www.nobelprize.org/prizes/peace/1901/dunant/facts/",
            "domain": "nobelprize.org",
            "title": "Henry Dunant – Facts",
            "description": "The Nobel Peace Prize 1901 was divided equally...",
            "rank": 0,
            "scrape_count": 5,
            "last_scraped": "2024-01-15T10:30:00Z",
            "has_serp_content": true
        }
    ],
    "total_urls": 10
}
```

---

### 🔍 SERP Content Endpoints

#### Get SERP Content by Query Parameter (Recommended)
Retrieve SERP (Search Engine Results Page) content for a specific URL using query parameters.

**GET** `/api/serp-content/?url={url}&fields={fields}`

**Query Parameters:**
- `url` (required): The URL to retrieve content for
- `fields` (optional): Comma-separated list of fields to return

**Available Fields:**
- `url`, `title`, `text`, `summary`
- `language`, `authors`, `publish_date`
- `meta_description`, `meta_keywords`, `meta_site_name`
- `top_image`, `meta_img`, `images`
- `keywords`, `tags`, `movies`
- `canonical_link`, `read_more_link`

**Example Request:**
```
GET /api/serp-content/?url=https://www.nobelprize.org/prizes/peace/1901/dunant/facts/&fields=title,text,summary
```

**Response:**
```json
{
    "success": true,
    "url": "https://www.nobelprize.org/prizes/peace/1901/dunant/facts/",
    "fields_requested": ["title", "text", "summary"],
    "scraped_at": "2024-01-15T10:30:00Z",
    "data": {
        "title": "Henry Dunant – Facts",
        "text": "Founder of the Red Cross\n\nIn 1859, a battle was raging...",
        "summary": "Biography and achievements of Henry Dunant..."
    }
}
```

---

## 📈 Usage Examples

### Python Example

```python
import requests

# Configuration
BASE_URL = "http://localhost:8000/api"
API_KEY = "your-api-key-here"
HEADERS = {"X-API-Key": API_KEY}

# Get all datasets
response = requests.get(f"{BASE_URL}/datasets/", headers=HEADERS)
datasets = response.json()
print(f"Available datasets: {len(datasets['datasets'])}")

# Get facts from FactBench
response = requests.get(f"{BASE_URL}/datasets/factbench/facts/", headers=HEADERS)
facts = response.json()
print(f"FactBench contains {facts['count']} facts")

# Get questions for a specific fact
fact_id = facts['facts'][0]['fact_id']
response = requests.get(
    f"{BASE_URL}/datasets/factbench/facts/{fact_id}/questions/", 
    headers=HEADERS
)
questions = response.json()
print(f"Found {questions['count']} questions for fact {fact_id}")

# Get SERP content
url = "https://www.nobelprize.org/prizes/peace/1901/dunant/facts/"
response = requests.get(
    f"{BASE_URL}/serp-content/",
    params={"url": url, "fields": "title,text,summary"},
    headers=HEADERS
)
content = response.json()
print(f"Retrieved content: {content['data']['title']}")
```

### cURL Examples

```bash
# Create API key
curl -X POST http://localhost:8000/api/create-key/ \
  -H "Content-Type: application/json" \
  -d '{"username": "researcher", "email": "test@example.com", "key_name": "Test Key"}'

# List datasets
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/datasets/

# Get SERP content
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/serp-content/?url=https://example.com&fields=title,text"
```

---

## 📊 Dataset Information

### FactBench
- **Facts:** 2,800
- **Predicates:** 10
- **Gold Accuracy:** 54%
- **Description:** Systematically generated incorrect facts for validation testing

### YAGO
- **Facts:** 1,386
- **Predicates:** 16
- **Gold Accuracy:** 99.2%
- **Description:** High-quality facts derived from Wikipedia, WordNet, and GeoNames

### DBpedia
- **Facts:** 9,344
- **Predicates:** 1,092
- **Gold Accuracy:** 85%
- **Description:** Broad coverage extracted from Wikipedia with diverse schemas

### RAG Dataset
- **Documents:** 2,090,305
- **Questions:** 130,820
- **Coverage:** 87.4% text coverage rate
- **Source:** Google SERP results for fact verification

---

## ⚙️ Configuration

### Create Superuser
```bash
python manage.py createsuperuser
```

### Access Admin Interface
Visit `http://localhost:8000/admin/` to manage data through Django admin.

---

## 📝 Error Handling

### Common Error Responses

**401 Unauthorized:**
```json
{
    "error": "Invalid API key"
}
```

**404 Not Found:**
```json
{
    "error": "URL not found", 
    "url_tried": ["https://example.com/", "https://example.com"],
    "suggestion": "Use query parameter method: /api/serp-content/?url=YOUR_URL"
}
```

**400 Bad Request:**
```json
{
    "error": "URL parameter is required",
    "usage": "GET /api/serp-content/?url=https://example.com"
}
```

**500 Internal Server Error:**
```json
{
    "error": "Internal server error: detailed error message"
}
```

## 📚 Research Applications

This API supports research in:

- **LLM Evaluation:** Benchmark different models on fact verification tasks
- **RAG Systems:** Access pre-collected evidence for retrieval-augmented generation
- **Knowledge Graph Quality:** Systematic evaluation of KG accuracy
- **Multi-modal Consensus:** Compare predictions across multiple models

### Citation

If you use this API in your research, please cite:

```bibtex
@article{....,
  title={Knowledge Graph Validation via Large Language Models},
  author={Shami, Farzad and Marchesin, Stefano and Silvello, Gianmaria},
  journal={....},
  year={2025}
}
```
---

## 📄 Acknowledgements

This work is partially supported by the HEREDITARY Project, as part of the European Union's Horizon Europe research and innovation program under grant agreement No. GA 101137074.
The authors thank Andrea Segala for contributing to the experiments on zero-shot and few-shot prompting during his master's thesis.

---

## 🔗 Related Resources

- **Web Interface:** https://factcheck.dei.unipd.it/
- **Datasets:** https://huggingface.co/FactCheck-AI
- **Paper:** Available on .... (link coming soon)