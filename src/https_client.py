# Класс для запросов на сайт Вышки
import requests


class HttpsClient:
    def __init__(self):
        self.https_session = requests.Session()

    def get_page(self, url: str) -> str:
        response = self.https_session.get(url)
        response.raise_for_status()
        return response.text
