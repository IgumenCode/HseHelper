import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class YandexAiclient:
    def __init__(self, api_key: str = None, folder_id: str = None):
        self.api_key = api_key or os.getenv("YANDEX_API_KEY")
        self.folder_id = folder_id or os.getenv("YANDEX_FOLDER_ID")

        if not self.api_key or not self.folder_id:
            raise ValueError("Не указаны YANDEX_API_KEY или YANDEX_FOLDER_ID")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://ai.api.cloud.yandex.net/v1",
            project=self.folder_id
        )

    def _get_model_uri(self, model_name: str) -> str:
        return f"gpt://{self.folder_id}/{model_name}"

    def preprocess_question(
        self,
        question: str,
        catalog_text: str,
        model_name: str = "yandexgpt-lite/latest"
    ) -> list[int]:
        """
        Шаг 1: Препроцессор вопроса.
        Принимает вопрос и список всех доступных курсов (ID + название).
        Возвращает список ID нужных курсов (например, [0, 1]).
        """
        system_prompt = (
            "Ты — маршрутизатор запросов для помощника первокурсника ИВТ МИЭМ НИУ ВШЭ.\n"
            "Твоя задача — выбрать из каталога ID дисциплин, которые нужны для ответа на вопрос.\n"
            "Правила:\n"
            "1. Если предмет назван без уточнения профиля (например, «информатика», «матан», «алгебра», «питон»), "
            "выбирай ID ВСЕХ его вариантов (обычный, углубленный, индустриальный).\n"
            "2. Если вопрос про связь дисциплин — выбирай все связанные курсы.\n"
            "3. Если вопрос общий и не привязан к конкретным предметам — верни пустой список [].\n\n"
            "Верни ответ СТРОГО в формате JSON-объекта с ключом \"selected_ids\" и списком чисел: "
            "{\"selected_ids\": [0, 1]}"
        )

        user_prompt = (
            f"КАТАЛОГ ДИСЦИПЛИН:\n{catalog_text}\n\n"
            f"ВОПРОС СТУДЕНТА:\n{question}\n\n"
            "Верни JSON с ключом \"selected_ids\":"
        )

        response = self.client.chat.completions.create(
            model=self._get_model_uri(model_name),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        raw_content = response.choices[0].message.content
        try:
            data = json.loads(raw_content)
            return data.get("selected_ids", [])
        except json.JSONDecodeError:
            return []

    def generate_answer(
        self,
        question: str,
        selected_courses_context: str,
        model_name: str = "yandexgpt/latest"
    ) -> str:
        """
        Шаг 2: Генерация финального ответа.
        Принимает вопрос и склеенный текст выбранных программ дисциплин (ПУД).
        Возвращает готовый ответ для студента.
        """
        system_prompt = (
            "Ты — помощник первокурсника программы «Информатика и вычислительная техника» МИЭМ НИУ ВШЭ.\n"
            "Ответь на вопрос студента точно и ТОЛЬКО на основе предоставленных ниже программ дисциплин (ПУД).\n"
            "Правила:\n"
            "1. Если в контексте переданы обычный и углубленный варианты курса, явно раздели ответ для каждого из них.\n"
            "2. Формулы оценивания, пререквизиты и списки литературы выводи аккуратными маркированными списками.\n"
            "3. Если в предоставленном тексте нет ответа на вопрос, и к нему нельзя прийти с помощью базовых рассуждений, честно сообщи об этом и ничего не придумывай от себя."
        )

        user_prompt = (
            f"МАТЕРИАЛЫ УЧЕБНЫХ ДИСЦИПЛИН:\n{selected_courses_context}\n\n"
            f"ВОПРОС СТУДЕНТА:\n{question}"
        )

        response = self.client.chat.completions.create(
            model=self._get_model_uri(model_name),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )

        return response.choices[0].message.content