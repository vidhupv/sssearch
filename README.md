# 🔍 Visual Memory Search (SSSearch)

Search your screenshot history using natural language queries for both text content AND visual elements.

## Features

- **OCR Text Extraction**: Extract text from screenshots using Tesseract
- **Visual Analysis**: Describe visual elements using Claude AI
- **Semantic Search**: Find screenshots using natural language queries
- **Confidence Scoring**: Get relevance scores for search results
- **Flexible Storage**: MongoDB Atlas or local storage fallback

## Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Install Tesseract OCR**
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

3. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Run the Application**
```bash
streamlit run app.py
```

## Usage

1. **Upload Screenshots**: Use the sidebar to upload PNG, JPG, or other image files
2. **Process Images**: Click "Process Screenshots" to extract text and analyze visuals
3. **Search**: Enter natural language queries like:
   - "error message about auth"
   - "screenshot with blue button"
   - "dashboard with charts"
   - "login form"

## Architecture

- **Frontend**: Streamlit
- **OCR**: Tesseract (pytesseract)
- **Vision**: Claude API
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Storage**: MongoDB Atlas + local fallback
- **Search**: Cosine similarity with embeddings

## API Keys Required

- **Anthropic API Key**: For Claude vision analysis
- **MongoDB URI** (optional): For cloud storage, otherwise uses local storage

## Example Queries

- "error message" - Find screenshots with error dialogs
- "blue button" - Find screenshots with blue UI elements  
- "login form" - Find authentication pages
- "dashboard" - Find admin or analytics interfaces
- "code editor" - Find development environment screenshots