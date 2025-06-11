# ==============================================================================
# File: processing/web_scraper.py
# ==============================================================================

import re
from typing import Dict, List, Optional
import httpx
from bs4 import BeautifulSoup

# A robust User-Agent to mimic a real browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
}

# Max characters to send to the LLM to prevent overly large/expensive payloads
MAX_LLM_CONTENT_LENGTH = 16000

async def scrape_homepage_content(url: str) -> Dict:
    """
    Asynchronously scrapes text, metadata, and contact info from a website's homepage.
    It attempts to clean the HTML to provide the most relevant content for analysis.
    """
    print(f"Starting to scrape: {url}")
    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0, headers=HEADERS) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            
            soup = BeautifulSoup(response.text, 'lxml') # Use 'lxml' as it's faster and more lenient
            
            # --- 1. Extract Metadata ---
            title = soup.title.string.strip() if soup.title else ''
            meta_desc_tag = soup.find('meta', attrs={'name': re.compile(r'description', re.I)})
            description = meta_desc_tag.get('content', '').strip() if meta_desc_tag else ''
            
            # --- 2. Extract and Clean Main Content ---
            # Decompose (remove) irrelevant tags to clean up the content
            for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
                tag.decompose()

            # Attempt to find the most relevant content block
            main_content_tag = soup.find('main') or \
                               soup.find('article') or \
                               soup.find('div', class_=re.compile(r'content|main|post', re.I)) or \
                               soup.body # Fallback to the entire body

            if main_content_tag:
                main_content = main_content_tag.get_text(separator='\n', strip=True)
                # Replace multiple newlines with a single one for cleaner text
                main_content = re.sub(r'\n{3,}', '\n\n', main_content)
            else:
                main_content = "" # Should not happen if soup.body is a fallback

            # --- 3. Extract Contact Information ---
            body_text = soup.get_text() # Get all text for contact info search
            
            # Find unique emails
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = list(set(re.findall(email_pattern, body_text)))
            
            # Find unique phone numbers (basic pattern)
            # This pattern is simplified to avoid false positives with version numbers etc.
            phone_pattern = r'(\(?\+?\d{1,3}\)?[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
            phones = list(set(re.findall(phone_pattern, body_text)))
            
            # Find social media links
            social_links = {}
            social_patterns = {
                'linkedin': r'linkedin\.com/company/[a-zA-Z0-9_-]+',
                'twitter': r'(twitter|x)\.com/[a-zA-Z0-9_]+',
                'facebook': r'facebook\.com/[a-zA-Z0-9_.-]+',
                'instagram': r'instagram\.com/[a-zA-Z0-9_.]+'
            }
            for platform, pattern in social_patterns.items():
                match = re.search(f'https?://(www\.)?{pattern}', response.text, re.I)
                if match and platform not in social_links:
                    social_links[platform] = match.group(0)

            print(f"Successfully scraped content from: {url}")
            
            return {
                "url": url,
                "main_content": main_content[:MAX_LLM_CONTENT_LENGTH],
                "metadata": {
                    "title": title,
                    "description": description,
                },
                "contact_info": {
                    "emails": emails,
                    "phones": phones,
                    "social_links": social_links
                }
            }

        except httpx.RequestError as exc:
            print(f"HTTP Request failed for {url}: {exc}")
            raise Exception(f"Failed to fetch the URL. The website may be down or blocking requests.")
        except Exception as exc:
            print(f"An unexpected error occurred during scraping of {url}: {exc}")
            raise Exception(f"An unexpected error occurred while processing the website's content.")