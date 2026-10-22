import https_client
import html_parser
import json
def parse_and_save_courses(BASE_URL: str, OUTPUT_FILE: str, hse_client: https_client.HttpsClient):
    # 1. Собираем ссылки на страницы каталога (пагинация)
    links_to_parse = [BASE_URL]
    base_page = hse_client.get_page(BASE_URL)
    links_to_parse.extend(html_parser.extract_next_page_urls(base_page))

    # 2. Собираем ссылки на сами курсы
    courses_urls = []
    for parsed_link in links_to_parse:
        parsed_page = hse_client.get_page(parsed_link)
        courses_urls.extend(html_parser.extract_course_urls(parsed_page))

    # 3. Парсим каждый курс и складываем в список словарей
    all_courses = []
    for idx, course_url in enumerate(courses_urls):
        try:
            current_course_html = hse_client.get_page(course_url)
            course_data = html_parser.extract_course_content(current_course_html)

            # Формируем итоговую структуру для JSON
            course_record = {
                "id": idx,
                "title": course_data["title"],
                "url": course_url,
                "content": course_data["content"]
            }
            all_courses.append(course_record)
        except Exception as e:
            print(f"Ошибка при парсинге {course_url}: {e}")

    # 4. Сохраняем список в JSON-файл
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_courses, f, ensure_ascii=False, indent=4)

#Возвращает список ["ID - title"]
def get_all_titles(json_patn: str) -> list[str]:
    with open(json_patn, "r", encoding="UTF-8") as f:
        courses = json.load(f)
    all_titles = []
    for course in courses:
        all_titles.append(f"ID {course["id"]} Название - {course["title"]} \n")
    return all_titles

#Возвращает текст дисциплин свыбранными id
def get_content(json_patn: str, ids: list[int]) -> list[str]:
    with open(json_patn, "r", encoding="UTF-8") as f:
        courses = json.load(f)
    content = []
    if len(ids) == 0:
        for id in range(0, len(courses)):
            content.append(' '.join(map(str, (courses[id].values()))))
        return content

    for id in ids:
        content.append(' '.join(map(str, (courses[id].values()) )))
    return content