import pandas as pd
from src.views import read_excel_file
from typing import Union
from pathlib import Path
import json


def filter_date(dataframe: pd.DataFrame, year: Union[int, str], month: Union[int, str]) -> pd.DataFrame:
    """
    Фильтрует df и оставляет только те транзакции, которые соответствуют заданному году и месяцу.

    :param dataframe: Исходный pd.DataFrame
    :param year: Год
    :param month: Месяц

    :return: Новая копия DataFrame, отфильтрованная по year и month.
    """

    column = "Дата операции"
    dt = dataframe.copy()

    dt[column] = pd.to_datetime(dt[column], format="%d.%m.%Y %H:%M:%S")

    y = int(year)
    m = int(month)

    mask = (dt[column].dt.year == y) & (dt[column].dt.month == m)
    return dt.loc[mask]


def group_categories(df: pd.DataFrame) -> pd.Series:
    """Группирует транзакции по категориям и возвращает Series, где index=Категория, value=сумма кэшбэка."""

    return df.groupby("Категория")["Кэшбэк"].sum()


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

    df = read_excel_file(df_path)  # функция читающая excel-файл
    filter_by_date = filter_date(df, year, month)  # фильтрует по году и месяцу

    group_by_categories = group_categories(filter_by_date)  # группирует по категориям

    return json.dumps(group_by_categories.to_dict(), indent=4, ensure_ascii=False)
