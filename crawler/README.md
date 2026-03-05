# News Country Crawler

A Python web crawler that analyzes which countries appear in US news articles and calculates their appearance probability. Generates choropleth-ready data showing how frequently each country is mentioned in news headlines.

## Features

✨ **Multi-source Crawling**: Scrapes from BBC, Reuters, CNN, The Guardian, and Al Jazeera
📊 **Comprehensive Country Detection**: Recognizes 195+ countries with aliases (e.g., "UK" = "United Kingdom", "Japanese" = "Japan")
💾 **Intermediate Storage**: Saves raw titles to `titles.json` for reprocessing
🔄 **Append Mode**: Automatically appends to existing titles.json instead of overwriting
⚙️ **Flexible Modes**: Run scraping only, calculation only, or both
📈 **Choropleth-Ready Output**: CSV format (`country,country_ISO,value`) ready for visualization

## Installation

### Prerequisites
- Python 3.7+
- pip

### Install Dependencies

```bash
pip install scrapy --break-system-packages
```

That's it! The script uses only Scrapy and Python standard library.

## Quick Start

### 1. Run Everything (Recommended)
Scrape 200 articles and calculate probabilities:
```bash
python news_country_crawler.py --mode both --articles 200
```

### 2. Scrape Only
Collect article titles without calculating:
```bash
python news_country_crawler.py --mode scrape --articles 500
```

### 3. Calculate Only
Process existing `titles.json`:
```bash
python news_country_crawler.py --mode calculate
```

## Usage Examples

### Basic Usage
```bash
# Default: scrape 100 articles and calculate
python news_country_crawler.py

# Scrape 1000 articles for comprehensive analysis
python news_country_crawler.py --mode both --articles 1000

# Quick test with 50 articles
python news_country_crawler.py --articles 50
```

### Advanced Usage
```bash
# Custom file names
python news_country_crawler.py --mode both \
    --titles my_titles.json \
    --output my_results.csv

# Incremental scraping: append more articles
python news_country_crawler.py --mode scrape --articles 200
python news_country_crawler.py --mode scrape --articles 200  # Adds 200 more!
python news_country_crawler.py --mode calculate  # Process all collected titles
```

## Command-Line Arguments

```
--mode {scrape,calculate,both}
    scrape     : Only collect news titles (saves to titles.json)
    calculate  : Only process existing titles.json
    both       : Run scraping then calculation (default)

--articles NUMBER
    Number of articles to scrape (default: 100, recommended: 100-1000)

--titles FILEPATH
    Path to titles JSON file (default: titles.json)

--output FILEPATH
    Path to output CSV file (default: country_probabilities.csv)
```

## Configuration

### Customize News Sources

Edit the `NEWS_SOURCES` list in `news_country_crawler.py`:

```python
NEWS_SOURCES = [
    {
        'name': 'Your News Source',
        'start_urls': ['https://example.com/news'],
        'allowed_domains': ['example.com'],
        'title_selector': 'h2::text, h3::text'  # CSS selector for titles
    },
    # Add more sources here...
]
```

### Adjust Country Aliases

The script includes comprehensive aliases for all countries. To add custom aliases, edit the `COUNTRY_DATA` dictionary:

```python
COUNTRY_DATA = {
    'Your Country': {
        'iso': 'ABC',  # ISO 3166-1 alpha-3 code
        'aliases': ['Country Name', 'Common Alias', 'Demonym']
    },
    # ...
}
```

## Output Format

### titles.json (Intermediate)
```json
[
  {
    "title": "UK Prime Minister meets with Japanese officials",
    "source": "bbc.com",
    "url": "https://www.bbc.com/news/world"
  },
  {
    "title": "French economy shows growth",
    "source": "reuters.com", 
    "url": "https://www.reuters.com/world/"
  }
]
```

### country_probabilities.csv (Final Output)
```csv
country,country_ISO,value
United States,USA,45.50
China,CHN,28.75
United Kingdom,GBR,22.30
Russia,RUS,18.90
France,FRA,12.45
...
```

**Value Interpretation**: Probability per 100 articles. For example, a value of 45.50 means the country appears in approximately 45.5 out of every 100 news articles.

## How It Works

1. **Scraping**: 
   - Crawls multiple news sources using Scrapy
   - Extracts headlines using CSS selectors
   - Follows links to discover more articles
   - Respects robots.txt and rate limits

2. **Country Detection**:
   - Matches 195+ countries and territories
   - Recognizes common aliases (UK, USA, etc.)
   - Detects demonyms (Japanese, British, etc.)
   - Uses word boundary matching to avoid false positives

3. **Probability Calculation**:
   - Counts mentions per country
   - Calculates: (mentions / total articles) × 100
   - Outputs probability per 100 articles

4. **Append Mode**:
   - Existing titles.json is preserved
   - New scrapes add to the existing data
   - Allows incremental data collection

## Tips & Recommendations

### For Best Results
- **Sample Size**: Use 200-500 articles for reliable statistics
- **Multiple Runs**: Run scraping multiple times to capture time-varying news
- **Source Diversity**: The default sources provide good geographic coverage
- **Incremental Collection**: Scrape 100-200 articles daily over a week for time-averaged results

### Handling Rate Limits
The script includes built-in delays, but if you encounter issues:
- Reduce `--articles` number
- Increase `DOWNLOAD_DELAY` in the spider settings
- Run scraping at different times

### Visualizing Results
Your `country_probabilities.csv` is ready for any choropleth tool that accepts:
- Country names
- ISO 3166-1 alpha-3 codes
- Numerical values

Popular tools:
- Plotly (Python)
- D3.js (JavaScript)
- Tableau
- Datawrapper
- Your existing visualization program!

## Troubleshooting

### "No titles found"
- Some sites may block scrapers or change their HTML structure
- Try adjusting CSS selectors in `NEWS_SOURCES`
- Check your internet connection
- Some sites require JavaScript (Scrapy doesn't execute JS by default)

### Low article count
- Increase `--articles` parameter
- Add more news sources to `NEWS_SOURCES`
- Some sites have fewer links to follow

### Country not detected
- Check if aliases are included in `COUNTRY_DATA`
- Verify the country name spelling in news titles
- The script uses word boundary matching (whole words only)

## Example Workflow

Complete workflow for a comprehensive analysis:

```bash
# Day 1: Initial collection
python news_country_crawler.py --mode scrape --articles 200

# Day 2: Add more data
python news_country_crawler.py --mode scrape --articles 200

# Day 3: Add more data
python news_country_crawler.py --mode scrape --articles 200

# Day 4: Process all collected data
python news_country_crawler.py --mode calculate

# Result: Analysis based on 600 articles collected over 3 days
```

## Technical Details

- **Framework**: Scrapy 2.x
- **Python**: 3.7+
- **Dependencies**: scrapy only
- **Rate Limiting**: 1 second delay between requests
- **Concurrent Requests**: 4 (configurable)
- **Respects**: robots.txt

## License

This script is provided as-is for educational and research purposes.

## Contributing

To add news sources:
1. Find the site's article title CSS selector
2. Add to `NEWS_SOURCES` list
3. Test with a small scrape first

## Support

For issues:
1. Check your CSS selectors are still valid (websites change)
2. Verify scrapy is installed correctly
3. Try with fewer articles first
4. Check internet connectivity

---

**Happy Mapping! 🗺️**
