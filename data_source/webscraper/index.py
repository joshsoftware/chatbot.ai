import requests
from bs4 import BeautifulSoup
import html2text
import json
from urllib.parse import urlparse, urljoin
from datetime import datetime
import os
import re
from collections import deque
from urllib.parse import urlsplit
from dotenv import load_dotenv
load_dotenv()

MAX_PAGES = int (os.getenv('MAX_PAGES'))
MIN_PAGES =  int (os.getenv('MIN_PAGES'))
MAX_PAGES_DEFAULT =  int (os.getenv('MAX_PAGES_DEFAULT'))

DEPTH_MIN =  int (os.getenv('DEPTH_MIN'))
DEPTH_MAX =  int (os.getenv('DEPTH_MAX'))
DEPTH_DEFAULT =  int (os.getenv('DEPTH_DEFAULT'))

class WebCrawler:
    def __init__(self, base_url, depth=DEPTH_DEFAULT, max_pages=MAX_PAGES):
        print(type(depth))
        """
        Initialize the web crawler.
        
        Args:
            base_url (str): The main website URL to start crawling from
            depth (int): How deep to crawl (1-10, where 1 is minimum and 10 is maximum)
            max_pages (int): Maximum number of pages to crawl
        """
        self.validate_base_url(base_url)
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.depth = max(DEPTH_MIN, min(DEPTH_MAX, depth))  # Ensure depth is between 1 and 10
        self.max_pages = max_pages
        self.visited_urls = set()
        self.urls_to_visit = deque([(base_url, 0)])  # Store URLs with their depth
        self.collected_data = []

    def validate_base_url(self, url):
        """
        Validate the base URL and raise an error if it's not valid.
        """
        try:
            result = urlsplit(url)
            if all([result.scheme, result.netloc]):
                return
            else:
                raise ValueError("Invalid base URL provided.")
        except Exception as e:
            raise ValueError("Invalid base URL provided.") from e

    def sanitize_json_value(self, value):
        """
        Sanitize a single value for JSON compatibility.
        
        Args:
            value: Any value that needs to be sanitized
            
        Returns:
            Sanitized value that is JSON-compatible
        """
        if isinstance(value, (int, float, bool)) or value is None:
            return value
        elif isinstance(value, str):
            # Remove null bytes
            value = value.replace('\x00', '')
            # Replace invalid unicode characters
            value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
            # Normalize whitespace
            value = ' '.join(value.split())
            # Handle empty strings
            return value if value else None
        elif isinstance(value, (list, tuple)):
            return [self.sanitize_json_value(item) for item in value]
        elif isinstance(value, dict):
            return {str(k): self.sanitize_json_value(v) for k, v in value.items()}
        else:
            return str(value)

    def sanitize_content(self, content):
        """
        Specifically sanitize content field with additional cleaning steps.
        
        Args:
            content (str): Raw content text
            
        Returns:
            str: Sanitized content text
        """
        if not content:
            return ""
            
        # Remove any potential JSON-breaking characters
        content = content.replace('\\', '\\\\')
        content = content.replace('"', '\\"')
        content = content.replace('\b', '')
        content = content.replace('\f', '')
        content = content.replace('\n', '\\n')
        content = content.replace('\r', '\\r')
        content = content.replace('\t', '\\t')
        
        # Remove any control characters
        content = ''.join(char for char in content if ord(char) >= 32 or char in '\n\r\t')
        
        # Normalize whitespace
        content = ' '.join(content.split())
        
        return content

    def prepare_metadata(self):
        """
        Prepare and sanitize metadata for JSON serialization.
        
        Returns:
            list: Sanitized metadata ready for JSON serialization
        """
        metadata = []
        for item in self.collected_data:
            sanitized_item = {
                'title': self.sanitize_json_value(item.get('title', 'No Title')),
                'url': self.sanitize_json_value(item.get('url', '')),
                'depth': self.sanitize_json_value(item.get('depth', 0)),
                'description': self.sanitize_json_value(item.get('description', '')),
                'keywords': self.sanitize_json_value(item.get('keywords', '')),
                'content': self.sanitize_content(item.get('content', ''))
            }
            metadata.append(sanitized_item)
        
        return metadata
        
    def is_valid_url(self, url):
        """Check if URL is valid and belongs to the same domain."""
        try:
            parsed = urlparse(url)
            return (
                parsed.netloc == self.base_domain and
                not url.endswith(('.pdf', '.jpg', '.png', '.gif', '.jpeg', '.doc', '.docx')) and
                '#' not in url
            )
        except:
            return False

    def clean_text(self, text):
        """Clean the text by removing links, extra spaces, and formatting issues."""
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'(?:[\w-]+/)+[\w-]+(?:\.\w+)?', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = '\n'.join(line.strip() for line in text.split('\n'))
        return text.strip()

    def extract_links(self, soup, current_url, current_depth):
        """
        Extract valid links from the page.
        
        Args:
            soup: BeautifulSoup object
            current_url: The URL being processed
            current_depth: Current depth level
            
        Returns:
            set: Set of (url, new_depth) tuples
        """
        links = set()
        if current_depth >= self.depth:
            return links
            
        for link in soup.find_all('a', href=True):
            url = link['href']
            absolute_url = urljoin(current_url, url)
            if self.is_valid_url(absolute_url):
                links.add((absolute_url, current_depth + 1))
        return links

    def get_page_data(self, url, current_depth):
        """Get data from a single webpage."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.extract()

            # Extract new links with depth
            new_links = self.extract_links(soup, url, current_depth)
            for link, new_depth in new_links:
                if link not in self.visited_urls:
                    self.urls_to_visit.append((link, new_depth))

            # Extract text
            html = str(soup)
            html2text_instance = html2text.HTML2Text()
            html2text_instance.ignore_links = True
            html2text_instance.ignore_images = True
            html2text_instance.ignore_emphasis = True
            html2text_instance.body_width = 0
            text = html2text_instance.handle(html)
            text = self.clean_text(text)

            # Extract metadata
            try:
                page_title = soup.title.string.strip() if soup.title else "No Title"
                page_title = self.clean_text(page_title)
            except:
                page_title = urlparse(url).path[1:].replace("/", "-") or "No Title"

            meta_description = soup.find("meta", attrs={"name": "description"})
            description = self.clean_text(meta_description.get("content")) if meta_description else "No description available"

            meta_keywords = soup.find("meta", attrs={"name": "keywords"})
            keywords = self.clean_text(meta_keywords.get("content")) if meta_keywords else "No keywords available"

            # Return sanitized data
            page_data = {
                'url': url,
                'depth': current_depth,
                'title': page_title,
                'description': description,
                'keywords': keywords,
                'content': text
            }

            return page_data

        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            return None

    def crawl(self):
        """Start the crawling process."""
        while self.urls_to_visit and len(self.visited_urls) < self.max_pages:
            current_url, current_depth = self.urls_to_visit.popleft()
            if current_url in self.visited_urls:
                continue
                
            print(f"\nCrawling {len(self.visited_urls) + 1}/{self.max_pages} (Depth: {current_depth}/{self.depth}): {current_url}")
            page_data = self.get_page_data(current_url, current_depth)
            
            if page_data:
                self.collected_data.append(page_data)
                self.visited_urls.add(current_url)
                print(f"Successfully processed: {current_url}")
            else:
                print(f"Failed to process: {current_url}")

    def save_results(self):
        """Save the crawled data to files."""
        domain = urlparse(self.base_url).netloc
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = "scrap_dump/" + domain
        
        # Create the output directory
        os.makedirs(output_dir, exist_ok=True)

        # Prepare sanitized metadata
        metadata = self.prepare_metadata()
        
        # Save metadata
        metadata_filename = os.path.join(output_dir, 'Result_'+domain+'.json')
        with open(metadata_filename, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)

        # Save content = Code to save data in text format (if req. uncomment the code) 
        # content_filename = os.path.join(output_dir, 'clean_content.txt')
        # with open(content_filename, 'w', encoding='utf-8') as f:
        #     for item in metadata:  # Use sanitized metadata
        #         f.write(f"\n{'='*80}\n")
        #         f.write(f"URL: {item['url']}\n")
        #         f.write(f"Depth: {item['depth']}\n")
        #         f.write(f"Title: {item['title']}\n")
        #         f.write(f"Description: {item['description']}\n")
        #         f.write(f"Keywords: {item['keywords']}\n")
        #         f.write(f"\n--- Content ---\n\n")
        #         f.write(item['content'].replace('\\n', '\n'))  # Convert back escaped newlines
        #         f.write(f"\n{'='*80}\n")

        # Save depth analysis
        depth_stats = {}
        for item in metadata:  # Use sanitized metadata
            depth = item['depth']
            if depth not in depth_stats:
                depth_stats[depth] = 0
            depth_stats[depth] += 1
            
        stats_filename = os.path.join(output_dir, 'depth_statistics.json')
        with open(stats_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'total_pages': len(self.visited_urls),
                'max_depth_reached': max(depth_stats.keys()) if depth_stats else 0,
                'pages_per_depth': depth_stats
            }, f, indent=4)

        print(f"\nCrawling complete!")
        print(f"Processed {len(self.visited_urls)} pages")
        print(f"Maximum depth reached: {max(depth_stats.keys()) if depth_stats else 0}")
        print(f"Results saved to: {output_dir}")
        
        return {
            "websiteUrl" : self.base_url,
            "websiteDepth": self.depth,
            "websiteMaxNumberOfPages": self.max_pages,
            "lastScrapedDate": timestamp,
            "filePath": metadata_filename
        }


# if __name__ == "__main__":
#     base_url = input("Enter the base URL to crawl: ")
#     depth = int(input("Enter the crawl depth (1-10): "))
#     max_pages = int(input("Enter the maximum number of pages to crawl: "))

#     crawler = WebCrawler(base_url, depth=depth, max_pages=max_pages)
#     crawler.crawl()
#     crawler.save_results()