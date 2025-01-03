# Web Content Safety Analyzer

This project is a Flask-based web application that analyzes the safety of web pages based on their content. It uses Natural Language Processing (NLP) techniques to identify sensitive keywords and determine a safety score and rating for each page.

## Features

-   **Web Page Analysis:** Analyzes the content of a single web page to determine its safety.
-   **Google Search Analysis:** Performs a Google search and analyzes the top results.
-   **Sensitive Content Detection:** Identifies sensitive keywords related to violence, adult content, drugs, discrimination, gambling, and fraud.
-   **Safety Scoring:** Assigns a safety score to each page based on the presence and frequency of sensitive keywords.
-   **Safety Rating:** Categorizes pages as "Very Safe", "Safe", "Moderate", "Unsafe", or "Very Unsafe" based on their safety score.
-   **Asynchronous Processing:** Uses asynchronous programming (asyncio and aiohttp) for efficient handling of multiple requests and improved performance.
-   **Rate Limiting:** Implements rate limiting to avoid overloading servers and prevent being blocked.
-   **User-Agent Randomization:** Uses a library (`fake_useragent`) to generate random user agents for each request, making it harder for websites to detect and block the analyzer.
-   **Error Handling:** Includes robust error handling and logging to capture and report issues during web page fetching and analysis.

## Technologies Used

-   **Flask:** A lightweight Python web framework.
-   **Beautiful Soup:** A library for parsing HTML and XML documents.
-   **NLTK:** The Natural Language Toolkit, a suite of libraries for NLP tasks.
-   **aiohttp:** An asynchronous HTTP client/server framework.
-   **asyncio:** A library for writing concurrent code using the async/await syntax.
-   **fake-useragent:** A library for generating fake user agent strings.

## Flask Routes

-   `/`: Renders the main page (index.html).
-   `/analyze` (POST): Accepts a search query, performs the analysis, and returns the results as JSON.

## Setup and Installation

1. **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Run the application:**

    ```bash
    python app.py
    ```

4. **Access the application in your web browser:**

    ```
    http://127.0.0.1:5000/
    ```

## Usage

1. **Run the Application**:
    ```bash
    python app.py
    ```

2. **Access the Web Interface**:
   Open your browser and go to [http://127.0.0.1:5000](http://127.0.0.1:5000).

3. **Analyze Search Queries**:
   - Enter a search query in the input box on the homepage.
   - View the safety scores and detailed analysis of the top search results.

---


## Dependencies

- **Python 3.8+**
- **Flask**: Web framework.
- **Requests**: HTTP requests library.
- **BeautifulSoup**: HTML parsing.
- **NLTK**: Natural language processing toolkit.
- **ThreadPoolExecutor**: Multithreading for concurrent processing.

- ## Error Handling

-   The application handles various errors, such as network issues, invalid URLs, and parsing errors.
-   Error messages are logged using the `logging` module.
-   If an error occurs during analysis, the application returns a 500 error with a descriptive message.
-   If a specific web page cannot be fetched or analyzed, an `AnalysisResult` object with an "error" status and a corresponding message is returned for that page.

## Notes

-   The accuracy of the analysis depends on the quality of the sensitive keyword list and the weights assigned to each category.
-   The application is designed to be respectful of website resources by implementing rate limiting and using random user agents. However, it's essential to use it responsibly and avoid overloading any particular website.
-   The safety scores and ratings are based on an automated analysis and should not be considered definitive. Human judgment is always recommended when assessing the safety of web content, especially for critical applications.
-   The project can be further improved by adding features such as:
    -   Customizable sensitive keyword lists and weights.
    -   Support for different languages.
    -   More advanced NLP techniques, such as sentiment analysis and topic modeling.
    -   Integration with other web safety APIs or databases.
    -   Caching of analysis results to improve performance.
-   The `index.html` and other frontend related files are not included in the code.

## License

This project is licensed under the MIT License. You can find the full license text in the `LICENSE` file (if it exists in the repository).
