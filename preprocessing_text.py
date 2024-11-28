import pandas as pd
import logging

class PreprocessingText:
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    # Загрузка таблицы из файла Excel
    def load_table(self, filepath):
        try:
            df = pd.read_excel(filepath)
            # Выделение необходимых столбцов
            df = df[['id', 'user_id', 'org_id', 'zayavka_id', 'created', 'text']]
            logging.info(f"Загруженные данные: {df.head(2)}")
            return df
        except FileNotFoundError:
            logging.error("Файл не найден. Проверьте путь к файлу.")
            return None
        except Exception as e:
            logging.error(f"Ошибка при загрузке файла: {e}")
            return None

    # Фильтрация данных на основе параметров: дата и количество строк
    def filter_data(self, df, row_count=None, date=None, additional_filter=None):
        if df is None:
            return None
        try:
            filtered_df = df.tail(50) if row_count is None else df.tail(row_count)
            logging.info(f"Отфильтрованные данные: {filtered_df.head()}")
            return filtered_df
        except Exception as e:
            logging.error(f"Ошибка при фильтрации данных: {e}")
            return None

    # Основная функция для работы с модулем preprocessing_text
    def preprocessing_main(self, filepath, row_count=None, date=None, additional_filter=None):
        df = self.load_table(filepath)
        filtered_df = self.filter_data(df, row_count, date, additional_filter)
        if filtered_df is not None:
            logging.info("Предобработка завершена успешно")
        return filtered_df


if __name__ == "__main__":
    filepath = "C:/Users/khabi/Python_project/barnaul/base_work/data_call_extended.xlsx"
    preprocessing = PreprocessingText()
    preprocessed_data = preprocessing.preprocessing_main(filepath)
