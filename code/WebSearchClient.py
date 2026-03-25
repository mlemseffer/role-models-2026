from huggingface_hub import InferenceClient
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


class WebSearchClient:
    def __init__(self, inference_server_base_url, inference_server_api_key, text_model):
        self.inference_client = InferenceClient(base_url=inference_server_base_url, api_key=inference_server_api_key)
        self.model = text_model

    def get_duckduckgo_results(self, query, n=5):
        urls = []
        with DDGS() as ddgs:
            for result in ddgs.text(query, max_results=n):
                urls.append(result["href"])
        return urls

    def fetch_page_content(self, url):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            content = soup.find("main")
            if content == None:
                content = soup.find("body")

            return content.text
        except Exception as e:
            return f"[Error fetching {url}: {e}]"

    def get_search_contents(self, query, n=3):
        urls = self.get_duckduckgo_results(query, n)
        contents = {}
        for url in urls:
            print(f"Fetching: {url}")
            contents[url] = self.fetch_page_content(url)
        return contents

    def get_summary(self, query):
        web_pages_content = self.get_search_contents(query)
        response = self.inference_client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Answer only with a very complete chronological biography using the given content. It must be comprehensive and include personal informations.",
                },
                {
                    "role": "user",
                    "content": str(web_pages_content),
                },
            ],
        )
        return response.choices[0].message.content

    def get_person_image(self, query, idx = 0):
        with DDGS() as ddgs:
            results = ddgs.images(query)
            return results[idx]['image']

