#!/usr/bin/env env python3
"""
News Country Crawler - Analyzes country mentions in news article titles
Generates a choropleth-ready CSV with country appearance probabilities
"""

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
import json
import csv
import re
from pathlib import Path
from collections import Counter
import argparse
import random


# Configuration: News sources to crawl
NEWS_SOURCES = [
    {
        'name': 'CNN',
        'start_urls': [
            'https://www.cnn.com/',
            'https://www.cnn.com/world',
            'https://www.cnn.com/politics'
        ],
        'allowed_domains': ['cnn.com'],
        'title_selector': 'span.container__headline-text::text, h3.container__headline-text::text, h2::text'
    },
    {
        'name': 'Fox News',
        'start_urls': [
            'https://www.foxnews.com/',
            'https://www.foxnews.com/world',
            'https://www.foxnews.com/politics'
        ],
        'allowed_domains': ['foxnews.com'],
        'title_selector': 'h2.title::text, h3.title::text, h4.title::text'
    },
    {
        'name': 'The New York Times',
        'start_urls': [
            'https://www.nytimes.com/',
            'https://www.nytimes.com/section/world'
        ],
        'allowed_domains': ['nytimes.com'],
        'title_selector': 'h3::text, h2::text, .indicate-hover::text'
    },
    {
        'name': 'NPR',
        'start_urls': [
            'https://www.npr.org/',
            'https://www.npr.org/sections/world/',
            'https://www.npr.org/sections/politics/'
        ],
        'allowed_domains': ['npr.org'],
        'title_selector': 'h2.title::text, h3.title::text, h2::text'
    }
]


