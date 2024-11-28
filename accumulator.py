import logging
import re

class Accumulator:
    def __init__(self):
        self.data = []
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    def accumulate_data(self, data):
        # Получает данные от "Распределитель" и накапливает их
        if not data:
            logging.error("Нет данных для накопления")
            return {"success": False, "message": "Нет данных для накопления"}

        self.data.append(data)
        logging.info(f"Данные накоплены: {data}")
        return {"success": True, "accumulated_data": self.data}

    def primary_text_processing(self):
        # Проводит первичную обработку текста: выделяет цитаты абонентов и комментарии агентов
        processed_data = []
        for entry in self.data:
            text = entry.get("processed_text", "")
            if text:
                quotes = re.findall(r"К: (.+?)(?: М:|$)", text)  # Извлекаем все фразы клиента
                comments = entry.get("comment", "")
                agent = entry.get("agent", "")
                processed_data.append({"quotes": quotes, "comments": comments, "agent": agent})

        self.data = processed_data
        logging.info(f"Первичная обработка текста завершена. Обработанные данные: {processed_data}")
        return processed_data

    def remove_duplicates(self):
        # Удаляет все дубликаты, оставляя только последний ответ каждого "Оценщик_n"
        unique_data = {}
        for entry in self.data:
            agent = entry.get("agent")
            if agent:
                unique_data[agent] = entry  # Последний элемент с данным агентом перепишет предыдущие

        self.data = list(unique_data.values())
        logging.info(f"Дубликаты удалены. Уникальные данные: {self.data}")
        return self.data

    def receive_flag_true(self):
        # Если от "Распределитель" поступил флаг "True", структурируем данные и передаем их в "Ревизор"
        if self.data:
            structured_data = {"agents": self.data}
            logging.info(f"Передача данных в 'Ревизор': {structured_data}")
            self.pass_to_next_agent("reviewer", structured_data)

    def pass_to_next_agent(self, agent_name, data):
        # Метод для передачи данных следующему агенту
        if agent_name == "reviewer":
            from reviewer import Reviewer
            reviewer_agent = Reviewer()
            reviewer_agent.process_reviewer(data)

if __name__ == "__main__":
    accumulator = Accumulator()
    sample_data = {
        "processed_text": "К: Здравствуйте, хочу узнать больше о вашем продукте М: Конечно, расскажу.",
        "agent": "evaluator_1"
    }
    accumulator.accumulate_data(sample_data)
    accumulator.primary_text_processing()
    accumulator.remove_duplicates()
    accumulator.receive_flag_true()
