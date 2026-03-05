# Quick Start Guide

## 5-Minute Setup

### Step 1: Install Scrapy
```bash
pip install scrapy --break-system-packages
```

### Step 2: Test the Setup
```bash
python test_country_detection.py
```

You should see output showing country detection working correctly.

### Step 3: Run Your First Crawl
```bash
python news_country_crawler.py --articles 50
```

This will:
1. Scrape ~50 news article titles
2. Save them to `titles.json`
3. Calculate country probabilities
4. Generate `country_probabilities.csv`

### Step 4: Check Your Results
```bash
cat country_probabilities.csv
```

You should see a CSV file with columns: `country,country_ISO,value`

## Common Commands

### Collect More Data
```bash
# Scrape 200 articles
python news_country_crawler.py --mode scrape --articles 200

# Scrape 200 more (appends to existing data!)
python news_country_crawler.py --mode scrape --articles 200

# Calculate probabilities from all collected data
python news_country_crawler.py --mode calculate
```

### Recommended Workflow
```bash
# Day 1: Collect initial data
python news_country_crawler.py --mode scrape --articles 200

# Day 2: Add more data
python news_country_crawler.py --mode scrape --articles 200

# Day 3: Add more data
python news_country_crawler.py --mode scrape --articles 200

# Day 4: Calculate results from all 600 articles
python news_country_crawler.py --mode calculate
```

## What You Get

### titles.json
Contains all scraped article titles:
```json
[
  {
    "title": "UK Prime Minister meets Japanese officials",
    "source": "bbc.com",
    "url": "https://www.bbc.com/news/world"
  }
]
```

### country_probabilities.csv
Ready for your choropleth visualization:
```csv
country,country_ISO,value
United States,USA,45.50
China,CHN,28.75
United Kingdom,GBR,22.30
```

The `value` column represents appearances per 100 articles.

## Troubleshooting

### "No titles found"
- Check your internet connection
- Try with fewer articles: `--articles 20`
- Some news sites may block scrapers

### Very low article count
- Increase the number: `--articles 500`
- Wait and try again (some sites rate-limit)

### Country not detected
- Check if it's in the aliases (see COUNTRY_DATA in the script)
- Make sure you're using common news sources

## Next Steps

1. **Customize sources**: Edit `NEWS_SOURCES` in the script
2. **Add countries**: Edit `COUNTRY_DATA` for missing aliases
3. **Visualize**: Load `country_probabilities.csv` into your choropleth tool
4. **Share**: The CSV is ready for any mapping software!

## Full Documentation

See `README.md` for complete documentation.
See `config_examples.txt` for advanced configuration.

---

**Happy mapping! 🗺️**
