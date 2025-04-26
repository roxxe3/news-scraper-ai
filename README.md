# News Scraper AI

A Python tool for scraping news articles from Les Echos website.

## Features

- Scrape free articles from Les Echos
- Scrape premium articles with login credentials
- Extract article metadata (title, published date, updated date)
- Extract full article content
- Save results in JSON format
- Command-line interface with various options
- Supports .env file for storing credentials

## Installation

1. Clone this repository:
```
git clone <repository-url>
cd news-scraper-ai
```

2. Install required dependencies:
```
pip install hrequests beautifulsoup4 playwright python-dotenv
```

3. Install Playwright browsers:
```
python -m playwright install
```

4. Set up your credentials:
   - Copy `.env.example` to `.env`
   - Edit `.env` and add your Les Echos login credentials

## Usage

### Basic Usage

```
python main.py
```

This will:
1. Fetch articles from Les Echos
2. Use credentials from your .env file or prompt if not found
3. Scrape article content
4. Save results to `output/articles.json`

### Command-line Options

```
python main.py --help
```

Options:
- `--free-only`: Only scrape free articles (no login required)
- `--output FILENAME`: Specify output filename (default: articles.json)
- `--sample`: Run with only the first article (for testing)
- `--verbose`: Enable verbose output

### Examples

Scrape only free articles:
```
python main.py --free-only
```

Run a quick test with just one article:
```
python main.py --sample
```

Specify a custom output file:
```
python main.py --output my_articles.json
```

### Environment Variables

Create a `.env` file in the project root with these variables:

```
LESECHOS_EMAIL=your_email@example.com
LESECHOS_PASSWORD=your_password
```

## Project Structure

- `main.py`: Entry point with command-line interface
- `scraper.py`: Contains the `LesEchosScraper` class with scraping logic
- `helpers.py`: Utility functions for date processing, file operations, etc.
- `output/`: Directory where scraped data is saved
- `.env`: File for storing credentials (not committed to source control)

## License

MIT