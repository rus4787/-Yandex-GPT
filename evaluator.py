import re
import logging


class Evaluator:
    def __init__(self, evaluator_id):
        self.evaluator_id = evaluator_id
        self.log = []  # Логирование действий агента
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    def evaluate_text(self, data):
        processed_text = data.get("processed_text", "")
        response = {}

        if not processed_text:
            logging.error("Нет обработанного текста для оценки")
            return {"success": False, "message": "Нет обработанного текста"}

        logging.info(f"Оценка текста оценщиком {self.evaluator_id}")

        # Оценка текста в зависимости от типа оценщика
        if self.evaluator_id == 1:
            response = self._evaluate_engagement_module(processed_text)
        elif self.evaluator_id == 2:
            response = self._evaluate_approach(processed_text)
        elif self.evaluator_id == 3:
            response = self._evaluate_engagement_summary(processed_text)
        elif self.evaluator_id == 4:
            response = self._evaluate_non_result(processed_text)
        elif self.evaluator_id == 5:
            response = self._evaluate_application(processed_text)
        elif self.evaluator_id == 6:
            response = self._evaluate_action(processed_text)
        elif self.evaluator_id == 7:
            response = self._evaluate_other(processed_text)

        logging.info(f"Оценка текста завершена оценщиком {self.evaluator_id}, передача данных в 'Контроль'")

        # Передача данных следующему агенту - "Контроль"
        self.pass_to_next_agent("control", {
            "evaluator_id": self.evaluator_id,
            "response": response,
            "log": self.log
        })

        return response

    def _evaluate_engagement_module(self, text):
        phrases = re.findall(r"М: (.+?)(?= К:|$)", text)[:5]  # Извлекаем первые 5 фраз менеджера
        response = {
            "engagement_module": phrases,
            "result": self._assess_result(phrases),
            "suitable": True
        }
        self.log_action(f"Оценка модуля вовлеченности, извлеченные фразы: {phrases}")
        return response

    def _evaluate_approach(self, text):
        approach_phrases = re.findall(r"М: (.+?)(?= К:|$)", text)[:3]
        response = {
            "approach": approach_phrases,
            "result": self._assess_result(approach_phrases),
            "suitable": True
        }
        self.log_action(f"Оценка захода менеджера, извлеченные фразы: {approach_phrases}")
        return response

    def _evaluate_engagement_summary(self, text):
        summary_phrases = re.findall(r"М: (.+?)(?= К:|$)", text)[:5]
        response = {
            "engagement_summary": summary_phrases,
            "suitable": True
        }
        self.log_action(f"Оценка модуля вовлеченности (обобщенный), извлеченные фразы: {summary_phrases}")
        return response

    def _evaluate_non_result(self, text):
        non_result_phrases = re.findall(r"К: (.+?)(?= М:|$)", text)
        manager_attempts = len(re.findall(r"М: (.+?)(?= К:|$)", text))
        response = {
            "non_result_phrases": non_result_phrases,
            "manager_attempts": manager_attempts,
            "reason": "Менеджер не смог преодолеть возражение клиента"
        }
        self.log_action(f"Оценка 'не-результата', извлеченные фразы: {non_result_phrases}")
        return response

    def _evaluate_application(self, text):
        application_phrases = re.findall(r"М: (.+?)(?= К:|$)", text)
        response = {
            "application_phrases": application_phrases,
            "client_agreement": "Точная фраза клиента, выражающая согласие на заявку",
            "contributing_factors": "Факторы, способствующие заявке"
        }
        self.log_action(f"Оценка заявки, извлеченные фразы: {application_phrases}")
        return response

    def _evaluate_action(self, text):
        action_phrases = re.findall(r"М: (.+?)(?= К:|$)", text)
        response = {
            "action_phrases": action_phrases,
            "client_interest": "Фраза клиента, проявляющая интерес",
            "action_classification": "Тип действия, достигнутого в результате"
        }
        self.log_action(f"Оценка действий, извлеченные фразы: {action_phrases}")
        return response

    def _evaluate_other(self, text):
        other_phrases = re.findall(r"М: (.+?)(?= К:|$)", text)
        response = {
            "other_phrases": other_phrases,
            "classification": "Классификация выявленных новых действий или интересов"
        }
        self.log_action(f"Оценка 'другое', извлеченные фразы: {other_phrases}")
        return response

    def log_action(self, message):
        self.log.append(f"Оценщик_{self.evaluator_id}: {message}")
        logging.info(message)

    def pass_to_next_agent(self, agent_name, data):
        if agent_name == "control":
            from control import Control
            control_agent = Control()
            control_agent.process_control(data)

    def evaluate_text(self, data):
        processed_text = data.get("processed_text", "")
        response = self._evaluate_engagement_module(processed_text)
        # Другие операции...

    def _evaluate_engagement_module(self, processed_text):
        # Ваш код для оценки модуля вовлеченности
        phrases = self.extract_key_phrases(processed_text)
        return {
            "result": self._assess_result(phrases),
            "engagement_score": self._calculate_engagement_score(phrases)
        }

    def _assess_result(self, phrases):
        # Реализация метода _assess_result
        # Здесь вы можете провести анализ фраз, чтобы определить результат
        if not phrases:
            return "Нет ключевых фраз для оценки"

        # Простая проверка для примера
        for phrase in phrases:
            if "неопределенность" in phrase or "проблема" in phrase:
                return "Отрицательный результат"
        return "Положительный результат"

    def extract_key_phrases(self, text):
        # Метод для извлечения ключевых фраз из текста
        return text.split('.')  # Примерное разделение текста на фразы

    def _calculate_engagement_score(self, phrases):
        # Метод для расчета вовлеченности
        return len(phrases)  # Простой пример: количество фраз в тексте


if __name__ == "__main__":
    evaluator = Evaluator(1)
    sample_data = {"processed_text": "М: Привет, как дела? К: Всё нормально, спасибо."}
    evaluator.evaluate_text(sample_data)