# Comprehensive country data with aliases and ISO codes
COUNTRY_DATA = {
    'Afghanistan': {'iso': 'AFG', 'aliases': ['Afghanistan', 'Afghan']},
    'Albania': {'iso': 'ALB', 'aliases': ['Albania', 'Albanian']},
    'Algeria': {'iso': 'DZA', 'aliases': ['Algeria', 'Algerian']},
    'Andorra': {'iso': 'AND', 'aliases': ['Andorra', 'Andorran']},
    'Angola': {'iso': 'AGO', 'aliases': ['Angola', 'Angolan']},
    'Antigua and Barbuda': {'iso': 'ATG', 'aliases': ['Antigua and Barbuda', 'Antigua', 'Barbuda']},
    'Argentina': {'iso': 'ARG', 'aliases': ['Argentina', 'Argentine', 'Argentinian']},
    'Armenia': {'iso': 'ARM', 'aliases': ['Armenia', 'Armenian']},
    'Australia': {'iso': 'AUS', 'aliases': ['Australia', 'Australian', 'Aussie']},
    'Austria': {'iso': 'AUT', 'aliases': ['Austria', 'Austrian']},
    'Azerbaijan': {'iso': 'AZE', 'aliases': ['Azerbaijan', 'Azerbaijani', 'Azeri']},
    'Bahamas': {'iso': 'BHS', 'aliases': ['Bahamas', 'Bahamian']},
    'Bahrain': {'iso': 'BHR', 'aliases': ['Bahrain', 'Bahraini']},
    'Bangladesh': {'iso': 'BGD', 'aliases': ['Bangladesh', 'Bangladeshi', 'Bengali']},
    'Barbados': {'iso': 'BRB', 'aliases': ['Barbados', 'Barbadian', 'Bajan']},
    'Belarus': {'iso': 'BLR', 'aliases': ['Belarus', 'Belarusian', 'Belarussian']},
    'Belgium': {'iso': 'BEL', 'aliases': ['Belgium', 'Belgian']},
    'Belize': {'iso': 'BLZ', 'aliases': ['Belize', 'Belizean']},
    'Benin': {'iso': 'BEN', 'aliases': ['Benin', 'Beninese']},
    'Bhutan': {'iso': 'BTN', 'aliases': ['Bhutan', 'Bhutanese']},
    'Bolivia': {'iso': 'BOL', 'aliases': ['Bolivia', 'Bolivian']},
    'Bosnia and Herzegovina': {'iso': 'BIH', 'aliases': ['Bosnia and Herzegovina', 'Bosnia', 'Bosnian']},
    'Botswana': {'iso': 'BWA', 'aliases': ['Botswana', 'Botswanan']},
    'Brazil': {'iso': 'BRA', 'aliases': ['Brazil', 'Brazilian']},
    'Brunei': {'iso': 'BRN', 'aliases': ['Brunei', 'Bruneian']},
    'Bulgaria': {'iso': 'BGR', 'aliases': ['Bulgaria', 'Bulgarian']},
    'Burkina Faso': {'iso': 'BFA', 'aliases': ['Burkina Faso', 'Burkinabe']},
    'Burundi': {'iso': 'BDI', 'aliases': ['Burundi', 'Burundian']},
    'Cambodia': {'iso': 'KHM', 'aliases': ['Cambodia', 'Cambodian']},
    'Cameroon': {'iso': 'CMR', 'aliases': ['Cameroon', 'Cameroonian']},
    'Canada': {'iso': 'CAN', 'aliases': ['Canada', 'Canadian']},
    'Cape Verde': {'iso': 'CPV', 'aliases': ['Cape Verde', 'Cabo Verde', 'Cape Verdean']},
    'Central African Republic': {'iso': 'CAF', 'aliases': ['Central African Republic', 'CAR']},
    'Chad': {'iso': 'TCD', 'aliases': ['Chad', 'Chadian']},
    'Chile': {'iso': 'CHL', 'aliases': ['Chile', 'Chilean']},
    'China': {'iso': 'CHN', 'aliases': ['China', 'Chinese', 'PRC', "People's Republic of China"]},
    'Colombia': {'iso': 'COL', 'aliases': ['Colombia', 'Colombian']},
    'Comoros': {'iso': 'COM', 'aliases': ['Comoros', 'Comorian']},
    'Congo': {'iso': 'COG', 'aliases': ['Congo', 'Republic of the Congo', 'Congo-Brazzaville']},
    'Costa Rica': {'iso': 'CRI', 'aliases': ['Costa Rica', 'Costa Rican']},
    'Croatia': {'iso': 'HRV', 'aliases': ['Croatia', 'Croatian']},
    'Cuba': {'iso': 'CUB', 'aliases': ['Cuba', 'Cuban']},
    'Cyprus': {'iso': 'CYP', 'aliases': ['Cyprus', 'Cypriot']},
    'Czech Republic': {'iso': 'CZE', 'aliases': ['Czech Republic', 'Czechia', 'Czech']},
    'Democratic Republic of the Congo': {'iso': 'COD', 'aliases': ['Democratic Republic of the Congo', 'DRC', 'DR Congo', 'Congo-Kinshasa']},
    'Denmark': {'iso': 'DNK', 'aliases': ['Denmark', 'Danish']},
    'Djibouti': {'iso': 'DJI', 'aliases': ['Djibouti', 'Djiboutian']},
    'Dominica': {'iso': 'DMA', 'aliases': ['Dominica', 'Dominican']},
    'Dominican Republic': {'iso': 'DOM', 'aliases': ['Dominican Republic']},
    'East Timor': {'iso': 'TLS', 'aliases': ['East Timor', 'Timor-Leste', 'Timorese']},
    'Ecuador': {'iso': 'ECU', 'aliases': ['Ecuador', 'Ecuadorian', 'Ecuadorean']},
    'Egypt': {'iso': 'EGY', 'aliases': ['Egypt', 'Egyptian']},
    'El Salvador': {'iso': 'SLV', 'aliases': ['El Salvador', 'Salvadoran']},
    'Equatorial Guinea': {'iso': 'GNQ', 'aliases': ['Equatorial Guinea', 'Equatoguinean']},
    'Eritrea': {'iso': 'ERI', 'aliases': ['Eritrea', 'Eritrean']},
    'Estonia': {'iso': 'EST', 'aliases': ['Estonia', 'Estonian']},
    'Eswatini': {'iso': 'SWZ', 'aliases': ['Eswatini', 'Swaziland', 'Swazi']},
    'Ethiopia': {'iso': 'ETH', 'aliases': ['Ethiopia', 'Ethiopian']},
    'Fiji': {'iso': 'FJI', 'aliases': ['Fiji', 'Fijian']},
    'Finland': {'iso': 'FIN', 'aliases': ['Finland', 'Finnish']},
    'France': {'iso': 'FRA', 'aliases': ['France', 'French']},
    'Gabon': {'iso': 'GAB', 'aliases': ['Gabon', 'Gabonese']},
    'Gambia': {'iso': 'GMB', 'aliases': ['Gambia', 'Gambian']},
    'Georgia': {'iso': 'GEO', 'aliases': ['Georgia', 'Georgian']},
    'Germany': {'iso': 'DEU', 'aliases': ['Germany', 'German']},
    'Ghana': {'iso': 'GHA', 'aliases': ['Ghana', 'Ghanaian']},
    'Greece': {'iso': 'GRC', 'aliases': ['Greece', 'Greek']},
    'Grenada': {'iso': 'GRD', 'aliases': ['Grenada', 'Grenadian']},
    'Guatemala': {'iso': 'GTM', 'aliases': ['Guatemala', 'Guatemalan']},
    'Guinea': {'iso': 'GIN', 'aliases': ['Guinea', 'Guinean']},
    'Guinea-Bissau': {'iso': 'GNB', 'aliases': ['Guinea-Bissau', 'Guinea Bissau']},
    'Guyana': {'iso': 'GUY', 'aliases': ['Guyana', 'Guyanese']},
    'Haiti': {'iso': 'HTI', 'aliases': ['Haiti', 'Haitian']},
    'Honduras': {'iso': 'HND', 'aliases': ['Honduras', 'Honduran']},
    'Hungary': {'iso': 'HUN', 'aliases': ['Hungary', 'Hungarian']},
    'Iceland': {'iso': 'ISL', 'aliases': ['Iceland', 'Icelandic']},
    'India': {'iso': 'IND', 'aliases': ['India', 'Indian']},
    'Indonesia': {'iso': 'IDN', 'aliases': ['Indonesia', 'Indonesian']},
    'Iran': {'iso': 'IRN', 'aliases': ['Iran', 'Iranian', 'Persia', 'Persian']},
    'Iraq': {'iso': 'IRQ', 'aliases': ['Iraq', 'Iraqi']},
    'Ireland': {'iso': 'IRL', 'aliases': ['Ireland', 'Irish']},
    'Israel': {'iso': 'ISR', 'aliases': ['Israel', 'Israeli']},
    'Italy': {'iso': 'ITA', 'aliases': ['Italy', 'Italian']},
    'Ivory Coast': {'iso': 'CIV', 'aliases': ['Ivory Coast', 'Côte d\'Ivoire', 'Cote d\'Ivoire', 'Ivorian']},
    'Jamaica': {'iso': 'JAM', 'aliases': ['Jamaica', 'Jamaican']},
    'Japan': {'iso': 'JPN', 'aliases': ['Japan', 'Japanese']},
    'Jordan': {'iso': 'JOR', 'aliases': ['Jordan', 'Jordanian']},
    'Kazakhstan': {'iso': 'KAZ', 'aliases': ['Kazakhstan', 'Kazakh', 'Kazakhstani']},
    'Kenya': {'iso': 'KEN', 'aliases': ['Kenya', 'Kenyan']},
    'Kiribati': {'iso': 'KIR', 'aliases': ['Kiribati']},
    'Kosovo': {'iso': 'XKX', 'aliases': ['Kosovo', 'Kosovar']},
    'Kuwait': {'iso': 'KWT', 'aliases': ['Kuwait', 'Kuwaiti']},
    'Kyrgyzstan': {'iso': 'KGZ', 'aliases': ['Kyrgyzstan', 'Kyrgyz']},
    'Laos': {'iso': 'LAO', 'aliases': ['Laos', 'Lao', 'Laotian']},
    'Latvia': {'iso': 'LVA', 'aliases': ['Latvia', 'Latvian']},
    'Lebanon': {'iso': 'LBN', 'aliases': ['Lebanon', 'Lebanese']},
    'Lesotho': {'iso': 'LSO', 'aliases': ['Lesotho', 'Basotho']},
    'Liberia': {'iso': 'LBR', 'aliases': ['Liberia', 'Liberian']},
    'Libya': {'iso': 'LBY', 'aliases': ['Libya', 'Libyan']},
    'Liechtenstein': {'iso': 'LIE', 'aliases': ['Liechtenstein']},
    'Lithuania': {'iso': 'LTU', 'aliases': ['Lithuania', 'Lithuanian']},
    'Luxembourg': {'iso': 'LUX', 'aliases': ['Luxembourg', 'Luxembourgish']},
    'Madagascar': {'iso': 'MDG', 'aliases': ['Madagascar', 'Malagasy']},
    'Malawi': {'iso': 'MWI', 'aliases': ['Malawi', 'Malawian']},
    'Malaysia': {'iso': 'MYS', 'aliases': ['Malaysia', 'Malaysian']},
    'Maldives': {'iso': 'MDV', 'aliases': ['Maldives', 'Maldivian']},
    'Mali': {'iso': 'MLI', 'aliases': ['Mali', 'Malian']},
    'Malta': {'iso': 'MLT', 'aliases': ['Malta', 'Maltese']},
    'Marshall Islands': {'iso': 'MHL', 'aliases': ['Marshall Islands', 'Marshallese']},
    'Mauritania': {'iso': 'MRT', 'aliases': ['Mauritania', 'Mauritanian']},
    'Mauritius': {'iso': 'MUS', 'aliases': ['Mauritius', 'Mauritian']},
    'Mexico': {'iso': 'MEX', 'aliases': ['Mexico', 'Mexican']},
    'Micronesia': {'iso': 'FSM', 'aliases': ['Micronesia', 'Micronesian']},
    'Moldova': {'iso': 'MDA', 'aliases': ['Moldova', 'Moldovan']},
    'Monaco': {'iso': 'MCO', 'aliases': ['Monaco', 'Monégasque', 'Monacan']},
    'Mongolia': {'iso': 'MNG', 'aliases': ['Mongolia', 'Mongolian']},
    'Montenegro': {'iso': 'MNE', 'aliases': ['Montenegro', 'Montenegrin']},
    'Morocco': {'iso': 'MAR', 'aliases': ['Morocco', 'Moroccan']},
    'Mozambique': {'iso': 'MOZ', 'aliases': ['Mozambique', 'Mozambican']},
    'Myanmar': {'iso': 'MMR', 'aliases': ['Myanmar', 'Burma', 'Burmese']},
    'Namibia': {'iso': 'NAM', 'aliases': ['Namibia', 'Namibian']},
    'Nauru': {'iso': 'NRU', 'aliases': ['Nauru', 'Nauruan']},
    'Nepal': {'iso': 'NPL', 'aliases': ['Nepal', 'Nepali', 'Nepalese']},
    'Netherlands': {'iso': 'NLD', 'aliases': ['Netherlands', 'Dutch', 'Holland']},
    'New Zealand': {'iso': 'NZL', 'aliases': ['New Zealand', 'NZ', 'Kiwi']},
    'Nicaragua': {'iso': 'NIC', 'aliases': ['Nicaragua', 'Nicaraguan']},
    'Niger': {'iso': 'NER', 'aliases': ['Niger', 'Nigerien']},
    'Nigeria': {'iso': 'NGA', 'aliases': ['Nigeria', 'Nigerian']},
    'North Korea': {'iso': 'PRK', 'aliases': ['North Korea', 'DPRK', 'Democratic People\'s Republic of Korea', 'North Korean']},
    'North Macedonia': {'iso': 'MKD', 'aliases': ['North Macedonia', 'Macedonia', 'Macedonian']},
    'Norway': {'iso': 'NOR', 'aliases': ['Norway', 'Norwegian']},
    'Oman': {'iso': 'OMN', 'aliases': ['Oman', 'Omani']},
    'Pakistan': {'iso': 'PAK', 'aliases': ['Pakistan', 'Pakistani']},
    'Palau': {'iso': 'PLW', 'aliases': ['Palau', 'Palauan']},
    'Palestine': {'iso': 'PSE', 'aliases': ['Palestine', 'Palestinian', 'Gaza', 'West Bank']},
    'Panama': {'iso': 'PAN', 'aliases': ['Panama', 'Panamanian']},
    'Papua New Guinea': {'iso': 'PNG', 'aliases': ['Papua New Guinea', 'PNG']},
    'Paraguay': {'iso': 'PRY', 'aliases': ['Paraguay', 'Paraguayan']},
    'Peru': {'iso': 'PER', 'aliases': ['Peru', 'Peruvian']},
    'Philippines': {'iso': 'PHL', 'aliases': ['Philippines', 'Filipino', 'Filipina', 'Philippine']},
    'Poland': {'iso': 'POL', 'aliases': ['Poland', 'Polish']},
    'Portugal': {'iso': 'PRT', 'aliases': ['Portugal', 'Portuguese']},
    'Qatar': {'iso': 'QAT', 'aliases': ['Qatar', 'Qatari']},
    'Romania': {'iso': 'ROU', 'aliases': ['Romania', 'Romanian']},
    'Russia': {'iso': 'RUS', 'aliases': ['Russia', 'Russian', 'Soviet', 'USSR', 'Kremlin']},
    'Rwanda': {'iso': 'RWA', 'aliases': ['Rwanda', 'Rwandan']},
    'Saint Kitts and Nevis': {'iso': 'KNA', 'aliases': ['Saint Kitts and Nevis', 'St Kitts']},
    'Saint Lucia': {'iso': 'LCA', 'aliases': ['Saint Lucia', 'St Lucia']},
    'Saint Vincent and the Grenadines': {'iso': 'VCT', 'aliases': ['Saint Vincent and the Grenadines', 'St Vincent']},
    'Samoa': {'iso': 'WSM', 'aliases': ['Samoa', 'Samoan']},
    'San Marino': {'iso': 'SMR', 'aliases': ['San Marino']},
    'Sao Tome and Principe': {'iso': 'STP', 'aliases': ['Sao Tome and Principe', 'São Tomé']},
    'Saudi Arabia': {'iso': 'SAU', 'aliases': ['Saudi Arabia', 'Saudi', 'Kingdom of Saudi Arabia']},
    'Senegal': {'iso': 'SEN', 'aliases': ['Senegal', 'Senegalese']},
    'Serbia': {'iso': 'SRB', 'aliases': ['Serbia', 'Serbian']},
    'Seychelles': {'iso': 'SYC', 'aliases': ['Seychelles', 'Seychellois']},
    'Sierra Leone': {'iso': 'SLE', 'aliases': ['Sierra Leone', 'Sierra Leonean']},
    'Singapore': {'iso': 'SGP', 'aliases': ['Singapore', 'Singaporean']},
    'Slovakia': {'iso': 'SVK', 'aliases': ['Slovakia', 'Slovak']},
    'Slovenia': {'iso': 'SVN', 'aliases': ['Slovenia', 'Slovenian', 'Slovene']},
    'Solomon Islands': {'iso': 'SLB', 'aliases': ['Solomon Islands']},
    'Somalia': {'iso': 'SOM', 'aliases': ['Somalia', 'Somali', 'Somalian']},
    'South Africa': {'iso': 'ZAF', 'aliases': ['South Africa', 'South African']},
    'South Korea': {'iso': 'KOR', 'aliases': ['South Korea', 'Korea', 'ROK', 'Republic of Korea', 'Korean']},
    'South Sudan': {'iso': 'SSD', 'aliases': ['South Sudan', 'South Sudanese']},
    'Spain': {'iso': 'ESP', 'aliases': ['Spain', 'Spanish']},
    'Sri Lanka': {'iso': 'LKA', 'aliases': ['Sri Lanka', 'Sri Lankan', 'Ceylon']},
    'Sudan': {'iso': 'SDN', 'aliases': ['Sudan', 'Sudanese']},
    'Suriname': {'iso': 'SUR', 'aliases': ['Suriname', 'Surinamese']},
    'Sweden': {'iso': 'SWE', 'aliases': ['Sweden', 'Swedish']},
    'Switzerland': {'iso': 'CHE', 'aliases': ['Switzerland', 'Swiss']},
    'Syria': {'iso': 'SYR', 'aliases': ['Syria', 'Syrian']},
    'Taiwan': {'iso': 'TWN', 'aliases': ['Taiwan', 'Taiwanese', 'ROC', 'Republic of China']},
    'Tajikistan': {'iso': 'TJK', 'aliases': ['Tajikistan', 'Tajik']},
    'Tanzania': {'iso': 'TZA', 'aliases': ['Tanzania', 'Tanzanian']},
    'Thailand': {'iso': 'THA', 'aliases': ['Thailand', 'Thai', 'Siam']},
    'Togo': {'iso': 'TGO', 'aliases': ['Togo', 'Togolese']},
    'Tonga': {'iso': 'TON', 'aliases': ['Tonga', 'Tongan']},
    'Trinidad and Tobago': {'iso': 'TTO', 'aliases': ['Trinidad and Tobago', 'Trinidad', 'Tobago', 'Trinidadian']},
    'Tunisia': {'iso': 'TUN', 'aliases': ['Tunisia', 'Tunisian']},
    'Turkey': {'iso': 'TUR', 'aliases': ['Turkey', 'Turkish', 'Türkiye']},
    'Turkmenistan': {'iso': 'TKM', 'aliases': ['Turkmenistan', 'Turkmen']},
    'Tuvalu': {'iso': 'TUV', 'aliases': ['Tuvalu', 'Tuvaluan']},
    'Uganda': {'iso': 'UGA', 'aliases': ['Uganda', 'Ugandan']},
    'Ukraine': {'iso': 'UKR', 'aliases': ['Ukraine', 'Ukrainian', 'Kyiv', 'Kiev']},
    'United Arab Emirates': {'iso': 'ARE', 'aliases': ['United Arab Emirates', 'UAE', 'Emirates', 'Emirati']},
    'United Kingdom': {'iso': 'GBR', 'aliases': ['United Kingdom', 'UK', 'Britain', 'British', 'England', 'Scotland', 'Wales', 'Northern Ireland', 'English', 'Scottish', 'Welsh']},
    'United States': {'iso': 'USA', 'aliases': ['United States', 'USA', 'US', 'America', 'American']},
    'Uruguay': {'iso': 'URY', 'aliases': ['Uruguay', 'Uruguayan']},
    'Uzbekistan': {'iso': 'UZB', 'aliases': ['Uzbekistan', 'Uzbek']},
    'Vanuatu': {'iso': 'VUT', 'aliases': ['Vanuatu', 'Ni-Vanuatu']},
    'Vatican City': {'iso': 'VAT', 'aliases': ['Vatican', 'Vatican City', 'Holy See']},
    'Venezuela': {'iso': 'VEN', 'aliases': ['Venezuela', 'Venezuelan']},
    'Vietnam': {'iso': 'VNM', 'aliases': ['Vietnam', 'Vietnamese', 'Viet Nam']},
    'Yemen': {'iso': 'YEM', 'aliases': ['Yemen', 'Yemeni']},
    'Zambia': {'iso': 'ZMB', 'aliases': ['Zambia', 'Zambian']},
    'Zimbabwe': {'iso': 'ZWE', 'aliases': ['Zimbabwe', 'Zimbabwean']},
}


