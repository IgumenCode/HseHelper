import parser
import httpsClient

BASE_URL = "https://www.hse.ru/ba/isct/courses?course=1.1.1.4&page=1&year=2026"  # Базовая URL
https_client = httpsClient.HttpsClient()
courses_urls = []

base_page = https_client.get_page_via_url(BASE_URL)
links_to_parse = [BASE_URL]
links_to_parse.extend(parser.parse_base_page_for_next_pages(base_page))

print(links_to_parse)

for parsed_link in links_to_parse:
    parsed_page = https_client.get_page_via_url(parsed_link)
    courses_urls.extend(parser.parse_page_for_courses_urls(parsed_page))
print(courses_urls)
