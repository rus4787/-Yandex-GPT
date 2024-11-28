from prompts import PROMPT_LABEL

class Label:
    def __init__(self):
        self.count = 0  # Счетчик для повторной обработки

    def process_label(self, data):
        processed_text = data.get("processed_text", "")
        char_count = data.get("char_count", 0)
        labels = []

        # Оценка количества символов
        if char_count < 150:
            labels.append("короткий")
            # Передаем текст следующему агенту - "Стилист", так как текст слишком короткий
            self.pass_to_next_agent("stylist", {"processed_text": processed_text, "labels": labels})
            return {"success": False, "message": "Короткий текст", "labels": labels}

        # Оценка типа разговора
        if "это не я" in processed_text or "я не отвечаю за это" in processed_text or "он отсутствует" in processed_text:
            labels.append("нет лпр")
        else:
            labels.append("разговор с лпр")

        # Оценка типа клиента
        if "впервые" in processed_text or "знакомство" in processed_text or "презентация продукта" in processed_text:
            labels.append("холодный")
        else:
            labels.append("теплый")

        # Проверка комбинации "теплый" и "нет лпр"
        if "теплый" in labels and "нет лпр" in labels:
            # Передаем текст следующему агенту - "Стилист"
            self.pass_to_next_agent("stylist", {"processed_text": processed_text, "labels": labels})
            return {"success": False, "message": "Теплый клиент без ЛПР", "labels": labels}

        # Оценка структуры разговора
        if "категорично отказывается" in processed_text or "отказ от сотрудничества" in processed_text:
            labels.append("отказ")
        elif "заявка" in processed_text or "сформируем заявку" in processed_text:
            labels.append("заявка")
        elif "просмотр удостоверения" in processed_text or "согласование сроков" in processed_text:
            labels.append("действие")
        else:
            labels.append("другое")

        # Проверка наличия лейблов
        if not labels:
            self.count += 1
            if self.count <= 1:
                # Повторная обработка текста
                self.pass_to_next_agent("processor", {"text": data["original_text"]})
                return {"success": False, "message": "Повторная обработка текста", "labels": labels}
            else:
                # Передаем текст следующему агенту - "Стилист" с пометкой об отсутствии лейблов
                self.pass_to_next_agent("stylist", {"processed_text": processed_text, "labels": ["отсутствуют лейблы"]})
                return {"success": False, "message": "Лейблы не найдены после повторной обработки", "labels": labels}

        # Передача обработанного текста и лейблов следующему агенту - "Распределитель"
        self.pass_to_next_agent("distributor", {"processed_text": processed_text, "labels": labels})
        return {"success": True, "labels": labels}

    def pass_to_next_agent(self, agent_name, data):
        # Метод передачи данных следующему агенту
        if agent_name == "stylist":
            from stylist import Stylist
            stylist = Stylist()
            stylist.process_data(data)

        elif agent_name == "distributor":
            from distributor import Distributor
            distributor = Distributor()
            distributor.process_distribution(data)

        elif agent_name == "processor":
            from processor import Processor
            processor = Processor()
            processor.process(data.get("text"))

if __name__ == "__main__":
    label_agent = Label()
    # Пример данных для обработки
    example_data = {
        "processed_text": "Привет, это первый контакт. Мы проводим презентацию продукта и хотели бы узнать ваше мнение.",
        "char_count": 180,
        "original_text": "Привет, это первый контакт. Мы проводим презентацию продукта и хотели бы узнать ваше мнение."
    }
    result = label_agent.process_label(example_data)
    print(result)
