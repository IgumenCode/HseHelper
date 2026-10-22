import bs4
#Функции парсинга

def extract_course_urls(page: str) -> list[str]:  # Возвращает список со всеми ссылками на курсы с данной страницы
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


def extract_next_page_urls(base_page: str) -> list[str]:  # Возвращает список с ссылками на следующие страницы с курсами, возвращает пустой список если не находит
    next_pages_urls = []
    soup = bs4.BeautifulSoup(base_page, "html.parser")
    indent3 = soup.find("div", class_="with-indent3")
    if indent3 is None:
        return []
    pages_indets = (indent3.find("div", class_="pages")).find_all("a")
    for i in pages_indets:
        next_pages_urls.append(i.get("href"))
    return next_pages_urls

def extract_course_content(course_page: str) -> dict[str, str]:  #Возвращает словарь {"Название курса": "Описание курса"}
    soup = bs4.BeautifulSoup(course_page, "html.parser")
    program_header = soup.find("div", class_="b-program__header")
    if not program_header:
        raise RuntimeError('Не обнаружено блока "b-program__header"')
    course_title = program_header.find("h1", class_="b-program__header-title").get_text(separator=" ", strip=True)
    course_content = program_header.find("div", class_="b-program__header-info").get_text(separator=" ", strip=True)
    program_comment = soup.find("div", class_="b-program__comment b-program__block")
    if not program_comment:
        raise RuntimeError('Не обнаружено блока "b-program__comment b-program__block"')
    program_comment_text = program_comment.get_text(separator=" ", strip=True)
    course_content = f"{course_content} {program_comment_text}"
    return {"title": course_title, "content" : course_content}

