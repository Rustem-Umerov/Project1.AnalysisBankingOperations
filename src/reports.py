from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

from src.logging import get_logger
from src.views import data_from_time_range, filter_negative_transactions, read_excel_file

logger = get_logger(__name__)


def date_range_calculation(date_str: Optional[str] = None, frmt: str = "%d.%m.%Y") -> date:
    """
    Функция определяет дату. Если пользователь передал дату, то дата (тип str) переводится в дату (тип date).
    Если пользователь не передал дату, то берется текущая дата.

    :param date_str: Дата (опционально).
    :param frmt: Формат даты.
    :return: Дата, которая будет концом временного диапазона.
    """

    if not isinstance(date_str, str):
        raise TypeError(f"date_str должен быть str или None, а получен {type(date_str).__name__}")

    if date_str:
        try:
            return datetime.strptime(date_str, frmt).date()
        except ValueError:
            print("Неправильный формат даты %r, ожидается %s", date_str, frmt)
            raise
    return date.today()


def spending_by_category(transactions: pd.DataFrame, category: str) -> pd.DataFrame:
    """
    Функция фильтрует DataFrame и оставляет только те транзакции, которые соответсвуют указанной категории.

    :param transactions: DataFrame.
    :param category: Категория.
    :return: DataFrame
    """

    if not isinstance(transactions, pd.DataFrame):
        raise TypeError(f"transactions должен быть pd.DataFrame, а получен {type(transactions).__name__}")

    if not isinstance(category, str):
        raise TypeError(f"category должен быть str, а получен {type(category).__name__}")

    try:
        df = transactions.copy()
        column = "Категория"
        final_category = category.strip().lower()
        df[column] = df[column].fillna("").str.lower().str.strip()
        filter_category = df[df[column] == final_category]
        return filter_category

    except Exception:
        logger.exception("Не удалось отфильтровать транзакции по категории %r", category)
        raise


def final_transactions(excel_file_path: Path, category: str, date_str: Optional[str] = None) -> pd.DataFrame:
    """
    Данная функция - это главная функция, которая объединяет второстепенные функции.
    Функция получает путь к файлу, наименование категории, дату(опционально).
    Далее функция read_excel_file читает файл и возвращает DataFrame.
    Далее функция date_range_calculation определяет конец временного диапазона.
    Далее, в переменной start_date, вычисляется начало временного диапазона.
    Далее функция data_from_time_range фильтрует DataFrame по дате.
    Далее функция filter_negative_transactions оставляет только расходы.
    Далее функция spending_by_category фильтрует по определенной категории.

    :param excel_file_path: Путь к файлу.
    :param category: Категория.
    :param date_str: Дата(опционально).
    :return: Готовый DataFrame.
    """

    try:
        df = read_excel_file(excel_file_path)  # читает excel файл и возвращает DataFrame
        logger.info("Функция read_excel_file успешно отработала.")

        end_date = date_range_calculation(date_str)  # определяет конец временного диапазона
        logger.info("Функция date_range_calculation успешно отработала.")

        start_date = end_date - relativedelta(months=3)  # определяет начало временного диапазона

        filter_data = data_from_time_range(df, (start_date, end_date))  # фильтрует по дате
        logger.info("Функция data_from_time_range успешно отработала.")

        filter_negative_tr = filter_negative_transactions(filter_data)  # оставляет только расходы
        logger.info("Функция filter_negative_transactions успешно отработала.")

        filter_by_category = spending_by_category(filter_negative_tr, category)  # фильтрует по определенной категории
        logger.info("Функция spending_by_category успешно отработала.")

        return filter_by_category

    except FileNotFoundError:
        logger.exception("Файл: %s, не найден.", excel_file_path)
        raise
    except ValueError:
        logger.exception("Неверные входные данные.")
        raise
    except Exception:
        logger.exception("Не удалось получить транзакции по категории %r.", category)
        raise
