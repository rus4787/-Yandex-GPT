from prompts import PROMPT_DISTRIBUTOR

class Distributor:
    def __init__(self):
        self.evaluators_indices = []
        self.evaluators_done_indices = []
        self.evaluators_count = 0
        self.agent_flags = {}  # Для хранения флагов состояния агентов

    def process_distribution(self, data):
        processed_text = data.get("processed_text", "")
        labels = data.get("labels", [])

        # Группируем лейблы по типам оценщиков
        evaluators_map = {
            "Оценщик_1": ["холодный", "разговор с лпр"],
            "Оценщик_2": ["холодный", "нет лпр"],
            "Оценщик_3": ["теплый", "разговор с лпр"],
            "Оценщик_4": ["отказ", "частичный отказ", "неявный отказ"],
            "Оценщик_5": ["заявка"],
            "Оценщик_6": ["действие", "пассивное согласие", "согласие с оговорками"],
            "Оценщик_7": ["другое"]
        }

        # Формируем список оценщиков, которые будут работать с текстом
        self.evaluators_indices = [key for key, value in evaluators_map.items() if any(label in labels for label in value)]
        self.evaluators_count = len(self.evaluators_indices)

        # Передаем обработанный текст и список индексов в "Control"
        self.pass_to_next_agent("control", {"processed_text": processed_text, "evaluators": self.evaluators_indices})

        # Передаем обработанный текст каждому оценщику
        for evaluator in self.evaluators_indices:
            self.pass_to_next_agent(evaluator, {"processed_text": processed_text})

    def receive_control_response(self, control_response):
        # Обработка ответа от "Control"
        if control_response.get("label") == "ревизор":
            # Получаем список индексов оценщиков на переработку
            failed_evaluators = control_response.get("evaluators", [])
            for evaluator in failed_evaluators:
                self.pass_to_next_agent(evaluator, {"processed_text": "Повторная обработка", "comment": "Нужна доработка по итогам ревизора"})

        elif control_response.get("success"):
            evaluator_index = control_response.get("evaluator_index")
            if evaluator_index:
                self.evaluators_done_indices.append(evaluator_index)
                # Передаем ответ в "Accumulator"
                self.pass_to_next_agent("accumulator", {"processed_text": control_response.get("text"), "evaluator_index": evaluator_index})

            # Проверяем, завершена ли работа всех оценщиков
            if len(self.evaluators_done_indices) == self.evaluators_count:
                # Запрашиваем флаги у всех оценщиков
                all_evaluators_true = all([self.get_flag(evaluator) for evaluator in self.evaluators_indices])
                if all_evaluators_true:
                    # Запрашиваем флаг у "Control"
                    if self.get_flag("control"):
                        # Передаем флаг "True" в "Accumulator"
                        self.pass_to_next_agent("accumulator", {"flag": True})
                else:
                    # Обработка случая с флагом "False" у "Control"
                    failed_evaluators = [evaluator for evaluator in self.evaluators_indices if not self.get_flag(evaluator)]
                    for failed_evaluator in failed_evaluators:
                        self.pass_to_next_agent(failed_evaluator, {"processed_text": "Повторная обработка"})

                    # Повторно проверяем после получения данных от оценщика
                    all_evaluators_true = all([self.get_flag(evaluator) for evaluator in self.evaluators_indices])
                    if all_evaluators_true:
                        # Передаем данные в "Accumulator"
                        self.pass_to_next_agent("accumulator", {"flag": True})
                    else:
                        # Логируем ошибку и передаем лог в накопитель
                        log_error = "Оценщик не может обработать данные"
                        self.pass_to_next_agent("accumulator", {"log_error": log_error})

    def pass_to_next_agent(self, agent_name, data):
        # Метод передачи данных следующему агенту
        if agent_name == "control":
            from control import Control
            control_agent = Control()
            control_agent.process_control(data)

        elif agent_name.startswith("Оценщик"):
            from evaluator import Evaluator
            evaluator_id = int(agent_name.split("_")[1])
            evaluator = Evaluator(evaluator_id)
            evaluator.evaluate_text(data)

        elif agent_name == "accumulator":
            from accumulator import Accumulator
            accumulator_agent = Accumulator()
            accumulator_agent.accumulate_data(data)

    def get_flag(self, agent_name):
        # Метод для получения флага состояния агента
        # Здесь мы эмулируем получение состояния агента
        if agent_name not in self.agent_flags:
            # Если флаг для агента еще не установлен, задаем начальное значение False
            self.agent_flags[agent_name] = False

        # Логика обновления флага, имитирующая успех после некоторой обработки
        # В реальной системе это значение будет обновляться в зависимости от состояния агента
        if agent_name in self.evaluators_indices and agent_name not in self.evaluators_done_indices:
            # Если оценщик уже завершил работу, задаем ему флаг True
            self.agent_flags[agent_name] = True
        elif agent_name == "control" and all(evaluator in self.evaluators_done_indices for evaluator in self.evaluators_indices):
            # Флаг "True" для "Control", если все оценщики завершили работу
            self.agent_flags[agent_name] = True

        return self.agent_flags[agent_name]

if __name__ == "__main__":
    distributor_agent = Distributor()
    # Пример данных для обработки
    example_data = {
        "processed_text": "Привет, это первый контакт. Мы проводим презентацию продукта и хотели бы узнать ваше мнение.",
        "labels": ["холодный", "разговор с лпр"]
    }
    distributor_agent.process_distribution(example_data)
