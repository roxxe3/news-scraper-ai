# News Scraper AI

An intelligent news scraping and filtering system that collects articles from Les Echos, filters them by topic using AI, and provides a user-friendly interface for review and export.

## Features

- Automated scraping of Les Echos news articles from the previous day
- AI-powered article filtering using OpenAI's GPT-4
- Clean database storage using PostgreSQL/SQLAlchemy
- User-friendly Streamlit interface for:
  - Article fetching and filtering
  - Content review and selection
  - PDF report generation
- Robust error handling and logging
- Article caching for improved performance

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/news-scraper-ai.git
cd news-scraper-ai
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with:
```
LESECHOS_EMAIL=your_lesechos_account_email
LESECHOS_PASSWORD=your_lesechos_account_password
```

For the OpenAI API key, it's recommended to use the export method:

Linux/macOS:
```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

Windows:
```bash
set OPENAI_API_KEY=your_openai_api_key_here
```

   **Important**: You must have a Les Echos account to scrape articles. Many articles are behind a paywall, and authentication is required to access their content. Register at [Les Echos](https://www.lesechos.fr/signup) if you don't have an account.

5. (Optional) Configure categories to scrape:
   You can modify which Les Echos categories are scraped by editing the `category_urls` list in `scraper.py`. 
   By default, only the homepage and world news sections are enabled, but you can uncomment additional categories 
   as needed:
   ```python
   self.category_urls = [
       'https://www.lesechos.fr',
       'https://www.lesechos.fr/monde',
       #'https://www.lesechos.fr/politique-societe',
       # 'https://www.lesechos.fr/industrie-services',
       #'https://www.lesechos.fr/bourse',
       # Uncomment more categories as needed
   ]
   ```

## Usage

### Using the Streamlit Interface

1. Start the Streamlit app:
```bash
streamlit run streamlit_app.py
```

2. Open your browser and navigate to the displayed URL (usually http://localhost:8501)

3. Follow the UI steps to:
   - Fetch new articles or use existing ones
   - Filter articles by your chosen topic
   - Review and select articles
   - Generate a PDF report

### Using the Command Line

You can also run the pipeline from the command line:

```bash
python cli_pipeline.py --topic "Artificial Intelligence" --verbose
```

## Project Structure

- `scraper.py`: Web scraping implementation for Les Echos
- `AI_filter.py`: OpenAI-powered article filtering
- `save_db.py`: Database models and storage logic
- `streamlit_app.py`: User interface implementation
- `cli_pipeline.py`: Command-line interface
- `helpers.py`: Utility functions and logging
- `output/`: Directory for cached articles and generated files

## Database Schema

The articles are stored with the following structure:

- `id`: Primary key
- `title`: Article title (String, 255 chars)
- `link`: Source URL (String, 255 chars)
- `category`: Article category (String, 100 chars)
- `topic`: Filtering topic (String, 100 chars)
- `published_date`: When the article was published (DateTime)
- `updated_date`: When the article was last updated (DateTime)
- `content`: Full article content (Text)

## Error Handling

The system includes robust error handling for:
- Network connectivity issues
- API rate limits
- Invalid article formats
- Database operations
- File I/O operations

## Contributing

Feel free to submit issues and enhancement requests!
