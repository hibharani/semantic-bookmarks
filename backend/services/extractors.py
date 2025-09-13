import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import yt_dlp
import pdfplumber
from io import BytesIO


class ContentExtractor(ABC):
    """Base class for content extractors"""
    
    @abstractmethod
    def extract(self, url: str) -> Dict[str, Any]:
        """Extract content from URL"""
        pass


class YouTubeExtractor(ContentExtractor):
    """Extract content from YouTube videos"""
    
    def extract(self, url: str) -> Dict[str, Any]:
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Get subtitles/transcript
                subtitles = ""
                if 'subtitles' in info and 'en' in info['subtitles']:
                    # Process subtitles to extract text
                    for sub in info['subtitles']['en']:
                        if sub.get('ext') == 'vtt':
                            # Download and parse VTT subtitles
                            sub_response = requests.get(sub['url'])
                            if sub_response.status_code == 200:
                                subtitles = self._parse_vtt(sub_response.text)
                            break
                
                return {
                    'title': info.get('title', ''),
                    'description': info.get('description', ''),
                    'content': subtitles,
                    'platform': 'youtube',
                    'meta_data': {
                        'duration': info.get('duration'),
                        'view_count': info.get('view_count'),
                        'upload_date': info.get('upload_date'),
                        'uploader': info.get('uploader'),
                        'channel_id': info.get('channel_id'),
                        'thumbnail': info.get('thumbnail'),
                    }
                }
        except Exception as e:
            return {
                'title': '',
                'description': '',
                'content': '',
                'platform': 'youtube',
                'meta_data': {'error': str(e)}
            }
    
    def _parse_vtt(self, vtt_content: str) -> str:
        """Parse VTT subtitle format to extract text"""
        lines = vtt_content.split('\n')
        text_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip timestamp lines and empty lines
            if '-->' in line or not line or line.startswith('WEBVTT'):
                continue
            # Skip lines that look like timestamps
            if re.match(r'^\d+$', line):
                continue
            text_lines.append(line)
        
        return ' '.join(text_lines)


class TwitterExtractor(ContentExtractor):
    """Extract content from Twitter/X posts"""
    
    def extract(self, url: str) -> Dict[str, Any]:
        # For now, use basic web scraping
        # In production, use Twitter API or ntscraper
        try:
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to extract tweet content (this is fragile and may need updates)
            title = soup.find('title')
            title_text = title.text if title else ''
            
            # Look for meta description or other content
            description_meta = soup.find('meta', {'name': 'description'})
            description = description_meta.get('content', '') if description_meta else ''
            
            return {
                'title': title_text,
                'description': description,
                'content': description,
                'platform': 'twitter',
                'metadata': {
                    'url': url,
                    'extracted_at': 'now'
                }
            }
        except Exception as e:
            return {
                'title': '',
                'description': '',
                'content': '',
                'platform': 'twitter',
                'meta_data': {'error': str(e)}
            }


class PDFExtractor(ContentExtractor):
    """Extract content from PDF files"""
    
    def extract(self, url: str) -> Dict[str, Any]:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                pdf_file = BytesIO(response.content)
                
                text_content = []
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
                
                content = '\n'.join(text_content)
                
                # Try to extract title from first page
                title = content.split('\n')[0][:100] if content else ''
                
                return {
                    'title': title,
                    'description': content[:500] + '...' if len(content) > 500 else content,
                    'content': content,
                    'platform': 'pdf',
                    'meta_data': {
                        'page_count': len(text_content),
                        'file_size': len(response.content)
                    }
                }
        except Exception as e:
            return {
                'title': '',
                'description': '',
                'content': '',
                'platform': 'pdf',
                'meta_data': {'error': str(e)}
            }


class WebsiteExtractor(ContentExtractor):
    """Extract content from general websites"""
    
    def extract(self, url: str) -> Dict[str, Any]:
        """Extract content using requests and BeautifulSoup"""
        return self._extract_with_requests(url)
    
    def _extract_with_requests(self, url: str) -> Dict[str, Any]:
        """Fallback extraction using requests and BeautifulSoup"""
        try:
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = soup.find('title')
            title_text = title.text if title else ''
            
            description_meta = soup.find('meta', {'name': 'description'})
            description = description_meta.get('content', '') if description_meta else ''
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            content = soup.get_text()
            
            return {
                'title': title_text,
                'description': description,
                'content': content,
                'platform': 'website',
                'metadata': {
                    'domain': urlparse(url).netloc
                }
            }
        except Exception as e:
            return {
                'title': '',
                'description': '',
                'content': '',
                'platform': 'website',
                'meta_data': {'error': str(e)}
            }


class ContentExtractorFactory:
    """Factory to get appropriate content extractor based on URL"""
    
    PLATFORM_PATTERNS = {
        'youtube': [r'youtube\.com', r'youtu\.be'],
        'twitter': [r'twitter\.com', r'x\.com'],
        'pdf': [r'\.pdf$'],
        'reddit': [r'reddit\.com'],
        'github': [r'github\.com'],
    }
    
    def get_extractor(self, url: str) -> ContentExtractor:
        """Get appropriate extractor for URL"""
        platform = self._detect_platform(url)
        
        extractors = {
            'youtube': YouTubeExtractor(),
            'twitter': TwitterExtractor(),
            'pdf': PDFExtractor(),
            'website': WebsiteExtractor(),
        }
        
        return extractors.get(platform, WebsiteExtractor())
    
    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL"""
        for platform, patterns in self.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return platform
        return 'website'