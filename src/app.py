import os
import json
import streamlit as st

import https_client
import json_handler
import yandex_ai_client

BASE_URL = "https://www.hse.ru/ba/isct/courses?course=1.1.1.4&page=1&year=2026"
OUTPUT_FILE = "courses.json"

st.set_page_config(
    page_title="Помощник первокурсника ИВТ МИЭМ",
    page_icon="🎓",
    layout="wide"
)


@st.cache_resource
def init_llm_client() -> yandex_ai_client.YandexAiclient:
    return yandex_ai_client.YandexAiclient()


def load_raw_courses(file_path: str) -> list[dict]:
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_sources_by_ids(courses: list[dict], selected_ids: list[int]) -> list[dict]:
    course_map = {c["id"]: c for c in courses if "id" in c}
    sources = []
    for cid in selected_ids:
        if cid in course_map:
            sources.append({
                "id": cid,
                "title": course_map[cid].get("title", f"Курс #{cid}"),
                "url": course_map[cid].get("url", "")
            })
    return sources


# --- Инициализация клиента YandexGPT ---
try:
    llm_client = init_llm_client()
except Exception as e:
    st.error(f"Ошибка инициализации YandexAiclient: {e}. Проверьте файл .env.")
    st.stop()

# --- Боковая панель (Настройки и управление базой) ---
with st.sidebar:
    st.header("Управление и настройки")

    courses_data = load_raw_courses(OUTPUT_FILE)
    if courses_data:
        st.success(f"База загружена: {len(courses_data)} дисциплин")
    else:
        st.warning(f"Файл {OUTPUT_FILE} не найден. Обновите базу дисциплин.")

    if st.button("🔄 Собрать / Обновить базу курсов", use_container_width=True):
        with st.spinner("Парсинг программ дисциплин с сайта ВШЭ..."):
            try:
                h_client = https_client.HttpsClient()
                json_handler.parse_and_save_courses(BASE_URL, OUTPUT_FILE, h_client)
                st.rerun()
            except Exception as e:
                st.error(f"Ошибка при парсинге: {e}")

    st.divider()

    router_model = st.selectbox(
        "Модель маршрутизатора (Шаг 1):",
        options=["yandexgpt-lite/latest", "yandexgpt/latest"],
        index=0
    )

    generator_model = st.selectbox(
        "Модель генерации ответа (Шаг 2):",
        options=["yandexgpt/latest", "yandexgpt-lite/latest", "deepseek-v4.1-flash/latest"],
        index=0
    )

    st.divider()

    if st.button("🗑️ Очистить историю диалога", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if courses_data:
        with st.expander("📋 Список дисциплин в базе"):
            for c in courses_data:
                st.markdown(f"**[{c['id']}]** [{c['title']}]({c['url']})")

# --- Основная область чата ---
st.title("🎓 Помощник первокурсника ИВТ МИЭМ НИУ ВШЭ")
st.caption("Ответы по содержанию учебных дисциплин, формулам оценивания и литературе (1 курс, 2026–2027 уч. год)")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Отрисовка истории сообщений
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📚 Использованные источники и дисциплины"):
                for src in msg["sources"]:
                    st.markdown(f"- **[{src['id']}] {src['title']}** — [{src['url']}]({src['url']})")

# Обработка нового вопроса
if user_query := st.chat_input("Задайте вопрос по учебным дисциплинам..."):
    if not courses_data:
        st.error("База дисциплин пуста. Нажмите «Собрать / Обновить базу курсов» на боковой панели.")
        st.stop()

    # Сохраняем и выводим вопрос пользователя
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Формируем ответ помощника
    with st.chat_message("assistant"):
        try:
            # Шаг 1: Выбор подходящих дисциплин через LLM
            with st.spinner("Определение релевантных дисциплин..."):
                titles_list = json_handler.get_all_titles(OUTPUT_FILE)
                catalog_text = "".join(titles_list)
                raw_ids = llm_client.preprocess_question(
                    question=user_query,
                    catalog_text=catalog_text,
                    model_name=router_model
                )

                valid_ids_set = {c["id"] for c in courses_data if "id" in c}
                selected_ids = [int(i) for i in raw_ids if str(i).isdigit() and int(i) in valid_ids_set]

            sources = get_sources_by_ids(courses_data, selected_ids)

            # Шаг 2: Извлечение контекста и генерация ответа
            if not selected_ids:
                answer_text = (
                    "Маршрутизатор не смог привязать вопрос к конкретным дисциплинам из каталога "
                    "(получен пустой список ID). Уточните название предмета в вопросе."
                )
            else:
                with st.spinner(f"Анализ программ дисциплин (выбрано: {len(selected_ids)}) и генерация ответа..."):
                    content_chunks = json_handler.get_content(OUTPUT_FILE, selected_ids)
                    context_str = "\n\n===\n\n".join(content_chunks)
                    answer_text = llm_client.generate_answer(
                        question=user_query,
                        selected_courses_context=context_str,
                        model_name=generator_model
                    )

            st.markdown(answer_text)

            if sources:
                with st.expander("📚 Использованные источники и дисциплины", expanded=True):
                    for src in sources:
                        st.markdown(f"- **[{src['id']}] {src['title']}** — [{src['url']}]({src['url']})")

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer_text,
                "sources": sources
            })

        except Exception as e:
            st.error(f"Произошла ошибка при обработке запроса: {e}")