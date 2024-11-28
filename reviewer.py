import logging

class Reviewer:
    def __init__(self):
        self.working_evaluators = {}
        self.reviewer_log = []
        self.counter = 1
        self.global_flag = False
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    def process_reviewer(self, data):
        processed_text = data.get("processed_text", "")
        evaluators_indices = data.get("evaluators", [])

        if not processed_text:
            logging.error("Нет обработанного текста для проверки")
            return {"success": False, "message": "Нет обработанного текста"}

        # Формируем список работающих "Оценщик_n" и устанавливаем им флаги "False"
        for evaluator in evaluators_indices:
            self.working_evaluators[evaluator] = False

        logging.info(f"Ревизор получил текст для проверки. Оценщики: {evaluators_indices}")

    def receive_control_log(self, evaluator_id, log_file):
        # Получает лог-файл от "Контроль" и изучает его
        for log_entry in log_file:
            if "Контроль: Не может быть выполнено по причине" in log_entry.get("comment", ""):
                self.reviewer_log.append({"evaluator_id": evaluator_id, "comment": log_entry["comment"]})
                logging.info(f"Ревизор получил лог-файл с ошибками от оценщика {evaluator_id}")

    def receive_accumulator_data(self, structured_data):
        # Получает данные от "Накопитель"
        evaluator_data = {evaluator.get("agent"): evaluator for evaluator in structured_data.get("agents", [])}
        inconsistencies_found = False

        for evaluator_id, evaluator in evaluator_data.items():
            if evaluator_id in self.working_evaluators:
                log_file = self.reviewer_log
                for log_entry in log_file:
                    if log_entry["evaluator_id"] == evaluator_id and "не устранено" in log_entry.get("comment", ""):
                        inconsistencies_found = True
                        evaluator["status"] = "needs revision"
                        log_comment = f"Ревизор: Недостаток для Оценщик_{evaluator_id} - {log_entry.get('comment')}"
                        self.reviewer_log.append({"evaluator_id": evaluator_id, "comment": log_comment})
                        logging.info(f"Ревизор обнаружил несоответствие у оценщика {evaluator_id}")
                        break

                if not inconsistencies_found:
                    self.working_evaluators[evaluator_id] = True

        # Проверка счетчика и отправка на доработку
        if inconsistencies_found:
            self.counter -= 1
            if self.counter > 0:
                for evaluator_id, evaluator in evaluator_data.items():
                    if evaluator.get("status") == "needs revision":
                        self.pass_to_next_agent("control", {"evaluator_id": evaluator_id, "comment": evaluator.get("comment")})
            else:
                for evaluator_id, evaluator in evaluator_data.items():
                    if evaluator.get("status") == "needs revision":
                        self.reviewer_log.append({"evaluator_id": evaluator_id, "comment": f"Ревизор: Не может быть выполнено по причине - недостаток не устранен."})
                        logging.error(f"Оценщик {evaluator_id} не смог устранить недостаток после всех попыток")

    def finalize_review(self):
        # Если все "Оценщики" завершили работу или исчерпаны все попытки
        if all(self.working_evaluators.values()) or self.counter == 0:
            final_response = {
                "structured_response": "",
                "reviewer_comments": []
            }
            for log_entry in self.reviewer_log:
                final_response["reviewer_comments"].append(log_entry.get("comment"))

            self.pass_to_next_agent("stylist", final_response)
            self.global_flag = True
            logging.info("Ревизор завершил проверку и передал данные стилисту")

    # def finalize_review(self):
    #     # Если все "Оценщики" завершили работу или исчерпаны все попытки
    #     if all(self.working_evaluators.values()) or self.counter == 0:
    #         final_response = {
    #             "structured_response": "",
    #             "reviewer_comments": [],
    #             "evaluators_labels": {}  # Добавлено: лейблы от оценщиков
    #         }
    #         for log_entry in self.reviewer_log:
    #             final_response["reviewer_comments"].append(log_entry.get("comment"))
    #
    #         # Добавляем данные от всех оценщиков, если они завершили работу успешно
    #         for evaluator_id, completed in self.working_evaluators.items():
    #             if completed:
    #                 evaluator_data = self.working_evaluators[evaluator_id]
    #                 final_response["evaluators_labels"][evaluator_id] = evaluator_data  # Сохраняем данные от оценщиков
    #
    #         self.pass_to_next_agent("stylist", final_response)
    #         self.global_flag = True
    #         logging.info("Ревизор завершил проверку и передал данные стилисту")

    def pass_to_next_agent(self, agent_name, data):
        # Метод для передачи данных следующему агенту
        if agent_name == "control":
            from control import Control
            control_agent = Control()
            control_agent.receive_reviewer_feedback(data.get("evaluator_id"), data.get("comment"))

        elif agent_name == "stylist":
            from stylist import Stylist
            stylist_agent = Stylist()
            stylist_agent.process_data(data)

    def get_flag(self):
        return self.global_flag

if __name__ == "__main__":
    reviewer = Reviewer()
    sample_data = {"processed_text": "М: Привет, как дела? К: Всё нормально, спасибо.", "evaluators": ["evaluator_1", "evaluator_2"]}
    reviewer.process_reviewer(sample_data)
