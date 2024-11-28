import logging


class Stylist:
    def __init__(self):
        self.logs = []
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    def process_data(self, data):
        # Получаем данные от "Ревизор" для финальной обработки
        structured_response = data.get("structured_response", "")
        reviewer_comments = data.get("reviewer_comments", [])

        if not structured_response:
            logging.error("Нет структурированных данных для обработки")
            return {"success": False, "message": "Нет структурированных данных для обработки"}

        # Добавляем комментарии к структурированному ответу
        final_output = self.apply_comments(structured_response, reviewer_comments)

        # Логируем результат
        self.logs.append("Финальная обработка завершена стилистом.")
        logging.info("Финальная обработка завершена стилистом.")

        # Передача данных обратно пользователю
        self.pass_to_next_agent("user", {"final_response": final_output})

    # def process_data(self, data):
    #     # Получаем данные от "Ревизор" для финальной обработки
    #     structured_response = data.get("structured_response", "")
    #     reviewer_comments = data.get("reviewer_comments", [])
    #     evaluators_labels = data.get("evaluators_labels", {})  # Добавлено: получаем данные от оценщиков
    #
    #     if not structured_response:
    #         logging.error("Нет структурированных данных для обработки")
    #         return {"success": False, "message": "Нет структурированных данных для обработки"}
    #
    #     # Добавляем комментарии к структурированному ответу
    #     final_output = self.apply_comments(structured_response, reviewer_comments)
    #
    #     # Добавляем информацию от оценщиков
    #     final_output += "\n\nОценки и лейблы от оценщиков:\n"
    #     for evaluator, labels in evaluators_labels.items():
    #         final_output += f"- {evaluator}: {labels}\n"
    #
    #     # Логируем результат
    #     self.logs.append("Финальная обработка завершена стилистом.")
    #     logging.info("Финальная обработка завершена стилистом.")
    #
    #     # Передача данных обратно пользователю
    #     self.pass_to_next_agent("user", {"final_response": final_output})

    def apply_comments(self, structured_response, reviewer_comments):
        # Обрабатываем структурированный ответ, добавляя комментарии ревизора
        final_output = f"Структурированный ответ:\n{structured_response}\n\nКомментарии ревизора:\n"
        for comment in reviewer_comments:
            final_output += f"- {comment}\n"

        return final_output

    def pass_to_next_agent(self, agent_name, data):
        # Передача результата пользователю
        if agent_name == "user":
            from user import User
            user_agent = User()
            user_agent.receive_final_output(data)


if __name__ == "__main__":
    stylist = Stylist()
    sample_data = {
        "structured_response": "Фраза менеджера: 'Привет, как дела?'. Фраза клиента: 'Всё нормально, спасибо.'",
        "reviewer_comments": ["Недостаточно убедительное приветствие", "Уточнить детали"]
    }
    stylist.process_data(sample_data)
