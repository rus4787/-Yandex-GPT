import pandas as pd
import requests
import json
import logging
from preprocessing_text import PreprocessingText
from processor import Processor
from prompts import PROMPT_USER

# Замените на ваши реальные значения
FOLDER_ID = <"твоя папка">
TOKEN_CACHE_FILE = "token_cache.json"
URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

class User:
    def __init__(self, input_filepath, output_filepath):
        self.input_filepath = input_filepath
        self.output_filepath = output_filepath
        self.data = pd.read_excel(input_filepath)
        self.processed_data = []
        self.token = self.get_cached_token()
        self.logs = []

    def get_cached_token(self):
        try:
            with open(TOKEN_CACHE_FILE, 'r') as f:
                token_data = json.load(f)
                return token_data.get("access_token")
        except FileNotFoundError:
            raise Exception("Token cache file not found.")

    def preprocessing(self):
        preprocessor = PreprocessingText()
        filtered_df = preprocessor.preprocessing_main(self.input_filepath)
        return filtered_df

    def initiate_processing(self, text):
        prompt = PROMPT_USER.format(text=text)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        payload = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,
                "maxTokens": 1024,
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Роль: Анализатор взаимодействий с клиентами. Задача: Обработать текст разговора менеджера с клиентом и выделить ключевые фразы, результат анализа, тип взаимодействия, а также указать все комментарии и цитаты."
                },
                {
                    "role": "user",
                    "text": text
                }
            ]
        }

        response = requests.post(URL, headers=headers, json=payload)
        if response.status_code != 200:
            logging.error(f"Failed to get response from YandexGPT: {response.text}")
            raise Exception(f"Failed to get response from YandexGPT: {response.text}")

        response_data = response.json()

        # Проверка наличия необходимых данных в ответе
        if 'result' not in response_data:
            response_data['result'] = {}
        if 'alternatives' not in response_data['result']:
            response_data['result']['alternatives'] = [{}]
        if 'message' not in response_data['result']['alternatives'][0]:
            response_data['result']['alternatives'][0]['message'] = {}
        if 'text' not in response_data['result']['alternatives'][0]['message']:
            response_data['result']['alternatives'][0]['message']['text'] = ""

        response_text = response_data['result']['alternatives'][0]['message'].get('text', "")
        if not response_text:
            logging.error("Нет структурированных данных для обработки: текст отсутствует в ответе")
            return None

        logging.info(f"Полученный текст для дальнейшей обработки: {response_text}")

        return response_text

    def process_pipeline(self, filtered_df):
        processor = Processor()
        processed_results = []

        for index, row in filtered_df.iterrows():
            text = row['text']
            processed_text = self.initiate_processing(text)
            if processed_text:
                result = processor.process(text=processed_text)
                processed_results.append({
                    "success": result.get("success", False),
                    "processed_text": processed_text,
                    "char_count": result.get("char_count", 0),
                    "тип_разговора": "",
                    "модуль_вовлеченности": "",
                    "не_результат": "",
                    "результат": "",
                    "другое": "",
                    "общая_оценка": "",
                    "надо_сказать": ""
                })
            else:
                logging.warning(f"Пустой обработанный текст для строки {index}, пропуск.")
                processed_results.append({
                    "success": False,
                    "processed_text": "",
                    "char_count": 0,
                    "тип_разговора": "",
                    "модуль_вовлеченности": "",
                    "не_результат": "",
                    "результат": "",
                    "другое": "",
                    "общая_оценка": "",
                    "надо_сказать": ""
                })

        processed_df = filtered_df.copy()
        for key in processed_results[0].keys():
            processed_df[key] = [res[key] for res in processed_results]

        # Запрос данных от Буфера для обновления всех нужных столбцов
        logging.info("Передача данных в Буфер для генерации дополнительных столбцов")
        buffer_response = self.request_buffer_data()
        if buffer_response is not None and not buffer_response.empty:
            for column in buffer_response.columns:
                processed_df[column] = buffer_response[column]
        else:
            logging.warning("Буфер вернул пустой ответ, дополнительные столбцы не были обновлены.")

        self.processed_data = processed_df

    def request_buffer_data(self):
        # Метод для взаимодействия с "Буфером" для получения данных
        from buffer import Buffer
        buffer_agent = Buffer()
        response = buffer_agent.get_suggestions(token=self.token)
        logging.info(f"Получены данные из Буфера: {response}")
        return response

    def save_processed_data(self):
        if not self.processed_data.empty:
            self.processed_data.drop(columns=['text'], inplace=True)
            self.processed_data.to_excel(self.output_filepath, index=False)
            logging.info(f"Обработанные данные успешно сохранены в {self.output_filepath}")
        else:
            logging.warning("Нет данных для сохранения")

    def run(self):
        filtered_df = self.preprocessing()
        self.process_pipeline(filtered_df)
        self.save_processed_data()

if __name__ == "__main__":
    input_path = "C:/Users/khabi/Python_project/barnaul/base_work/data_call_extended.xlsx"
    output_path = "C:/Users/khabi/Python_project/barnaul/base_work/processed_data.xlsx"
    user_agent = User(input_path, output_path)
    user_agent.run()


