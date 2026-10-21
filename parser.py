import bs4
#Функции парсинга

def parse_page_for_courses_urls(page: str) -> list[str]:  # Находит все ссылки на курсы на одной странице
    links = []
    soup = bs4.BeautifulSoup(page, "html.parser")
    content_block = soup.find("div", class_="content__inner")
    if content_block is None:
        raise RuntimeError('Не обнаружено блока "content__inner"')
    edu_events = content_block.find_all("div", class_="edu-events__item")
    if not edu_events:
        raise RuntimeError('Не обнаружено блока "edu-events__item"')
    for event in edu_events:
        course = event.find("div", class_="edu-events_courses")
        if course is None:
            continue
        title = course.find("div", class_="edu-events_title")
        if not title:
            continue
        links.append(title.find("a").get("href"))
    return links


def parse_base_page_for_next_pages(base_page: str) -> list[str]:  # Находит ссылки на следующие страницы с курсами, возвращает пустой список если не находит
    next_pages_urls = []
    soup = bs4.BeautifulSoup(base_page, "html.parser")
    indent3 = soup.find("div", class_="with-indent3")
    if indent3 is None:
        return []
    pages_indets = (indent3.find("div", class_="pages")).find_all("a")
    for i in pages_indets:
        next_pages_urls.append(i.get("href"))
    return next_pages_urls

def parse_for
