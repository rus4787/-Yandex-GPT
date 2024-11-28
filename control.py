import logging

class Control:
    def __init__(self):
        self.flags = {}
        self.counters = {}
        self.log_files = {}
        self.global_flag = False
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    def process_control(self, data):
        processed_text = data.get("processed_text", "")
        evaluators_indices = data.get("evaluators", [])

        if not processed_text:
            logging.error("Нет обработанного текста для контроля")
            return {"success": False, "message": "Нет обработанного текста"}

        # Инициализация флагов, счетчиков и логов для каждого "Оценщик_n"
        for evaluator in evaluators_indices:
            self.flags[evaluator] = False
            self.counters[evaluator] = 3
            self.log_files[evaluator] = []

        # Передача данных агенту "Ревизор" для первичной проверки и в Буфер
        logging.info(f"Передача данных агенту 'Ревизор' и в Буфер для первичной проверки: Оценщики - {evaluators_indices}")
        self.pass_to_next_agent("reviewer", {"processed_text": processed_text, "evaluators": evaluators_indices})
        self.pass_to_next_agent("buffer", {"text": processed_text, "evaluators": evaluators_indices})

    def receive_evaluator_response(self, evaluator_id, response):
        # Проверка полученного ответа от "Оценщик_n"
        task = response.get("task", "")
        prepared_response = response.get("response", "")
        text_indices = response.get("text_indices", [])

        if self._validate_response(task, prepared_response, text_indices):
            # Если ответ соответствует заданию
            self.flags[evaluator_id] = True
            self._log_action(evaluator_id, "Ответ принят. Установлен флаг True.")
            self.pass_to_next_agent("distributor", {"flag": True, "evaluator_id": evaluator_id, "response": prepared_response})
            self.pass_to_next_agent("reviewer", {"evaluator_id": evaluator_id, "log_file": self.log_files[evaluator_id]})
            self.pass_to_next_agent("buffer", {"evaluator_id": evaluator_id, "response": prepared_response})
        else:
            # Если ответ не соответствует заданию
            self.counters[evaluator_id] -= 1
            comment = f"Доработайте ответ. Осталось попыток: {self.counters[evaluator_id]}"
            self._log_action(evaluator_id, f"Ответ не соответствует. {comment}")

            if self.counters[evaluator_id] > 0:
                # Повторная передача задания в "Оценщик_n"
                self.pass_to_next_agent(f"evaluator_{evaluator_id}", {"flag": False, "comment": comment})
            else:
                # Если все попытки исчерпаны
                self._log_action(evaluator_id, "Контроль: Не может быть выполнено по причине: исчерпание попыток.")
                self.flags[evaluator_id] = True
                # Передаем итоговый результат и лог для регистрации "неудачи"
                self.pass_to_next_agent("distributor", {"flag": True, "evaluator_id": evaluator_id, "response": prepared_response})
                self.pass_to_next_agent("reviewer", {"evaluator_id": evaluator_id, "log_file": self.log_files[evaluator_id]})
                self.pass_to_next_agent("buffer", {"evaluator_id": evaluator_id, "response": prepared_response})

        # Проверка завершенности всех "Оценщик_n"
        if all(self.flags.values()):
            self.global_flag = True
            self._log_action("Контроль", "Все 'Оценщики' завершили работу, установлен глобальный флаг True.")

    def _validate_response(self, task, response, text_indices):
        # Проверка полноты и соответствия ответа "Оценщик_n" поставленной задаче
        if not response or not isinstance(response, str):
            return False

        # Проверка, что все текстовые индексы из text_indices были найдены в ответе
        missing_indices = [index for index in text_indices if index not in response]
        if missing_indices:
            return False

        if task and task not in response:
            return False

        if not response.strip():
            return False

        return True

    def receive_reviewer_feedback(self, evaluator_ids, comment):
        # Обработка флага "False" от "Ревизор"
        self.global_flag = False

        for evaluator_id in evaluator_ids:
            self.flags[evaluator_id] = False
            self.counters[evaluator_id] = 3
            self._log_action(evaluator_id, f"Ревизор: {comment}")

        # Передача списка оценщиков с флагом "ревизор" в "Распределитель"
        self.pass_to_next_agent("distributor", {"label": "ревизор", "evaluator_ids": evaluator_ids})

    def get_global_flag(self):
        return self.global_flag

    def _log_action(self, evaluator_id, action):
        if evaluator_id in self.log_files:
            self.log_files[evaluator_id].append({"action": action})
        else:
            self.log_files[evaluator_id] = [{"action": action}]
        logging.info(f"Оценщик_{evaluator_id}: {action}")

    def pass_to_next_agent(self, agent_name, data):
        if agent_name == "reviewer":
            from reviewer import Reviewer
            reviewer_agent = Reviewer()
            reviewer_agent.process_reviewer(data)
        elif agent_name == "distributor":
            from distributor import Distributor
            distributor_agent = Distributor()
            distributor_agent.receive_control_response(data)
        elif agent_name == "buffer":
            from buffer import Buffer
            buffer_agent = Buffer()
            buffer_agent.store_data(data)

if __name__ == "__main__":
    control = Control()
    sample_data = {"processed_text": "Клиент отказался от предложения", "evaluators": ["evaluator_1", "evaluator_2"]}
    control.process_control(sample_data)


