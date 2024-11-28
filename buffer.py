import pandas as pd
import requests
import json
import logging
from prompts import PROMPT_BUFFER

# Замените на ваши реальные значения
FOLDER_ID = <"твоя папка">
TOKEN_CACHE_FILE = "token_cache.json"
URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

class Buffer:
    def __init__(self):
        self.data = pd.DataFrame(columns=["текст", "тип_разговора", "модуль_вовлеченности", "не_результат", "результат", "другое", "общая_оценка", "надо_сказать"])
        self.token = self.get_cached_token()

    def get_cached_token(self):
        try:
            with open(TOKEN_CACHE_FILE, 'r') as f:
                token_data = json.load(f)
                return token_data.get("access_token")
        except FileNotFoundError:
            raise Exception("Token cache file not found.")

    def store_data(self, data):
        logging.info(f"Входящие данные для сохранения в буфер: {data}")
        # Добавление новой строки данных в "Буфер"
        new_row = {
            "текст": data.get("text", ""),
            "тип_разговора": data.get("тип_разговора", ""),
            "модуль_вовлеченности": data.get("модуль_вовлеченности", ""),
            "не_результат": data.get("не_результат", ""),
            "результат": data.get("результат", ""),
            "другое": data.get("другое", ""),
            "общая_оценка": data.get("общая_оценка", ""),
            "надо_сказать": ""
        }
        self.data = pd.concat([self.data, pd.DataFrame([new_row])], ignore_index=True)
        logging.info(f"Буфер после добавления новой строки: {self.data}")
        logging.info(f"Данные успешно сохранены в буфер: {new_row}")

    def analyze_and_generate_suggestions(self):
        logging.info("Начало анализа и генерации предложений для каждой строки буфера")

        for index, row in self.data.iterrows():
            if not row["надо_сказать"]:  # Если поле "надо_сказать" пустое, запускаем нейросеть
                текст = row["текст"]
                модуль_вовлеченности = row["модуль_вовлеченности"]
                не_результат = row["не_результат"]

                # Логирование перед отправкой запроса в нейросеть
                logging.info(
                    f"Запрос к нейросети для строки {index}: текст='{текст}', модуль_вовлеченности='{модуль_вовлеченности}', не_результат='{не_результат}'")

                prompt = PROMPT_BUFFER.format(текст=текст, модуль_вовлеченности=модуль_вовлеченности,
                                              не_результат=не_результат)
                suggestion = self.get_suggestion_from_api(prompt)

                if suggestion:
                    self.data.at[index, "надо_сказать"] = suggestion
                    logging.info(f"Сгенерированная фраза для строки {index}: {suggestion}")
                else:
                    logging.warning(f"Не удалось сгенерировать фразу для строки {index}")
                    logging.info(f"Буфер после обновления строки {index}: {self.data}")

        logging.info("Завершение анализа и генерации предложений")

    def get_suggestion_from_api(self, prompt):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        payload = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 1.0,
                "maxTokens": 150,
            },
            "messages": [
                {
                    "role": "system",
                    "text": prompt
                }
            ]
        }

        logging.info(f"Отправка запроса в YandexGPT с payload: {payload}")

        try:
            response = requests.post(URL, headers=headers, json=payload)
            response.raise_for_status()  # Это выбросит исключение при ошибке
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при вызове YandexGPT API: {e}")
            return None

        response_data = response.json()
        logging.info(f"Получен ответ от YandexGPT: {response_data}")

        suggestion = response_data.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "")
        if not suggestion:
            logging.warning("Нет сгенерированной фразы в ответе от YandexGPT")

        return suggestion

    def get_suggestions(self, token):
        # Метод для получения всех предложений и передачи в User
        self.token = token  # Обновляем токен
        self.analyze_and_generate_suggestions()
        return self.data[["надо_сказать"]]

if __name__ == "__main__":
    buffer_agent = Buffer()
    sample_data_1 = {
        "text": "1)  Алло! Здравствуйте! Сергей Александрович, это Елена Владимировна, институт АААА. Мы с вами по обучению говорили.2)  Да, слушаю вас.1)  Помните, да, говорила вам по тысяче рублей за человек по охране труда?2)  Да-да, смена.1)  Угу. Что решили? У вас получается 38 тысяч человек?2)  Так.2)  Ну, не рассматриваю вопрос, я тут приболел чуть-чуть,1)  Угу. Угу. Сергей Александрович, неактуально, понятно. То есть финансов нет у вас, да?2)  поэтому не получилось ничего посмотреть.2) 2)  Но в любом случае, на сегодняшний год это не актуально.2)  Да.2)  Да-да-да.1)  Угу. А, смотрите, Сергей Александрович, там сумма уже небольшая на человека выходит. Не рассматриваете такой вариант, чтобы оплатить не с бюджетных средств, а за свои обучиться?2)  У нас своих средств нет, вы полностью бюджетники.1)  Не, я имею в виду, каждый работник сам за себя оплатит. Не будете? Угу.2)  Нет, такого у нас не будет.2)  Нет.2)  Да, слушаю.2) 2) 2) 2) 1)  Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. Угу. У2)  Ну, вы мне на самом деле обещали прислать материалы2)  на почту какие-то, ничего не прислали?2)  От нас ничего не пришло.2)  Давайте вы мне оставите контакты в письме, которое пришлете,2)  я потом уже на свое усмотрение.1)  Угу. Угу.2)  Вероятней всего, да.2)  Да, я не знаю, что вы делаете, но я не знаю, что вы делаете.2) 2)  Да.2) 1)  Спасибо за внимание!2)  Всего доброго, до встречи.",
        "модуль_вовлеченности": "это Елена Владимировна, институт ААА. Мы с вами по обучению говорили",
        "не_результат": " У нас своих средств нет, вы полностью бюджетник"
    }
    buffer_agent.store_data(sample_data_1)
    buffer_agent.analyze_and_generate_suggestions()
    print(buffer_agent.data)
    buffer_agent.data.to_excel("buffer.xlsx")
