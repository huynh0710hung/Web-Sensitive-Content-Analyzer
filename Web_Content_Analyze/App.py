from flask import Flask, render_template, request, jsonify, abort
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from urllib.parse import urlparse
import re
import time
import logging
from typing import Dict, List, Tuple, Optional
from fake_useragent import UserAgent
import aiohttp
import asyncio

##Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisResult:
    url: str
    domain: str
    safety_score: float
    rating: str
    bad_word_count: int
    total_word_count: int
    category_analysis: Dict
    status: str = 'success'
    message: str = ''

class WebContentAnalyzer():
    def __init__(self):
        ##download punkt sentence tokenizer
        ##download stopwords collection
        ##download part of speech tagging
        nltk_packages = ['punkt', 'stopwords', 'averaged_perceptron_tagger']
        for package in nltk_packages:
            nltk.download(package, quiet=True)

        self.stopwords = set(stopwords.words('english'))
        self.user_agent = UserAgent()
        ##create aiohttp session for async requests
        self.session = aiohttp.ClientSession()

        ##define sensitive keywords with weights
        self.sensitive_keywords = {
            'violence': {
                'words': ['violence', 'murder', 'fight', 'weapons', 'blood', 'death', 'fatal'],
                'weight': 1.5
            },
            'adult_content': {
                'words': ['pornography', 'adult', 'sex', 'nude', 'naked'],
                'weight': 2.0
            },
            'drugs': {
                'words': ['drugs', 'cocaine', 'heroin', 'marijuana', 'opium'],
                'weight': 1.8
            },
            'discrimination': {
                'words': ['discrimination', 'racism', 'sexism', 'hate'],
                'weight': 1.7
            },
            'gambling': {
                'words': ['gambling', 'casino', 'betting', 'wager'],
                'weight': 1.3
            },
            'fraud': {
                'words': ['fraud', 'hacking', 'scamming', 'theft', 'steal'],
                'weight': 1.6
            }
        }
        #delay time to avoid being blocked by server
        self.request_delay = 1
        self.last_request_time = 0

    ##Implement asynchronous context manager
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.session.close()

    ##Implement rate limiting for requests
    async def respect_rate_limit(self):

        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last_request)

        self.last_request_time = time.time()
    ##Generate different headers for requests, avoid being detected by server
    def get_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        }

    ##simulate google search url and return links
    async def google_search(self, query, num_results=10, max_retries=5) -> List[str]:
        await self.respect_rate_limit()
        url = f'https://www.google.com/search?q={query}&num={num_results}'

        try:
            async with self.session.get(url, headers=self.get_headers()) as response:
                if response.status != 200:
                    logging.exception(f"Google search failed with response status: {response.status}")
                    return []

                soup = BeautifulSoup(await response.text(), 'html.parser')

                links = []
                for result in soup.select('div.yuRUbf a'):
                    if result.has_attr('href'):
                        links.append(result['href'])

                return links[:num_results]

        except Exception as e:
            logging.exception(f"Google search error: {e}")
            return []

    ##fetch webpage content
    async def fetch_webpage(self, url: str) -> Optional[str]:
        await self.respect_rate_limit()

        try:
            async with self.session.get(
                    url,
                    headers=self.get_headers(),
                    timeout=aiohttp.ClientTimeout(total=10),
                    ssl=False
            ) as response:
                if response.status != 200:
                    logging.exception(f"Failed to fetch {url}: Reponse status {response.status}")
                    return None

                return await response.text()

        except Exception as e:
            logging.exception(f"Error fetching {url}: {e}")
            return None

    ##Analyze text content for sensitive words with weights
    def analyze_text_content(self, text: str) -> Tuple[Dict, int, int]:
        if not text:
            return {}, 0, 0

        tokens = word_tokenize(text.lower())
        ##count total meaningful words, removing stopwords
        tokens = [word for word in tokens if word not in self.stopwords]
        total_word_count = len(tokens) - len(self.stopwords.intersection(tokens))

        sensitive_score = {}
        bad_word_count = 0

        for category, data in self.sensitive_keywords.items():
            keywords = data['words']
            weight = data['weight']

            ##count weighted matches for each category
            matches = sum(1 for token in tokens if any(keyword in token for keyword in keywords))
            weighted_matches = matches * weight
            sensitive_score[category] = weighted_matches / (total_word_count or 1) ##avoid division by zero
            bad_word_count += matches

        return sensitive_score, bad_word_count, total_word_count

    ##Calculate safety score and rating based on word counts
    def calculate_safety_rating(self, bad_word_count: int, total_word_count: int) -> Tuple[float, str]:

        base_score = 10

        if total_word_count == 0:
            return base_score, "Unknown"

        ##calculate weighted penalty
        bad_word_ratio = bad_word_count / total_word_count
        penalty = bad_word_ratio * 10 * 2  # Multiply by 2 to make the penalty more significant

        ##calculate final score
        safety_score = max(0.0, base_score - penalty)

        ##determine rating based on safety score
        if safety_score >= 9:
            rating = "Very Safe"
        elif safety_score >= 7:
            rating = "Safe"
        elif safety_score >= 5:
            rating = "Moderate"
        elif safety_score >= 3:
            rating = "Unsafe"
        else:
            rating = "Very Unsafe"

        return safety_score, rating

    async def analyze_single_webpage(self, url: str) -> AnalysisResult:
        try:
            content = await self.fetch_webpage(url)
            if not content:
                return AnalysisResult(
                    url=url,
                    domain='',
                    safety_score=0,
                    rating='Error',
                    bad_word_count=0,
                    total_word_count=0,
                    category_analysis={},
                    status='error',
                    message='Could not fetch page content'
                )

            text_content = BeautifulSoup(content, 'html.parser').get_text()
            ##remove any special characters and redundant whitespace
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            text_content = re.sub(r'[^\w\s]', '', text_content)

            category_scores, bad_word_count, total_word_count = self.analyze_text_content(text_content)
            safety_score, rating = self.calculate_safety_rating(bad_word_count, total_word_count)

            return AnalysisResult(
                url=url,
                domain=urlparse(url).netloc,
                safety_score=round(safety_score, 2),
                rating=rating,
                bad_word_count=bad_word_count,
                total_word_count=total_word_count,
                category_analysis=category_scores,
            )

        except Exception as e:
            logging.exception(f"Error analyzing {url}: {e}")
            return AnalysisResult(
                url=url,
                domain='',
                safety_score=0,
                rating='Error',
                bad_word_count=0,
                total_word_count=0,
                category_analysis={},
                status='error',
                message=str(e)
            )

    async def analyze_search_results(self, query: str) -> List[AnalysisResult]:
        urls = await self.google_search(query)
        if not urls:
            return []

        tasks = [self.analyze_single_webpage(url) for url in urls]
        results = await asyncio.gather(*tasks)

        valid_results = [r for r in results if r.status == 'success']
        return sorted(valid_results, key=lambda x: x.safety_score, reverse=True)


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
async def analyze():
    try:
        query = request.form.get('query')
        if not query:
            abort(400, description="Please enter a search keyword")

        async with WebContentAnalyzer() as analyzer:
            results = await analyzer.analyze_search_results(query)
    except Exception as e:
        logging.exception("An error occurred during analysis:")  ##logs full traceback
        abort(500, description=f"An internal server error occurred: {e}")
    return jsonify({
        'results': [vars(result) for result in results],
        'metadata': {
            'query': query,
            'total_results': len(results),
            'timestamp': time.time()
        }
    })


if __name__ == '__main__':
    app.run(debug=True)