# import logging
#
# class Control:
#     def __init__(self):
#         self.flags = {}
#         self.counters = {}
#         self.log_files = {}
#         self.global_flag = False
#         logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
#
#     def process_control(self, data):
#         processed_text = data.get("processed_text", "")
#         evaluators_indices = data.get("evaluators", [])
#
#         if not processed_text:
#             logging.error("Нет обработанного текста для контроля")
#             return {"success": False, "message": "Нет обработанного текста"}
#
#         # Инициализация флагов, счетчиков и логов для каждого "Оценщик_n"
#         for evaluator in evaluators_indices:
#             self.flags[evaluator] = False
#             self.counters[evaluator] = 3
#             self.log_files[evaluator] = []
#
#         # Передача данных агенту "Ревизор" для первичной проверки
#         logging.info(f"Передача данных агенту 'Ревизор' для первичной проверки: Оценщики - {evaluators_indices}")
#         self.pass_to_next_agent("reviewer", {"processed_text": processed_text, "evaluators": evaluators_indices})
#
#     def receive_evaluator_response(self, evaluator_id, response):
#         # Проверка полученного ответа от "Оценщик_n"
#         task = response.get("task", "")
#         prepared_response = response.get("response", "")
#         text_indices = response.get("text_indices", [])
#
#         if self._validate_response(task, prepared_response, text_indices):
#             # Если ответ соответствует заданию
#             self.flags[evaluator_id] = True
#             self._log_action(evaluator_id, "Ответ принят. Установлен флаг True.")
#             self.pass_to_next_agent("distributor", {"flag": True, "evaluator_id": evaluator_id, "response": prepared_response})
#             self.pass_to_next_agent("reviewer", {"evaluator_id": evaluator_id, "log_file": self.log_files[evaluator_id]})
#         else:
#             # Если ответ не соответствует заданию
#             self.counters[evaluator_id] -= 1
#             comment = f"Доработайте ответ. Осталось попыток: {self.counters[evaluator_id]}"
#             self._log_action(evaluator_id, f"Ответ не соответствует. {comment}")
#
#             if self.counters[evaluator_id] > 0:
#                 # Повторная передача задания в "Оценщик_n"
#                 self.pass_to_next_agent(f"evaluator_{evaluator_id}", {"flag": False, "comment": comment})
#             else:
#                 # Если все попытки исчерпаны
#                 self._log_action(evaluator_id, "Контроль: Не может быть выполнено по причине: исчерпание попыток.")
#                 self.flags[evaluator_id] = True
#                 # Передаем итоговый результат и лог для регистрации "неудачи"
#                 self.pass_to_next_agent("distributor", {"flag": True, "evaluator_id": evaluator_id, "response": prepared_response})
#                 self.pass_to_next_agent("reviewer", {"evaluator_id": evaluator_id, "log_file": self.log_files[evaluator_id]})
#
#         # Проверка завершенности всех "Оценщик_n"
#         if all(self.flags.values()):
#             self.global_flag = True
#             self._log_action("Контроль", "Все 'Оценщики' завершили работу, установлен глобальный флаг True.")
#
#     def _validate_response(self, task, response, text_indices):
#         # Проверка полноты и соответствия ответа "Оценщик_n" поставленной задаче
#         if not response or not isinstance(response, str):
#             return False
#
#         # Проверка, что все текстовые индексы из text_indices были найдены в ответе
#         missing_indices = [index for index in text_indices if index not in response]
#         if missing_indices:
#             return False
#
#         if task and task not in response:
#             return False
#
#         if not response.strip():
#             return False
#
#         return True
#
#     def receive_reviewer_feedback(self, evaluator_ids, comment):
#         # Обработка флага "False" от "Ревизор"
#         self.global_flag = False
#
#         for evaluator_id in evaluator_ids:
#             self.flags[evaluator_id] = False
#             self.counters[evaluator_id] = 3
#             self._log_action(evaluator_id, f"Ревизор: {comment}")
#
#         # Передача списка оценщиков с флагом "ревизор" в "Распределитель"
#         self.pass_to_next_agent("distributor", {"label": "ревизор", "evaluator_ids": evaluator_ids})
#
#     def get_global_flag(self):
#         return self.global_flag
#
#     def _log_action(self, evaluator_id, action):
#         if evaluator_id in self.log_files:
#             self.log_files[evaluator_id].append({"action": action})
#         else:
#             self.log_files[evaluator_id] = [{"action": action}]
#         logging.info(f"Оценщик_{evaluator_id}: {action}")
#
#     def pass_to_next_agent(self, agent_name, data):
#         if agent_name == "reviewer":
#             from reviewer import Reviewer
#             reviewer_agent = Reviewer()
#             reviewer_agent.process_reviewer(data)
#         elif agent_name == "distributor":
#             from distributor import Distributor
#             distributor_agent = Distributor()
#             distributor_agent.receive_control_response(data)
#
# if __name__ == "__main__":
#     control = Control()
#     sample_data = {"processed_text": "Клиент отказался от предложения", "evaluators": ["evaluator_1", "evaluator_2"]}
#     control.process_control(sample_data)
