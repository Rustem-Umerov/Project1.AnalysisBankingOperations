import json
from pathlib import Path
from typing import Union

import pandas as pd

from src.logging import get_logger
from src.utils import read_excel_file

logger = get_logger(__name__)


def filter_date(
        dataframe: pd.DataFrame, year: Union[int, str], month: Union[int, str]) -> pd.DataFrame:
    """
    Фильтрует df и оставляет только те транзакции, которые соответствуют заданному году и месяцу.

    :param dataframe: Исходный pd.DataFrame
    :param year: Год
    :param month: Месяц

    :return: Новая копия DataFrame, отфильтрованная по year и month.
    """

    try:
        column = "Дата операции"
        dt = dataframe.copy()

        dt[column] = pd.to_datetime(dt[column], format="%d.%m.%Y %H:%M:%S", errors="coerce")

        y = int(year)
        m = int(month)

        mask = (dt[column].dt.year == y) & (dt[column].dt.month == m)
        return dt.loc[mask]

    except (ValueError, TypeError):
        logger.exception("Ошибка преобразования даты.")
        raise
    except KeyError:
        logger.exception("В DataFrame отсутствует колонка 'Дата операции'.")
        raise
    except Exception:
        logger.exception("Неожиданная ошибка при фильтрации по дате.")
        raise


def group_categories(df: pd.DataFrame) -> pd.Series:
    """Группирует транзакции по категориям и возвращает Series, где index=Категория, value=сумма кэшбэка."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"df должен быть pd.DataFrame, а получен {type(df).__name__}")

    try:
        return df.groupby("Категория")["Кэшбэк"].sum()
    except KeyError:
        logger.exception("Отсутствует необходимая колонка в DataFrame.")
        raise
    except Exception:
        logger.exception("Неожиданная ошибка при группировке.")
        raise


def favorable_categories(df_path: Path, year: Union[int, str], month: Union[int, str]) -> str:
    """
    Главная функция.

    :param df_path: Путь к файлу.
    :param year: Год.
    :param month: Месяц.

    :return: JSON-ответ.

    Данная функция - это главная функция, которая объединяет второстепенные функции.
    Функция получает путь к файлу, год, месяц.
    Далее функция read_excel_file читает файл.
    Далее функция filter_date фильтрует по году и месяцу.
    Далее функция group_categories группирует по категориям и суммирует все кэшбэки.
    """

    if not isinstance(year, (int, str)) or not isinstance(month, (int, str)):
        raise TypeError(
            f"Неверный тип входных данных. Должны быть int или str, "
            f"а получены {type(year).__name__}, {type(month).__name__}"
        )

    try:
        df = read_excel_file(df_path)  # функция читающая excel-файл
        logger.info("Функция read_excel_file успешно отработала.")

        filter_by_date = filter_date(df, year, month)  # фильтрует по году и месяцу
        logger.info("Функция filter_date успешно отработала.")

        group_by_categories = group_categories(filter_by_date)  # группирует по категориям
        logger.info("Функция group_categories успешно отработала.")

        return json.dumps(group_by_categories.to_dict(), indent=4, ensure_ascii=False)

    except (TypeError, OverflowError):
        logger.exception("Ошибка преобразования данных в JSON.")
        raise
    except Exception:
        logger.exception("Неожиданная ошибка в основной функции.")
        raise