class NewsSpider(scrapy.Spider):
    """Spider to crawl news titles from multiple sources"""
    name = 'news_spider'
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 1,
        'COOKIES_ENABLED': False,
        'TELNETCONSOLE_ENABLED': False,
        'LOG_LEVEL': 'INFO',
    }
    
    def __init__(self, max_articles=100, *args, **kwargs):
        super(NewsSpider, self).__init__(*args, **kwargs)
        self.max_articles = int(max_articles)
        self.collected_titles = []
        self.titles_per_source = max(10, self.max_articles // len(NEWS_SOURCES))
        
        # Setup spider with news sources
        self.start_urls = []
        self.allowed_domains = []
        self.source_selectors = {}
        
        for source in NEWS_SOURCES:
            self.start_urls.extend(source['start_urls'])
            self.allowed_domains.extend(source['allowed_domains'])
            for domain in source['allowed_domains']:
                self.source_selectors[domain] = source['title_selector']
    
    def parse(self, response):
        """Extract titles from news pages"""
        # Determine which selector to use based on domain
        domain = response.url.split('/')[2].replace('www.', '')
        selector = None
        
        for allowed_domain in self.source_selectors:
            if allowed_domain in domain:
                selector = self.source_selectors[allowed_domain]
                break
        
        if not selector:
            self.logger.warning(f"No selector found for domain: {domain}")
            return
        
        # Extract titles
        titles = response.css(selector).getall()
        
        for title in titles:
            title = title.strip()
            if title and len(title) > 10:  # Filter out very short text
                self.collected_titles.append({
                    'title': title,
                    'source': domain,
                    'url': response.url
                })
                
                if len(self.collected_titles) >= self.max_articles:
                    return
        
        # Follow links to get more articles (limited depth)
        if len(self.collected_titles) < self.max_articles:
            links = response.css('a::attr(href)').getall()
            # Randomly sample some links to follow
            links = random.sample(links, min(5, len(links)))
            
            for link in links:
                if len(self.collected_titles) >= self.max_articles:
                    break
                yield response.follow(link, callback=self.parse)
    
    def closed(self, reason):
        """Save collected titles when spider closes"""
        self.logger.info(f"Spider closed. Collected {len(self.collected_titles)} titles")
        # Attempt to save collected titles to the provided output file (if any)
        output_file = getattr(self, 'output_file', 'titles.json')
        try:
            existing = []
            out_path = Path(output_file)
            if out_path.exists():
                with open(out_path, 'r', encoding='utf-8') as f:
                    try:
                        existing = json.load(f)
                    except json.JSONDecodeError:
                        existing = []

            # Merge while avoiding duplicates (by title text)
            seen = set([t.get('title', '').strip().lower() for t in existing if t.get('title')])
            new_items = []
            for item in self.collected_titles:
                title_text = item.get('title', '').strip()
                if not title_text:
                    continue
                if title_text.lower() not in seen:
                    seen.add(title_text.lower())
                    new_items.append(item)

            merged = existing + new_items

            # Write merged list back to file
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Saved {len(new_items)} new titles to {output_file} (total {len(merged)})")
        except Exception as e:
            self.logger.error(f"Failed to save titles to {output_file}: {e}")


def scrape_news_titles(max_articles=100, output_file='titles.json'):
    """Run the scraper to collect news titles"""
    print(f"Starting news scraper (target: {max_articles} articles)...")
    
    # Load existing titles if file exists
    existing_titles = []
    if Path(output_file).exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            try:
                existing_titles = json.load(f)
                print(f"Found {len(existing_titles)} existing titles in {output_file}")
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {output_file}, starting fresh")
    
    # Run spider
    process = CrawlerProcess({
        'LOG_LEVEL': 'INFO',
    })
    
    spider = NewsSpider
    # Pass the output filename into the spider so it can persist titles on close
    process.crawl(spider, max_articles=max_articles, output_file=output_file)
    process.start()
    
    # Get collected titles from the spider (need to access after crawl)
    # Note: Due to Scrapy's architecture, we'll save during the spider's closed event
    # For now, we'll use a simpler approach with a temporary file
    
    print(f"Scraping completed. Processing results...")
    return existing_titles


def detect_countries_in_title(title):
    """
    Detect country mentions in a title using comprehensive alias matching
    Returns list of country names found
    """
    title_lower = title.lower()
    found_countries = []
    
    for country, data in COUNTRY_DATA.items():
        for alias in data['aliases']:
            # Use word boundary matching to avoid false positives
            # e.g., "Americans" contains "America" but we still want to match it
            pattern = r'\b' + re.escape(alias.lower()) + r's?\b'
            if re.search(pattern, title_lower):
                found_countries.append(country)
                break  # Count each country only once per title
    
    return found_countries


def calculate_country_probabilities(titles_file='titles.json', output_csv='country_probabilities.csv'):
    """
    Calculate probability of each country appearing in news titles
    Output CSV format: country,country_ISO,value
    """
    print(f"\nCalculating country probabilities from {titles_file}...")
    
    # Load titles
    if not Path(titles_file).exists():
        print(f"Error: {titles_file} not found. Run scraping first.")
        return
    
    with open(titles_file, 'r', encoding='utf-8') as f:
        titles_data = json.load(f)
    
    if not titles_data:
        print("Error: No titles found in the file.")
        return
    
    total_articles = len(titles_data)
    print(f"Analyzing {total_articles} article titles...")
    
    # Count country mentions
    country_mentions = Counter()
    
    for item in titles_data:
        title = item.get('title', '')
        countries = detect_countries_in_title(title)
        for country in countries:
            country_mentions[country] += 1
    
    print(f"Found mentions of {len(country_mentions)} countries")
    
    # Calculate probabilities and prepare CSV data
    csv_data = []
    for country, data in COUNTRY_DATA.items():
        count = country_mentions.get(country, 0)
        probability = (count / total_articles) * 100  # Per 100 articles
        csv_data.append({
            'country': country,
            'country_ISO': data['iso'],
            'value': round(probability, 2)
        })
    
    # Sort by probability (descending)
    csv_data.sort(key=lambda x: x['value'], reverse=True)
    
    # Write to CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['country', 'country_ISO', 'value'])
        writer.writeheader()
        writer.writerows(csv_data)
    
    print(f"\n✓ Results saved to {output_csv}")
    
    # Print top 10 countries
    print("\nTop 10 countries by news appearance probability:")
    for i, item in enumerate(csv_data[:10], 1):
        print(f"{i:2d}. {item['country']:30s} {item['value']:6.2f}% (ISO: {item['country_ISO']})")
    
    return csv_data


def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(
        description='News Country Crawler - Analyze country mentions in news titles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run both scraping and calculation
  python news_country_crawler.py --mode both --articles 200
  
  # Only scrape news (saves to titles.json)
  python news_country_crawler.py --mode scrape --articles 500
  
  # Only calculate from existing titles.json
  python news_country_crawler.py --mode calculate
  
  # Custom file names
  python news_country_crawler.py --mode both --titles my_titles.json --output my_results.csv
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['scrape', 'calculate', 'both'],
        default='both',
        help='Operation mode: scrape only, calculate only, or both (default: both)'
    )
    
    parser.add_argument(
        '--articles',
        type=int,
        default=100,
        help='Number of articles to scrape (default: 100, recommended: 100-1000)'
    )
    
    parser.add_argument(
        '--titles',
        default='titles.json',
        help='Path to titles JSON file (default: titles.json)'
    )
    
    parser.add_argument(
        '--output',
        default='country_probabilities.csv',
        help='Path to output CSV file (default: country_probabilities.csv)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("News Country Crawler")
    print("=" * 70)
    
    # Execute based on mode
    if args.mode in ['scrape', 'both']:
        scrape_news_titles(max_articles=args.articles, output_file=args.titles)
    
    if args.mode in ['calculate', 'both']:
        calculate_country_probabilities(titles_file=args.titles, output_csv=args.output)
    
    print("\n" + "=" * 70)
    print("Process completed!")
    print("=" * 70)


if __name__ == '__main__':
    main()
