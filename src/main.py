import https_client
import json_handler
import yandex_ai_client

BASE_URL = "https://www.hse.ru/ba/isct/courses?course=1.1.1.4&page=1&year=2026"
OUTPUT_FILE = "courses.json"

#отладка
if __name__ == "__main__":
    h = https_client.HttpsClient()
    json_handler.parse_and_save_courses(BASE_URL, OUTPUT_FILE, h)
    titles = json_handler.get_all_titles(OUTPUT_FILE)
    yandex_client = yandex_ai_client.YandexAiclient()
    quer = input()
    tst = yandex_client.preprocess_question(quer, ' '.join(titles))
    co = json_handler.get_content(OUTPUT_FILE, tst)
    print( yandex_client.generate_answer(quer, ' '.join(co), "deepseek-v4.1-flash/latest")   )