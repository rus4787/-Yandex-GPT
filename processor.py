import re
import requests
import importlib  # Для динамического импорта
from prompts import PROMPT_PROCESSOR

# Константы для нейросети
FOLDER_ID = "b1g7qjo8ml4elpitihit"
URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

class Processor:
    def __init__(self):
        self.stopwords = {"ну", "как бы", "типа", "это самое", "значит", "короче", "слушай", "понимаешь",
                          "вообще", "на самом деле", "в общем", "просто", "кстати", "эээ", "эм", "ммм", "вот",
                          "знаешь", "получается", "собственно", "в принципе", "короче говоря", "так сказать",
                          "ясное дело", "ну как бы", "вообще-то", "да, ну", "наверное", "кажется", "честно говоря",
                          "в любом случае", "так вот", "между прочим", "кстати говоря", "ну ладно", "точнее",
                          "вот это", "прямо", "то есть"}

    def process(self, text):
        # Проверяем наличие текста
        if not text or len(text.strip()) == 0:
            # Если текста нет, ставим флаг и отправляем сообщение пользователю
            return {"success": False, "message": "Нет текста для обработки", "processed_text": None}

        # Приводим к нижнему регистру
        text = text.lower()

        # Удаляем стоп-слова и лишние символы, кроме меток 1) и 2)
        text = re.sub(r'\b(?:{})\b'.format('|'.join(self.stopwords)), '', text)
        text = re.sub(r'[^\w\s\d():]', '', text)  # Убираем лишние символы

        # Заменяем "1)" на "М:" и "2)" на "К:"
        text = text.replace("1)", "М:").replace("2)", "К:")

        # Объединяем реплики одного говорящего
        result = []
        lines = text.splitlines()  # Разбиваем текст по строкам
        current_speaker = None
        buffer = []

        for line in lines:
            # Разделяем текст на фрагменты по меткам говорящих
            parts = re.split(r'(М:|К:)', line)
            for part in parts:
                # Если найден новый говорящий
                if part in {'М:', 'К:'}:
                    # Если сменился говорящий, добавляем буфер в результат
                    if current_speaker and buffer and current_speaker != part:
                        result.append(f"{current_speaker} {' '.join(buffer).strip()}")
                        buffer = []
                    current_speaker = part
                else:
                    # Убираем лишние пробелы и добавляем текст в буфер
                    cleaned_part = re.sub(r'\s+', ' ', part).strip()
                    if cleaned_part:
                        buffer.append(cleaned_part)

        # Добавляем последний буфер в результат
        if current_speaker and buffer:
            result.append(f"{current_speaker} {' '.join(buffer).strip()}")

        # Собираем итоговый текст
        processed_text = ' '.join(result)

        # Считаем количество символов с пробелами
        char_count = len(processed_text)

        # Передаем обработанный текст и флаг следующему агенту напрямую
        next_agent = self.call_next_agent("label", {"processed_text": processed_text, "char_count": char_count})

        return {
            "success": True,
            "processed_text": processed_text,
            "char_count": char_count
        }

    def call_neural_network(self, text, token):
        # Формирование запроса к нейросети с использованием параметров из PROMPT_PROCESSOR
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        payload = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.2,  # Используем температуру из PROMPT_PROCESSOR
                "maxTokens": 1024,
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Роль: Обработчик текста. Задача: Провести предварительную обработку текста, выделить ключевые фразы, привести текст к структурированному виду."
                },
                {
                    "role": "user",
                    "text": text
                }
            ]
        }

        # Отправка запроса на сервер
        response = requests.post(URL, headers=headers, json=payload)

        if response.status_code != 200:
            # Обработка ошибок
            print(f"Ошибка при вызове нейросети: {response.text}")
            return None

        response_data = response.json()
        response_text = response_data.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "")

        return response_text

    def simplified_process(self, text):
        # Приведение текста к нижнему регистру и замена титулов абонентов
        text = text.lower()
        text = text.replace("1)", "М:").replace("2)", "К:")
        return text

    def call_next_agent(self, next_agent_name, data):
        # Динамический вызов следующего агента
        agent_module = importlib.import_module(next_agent_name)
        Agent = getattr(agent_module, next_agent_name.capitalize())
        agent_instance = Agent()
        return agent_instance.process_label(data)
