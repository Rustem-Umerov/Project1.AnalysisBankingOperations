import json
import os
from datetime import datetime, time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

from src.logging import get_logger

logger = get_logger(__name__)

SRC_DIR = Path(__file__).resolve().parent
EXCEL_PATH = SRC_DIR.parent / "data" / "operations.xlsx"
JSON_PATH = SRC_DIR.parent / "user_settings.json"

load_dotenv()
API_KEY_1 = os.getenv("API_KEY_1")
API_KEY_2 = os.getenv("API_KEY_2")


def date_range(input_date: str) -> tuple[datetime, datetime]:
    """Функция принимает дату в формате "%d.%m.%Y %H:%M:%S" и возвращает список двух дат:
    - начало месяца (1-е число данного месяца)
    - дата из входной строки с обнулённым временем (полночь)."""

    if not isinstance(input_date, str):
        raise TypeError(f"input_date должен быть str, а получен {type(input_date).__name__}")

    try:
        date_obj = datetime.strptime(input_date, "%d.%m.%Y %H:%M:%S")
        logger.info("Полученная от пользователя дата: %s, преобразована в datetime.", input_date)
    except ValueError as e:
        raise ValueError(f"Неверный формат даты: {input_date}. Ожидается '%d.%m.%Y %H:%M:%S'") from e

    start_date = datetime(date_obj.year, date_obj.month, 1)
    logger.info("Дата начала: %s и дата конца: %s успешно определена.", start_date, date_obj)

    return start_date, date_obj


def greetings(str_date_time: str) -> str:
    """Возвращает приветствие в зависимости от полученного времени.

    Интервалы определяются следующим образом:
      - Доброе утро: с 05:00 до 12:00 (включительно 05:00, исключая 12:00)
      - Добрый день: с 12:00 до 18:00
      - Добрый вечер: с 18:00 до 23:00
      - Доброй ночи: с 23:00 до 05:00 (включая ночной интервал через полночь)"""

    default = "Добрый день"
    if not isinstance(str_date_time, str):
        logger.error("Ожидали строку, получили %r", str_date_time)
        return default

    if len(str_date_time.split(maxsplit=1)) != 2:
        logger.error("Неверный формат входа: %r", str_date_time)
        return default

    try:
        str_time = str_date_time.split()[1]
        time_dt = datetime.strptime(str_time, "%H:%M:%S").time()
        logger.info("Время полученное от пользователя: %s, успешно преобразовано в datetime.", str_date_time)

        morning = time(5, 0, 0)
        afternoon = time(12, 0, 0)
        evening = time(18, 0, 0)
        night = time(23, 0, 0)

        if morning <= time_dt < afternoon:
            result = "Доброе утро"
        elif afternoon <= time_dt < evening:
            result = "Добрый день"
        elif evening <= time_dt < night:
            result = "Добрый вечер"
        else:
            result = "Доброй ночи"

        return result

    except ValueError:
        logger.exception("Ошибка обработки времени: %r", str_date_time)
        return default


def read_excel_file(excel_file_path: Path) -> pd.DataFrame:
    """Читает Excel-файл по указанному пути и возвращает DataFrame."""

    try:
        result = pd.read_excel(excel_file_path)
        logger.info("Excel-файл: %s, успешно прочитан.", excel_file_path)
        return result
    except FileNotFoundError:
        logger.exception("Файл не найден: %s", excel_file_path)
        raise
    except pd.errors.ParserError:
        logger.exception("Ошибка парсинга Excel-файла: %s", excel_file_path)
        raise
    except Exception:
        logger.exception("Ошибка при чтении Excel-файла.")
        raise


def data_from_time_range(
    dataframe: pd.DataFrame, time_range: tuple, column: str = "Дата операции", date_fmt: str = "%d.%m.%Y %H:%M:%S"
) -> pd.DataFrame:
    """Фильтрует строки DataFrame по столбцу 'Дата операции',
    возвращая только те, где дата лежит в диапазоне (start, end)."""

    try:
        df = dataframe.copy()
        df[column] = pd.to_datetime(df[column], format=date_fmt, errors="coerce")

        start, end = pd.to_datetime(time_range[0]), pd.to_datetime(time_range[1])

        mask = (df[column] >= start) & (df[column] <= end)
        filtered_df: pd.DataFrame = df.loc[mask]
        logger.info("DataFrame успешно отфильтрован.")

        return filtered_df

    except Exception:
        logger.exception("Ошибка фильтрации по дате.")
        raise


def check_column(df: pd.DataFrame, expected_column: str = "Сумма платежа") -> None:
    """Проверяет DataFrame на наличие столбца. Название столбца функция принимает, как аргумент,
    по умолчанию expected_column = 'Сумма платежа'"""

    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"DataFrame должен быть pd.DataFrame, а получен {type(df).__name__}")
    if not isinstance(expected_column, str):
        raise TypeError(f"Название колонки должно быть str, а получено {type(expected_column).__name__}")
    if expected_column not in df.columns:
        raise KeyError(f"Колонка '{expected_column}' не найдена")


def filter_negative_transactions(df: pd.DataFrame, col_amount: str = "Сумма платежа") -> pd.DataFrame:
    """Оставляет в DataFrame только те строки, где значение в колонке col < 0."""

    try:
        df2 = df.copy()
        mask = df2[col_amount] < 0
        logger.info(
            "filter_negative_transactions: из %d строк выбрано %d расходов по '%s'", len(df2), mask.sum(), col_amount
        )

        return df2.loc[mask]

    except KeyError:
        logger.exception("Ошибка: отсутствует необходимый ключ в данных.")
        raise
    except TypeError:
        logger.exception("Ошибка типа данных при фильтрации.")
        raise
    except Exception:
        logger.exception("Неожиданная ошибка при фильтрации.")
        raise


def cards_info(dataframe: pd.DataFrame) -> list:
    """Группирует транзакции по номеру карты, считает суммарные траты (по модулю) и
    вычисляет кэшбэк (1₽ за каждые 100₽).
    Возвращает список словарей в виде: [{"Номер карты": ..., "Сумма потрачено": ..., "Кешбэк": ...}]"""

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError(f"Ожидался pd.DataFrame, а получен {type(dataframe).__name__}")

    try:
        card_grouped = dataframe.groupby("Номер карты")["Сумма платежа"].sum()
        logger.info("Транзакции успешно сгруппированы по номеру карты.")

        card_grouped_abs = card_grouped.abs().round(2)
        clean_cards = card_grouped_abs.index.astype(str)
        clean_cards = clean_cards.str.lstrip("*")

        result_df = pd.DataFrame(
            {
                "last_digits": clean_cards,
                "total_spent": card_grouped_abs.values,
                "cashback": (card_grouped_abs // 100).values,
            }
        )

        return result_df.to_dict(orient="records")

    except Exception:
        logger.exception("Ошибка обработки транзакции.")
        raise


def top_transactions(
    df: pd.DataFrame, number_best_transactions: int, reverse: bool = True, expected_column: str = "Сумма платежа"
) -> list:
    """Выбирает топ транзакций из Excel-файла, сортируя по значению ключа 'Сумма платежа'"""

    try:
        sorted_df = df.sort_values(by=expected_column, ascending=reverse)
        top_transactions_list = sorted_df.head(number_best_transactions).to_dict("records")
        logger.info("Топ %s транзакций определен.", number_best_transactions)

        return top_transactions_list

    except Exception:
        logger.exception("Ошибка получения топ транзакций.")
        raise


def read_json_file(json_file_path: Path) -> dict[str, Any]:
    """Читает Json-файл по указанному пути и возвращает словарь с данными."""

    try:
        with open(json_file_path) as f:
            data: dict[Any, Any] = json.load(f)
            logger.info("Json-файл: %s, успешно прочитан.", json_file_path)
            return data
    except Exception:
        logger.exception("Ошибка при чтении Json-файла.")
        raise


def exchange_rates(list_currencies: list) -> dict:
    """
    :param list_currencies: Список валют.
    :return: Словарь, где ключ — код валюты, значение — курс в рублях.

    Получает курсы валют по отношению к российскому рублю.

    Функция запрашивает у API CurrencyFreaks актуальные курсы валют
    относительно доллара США, затем пересчитывает их в рубли.
    Автоматически добавляет в список валют RUB, если его там нет.
    """

    if "RUB" not in list_currencies:
        list_currencies.append("RUB")

    str_currencies = ",".join(list_currencies)

    url = "https://api.currencyfreaks.com/v2.0/rates/latest"

    params = {
        "apikey": API_KEY_1,
        "symbols": str_currencies,
    }

    try:
        # Ниже отправляю GET-запрос к API с заданными заголовками и параметрами
        response = requests.get(url, params=params)
        # Ниже проверяю статус ответа. Если статус-код указывает на ошибку, raise_for_status() выбросит исключение.
        response.raise_for_status()

    except requests.exceptions.RequestException:
        logger.exception("Ошибка при обращении к API конвертации.")
        return {}

    try:
        result = response.json()
        rates_key = result.get("rates", {})
        usd_to_rub = float(rates_key["RUB"])
    except (json.JSONDecodeError, KeyError, ValueError):
        logger.exception("Ошибка обработки данных от API.")
        return {}

    rub_retes = {}

    for currency, rate in rates_key.items():
        try:
            if currency == "RUB":
                rub_retes[currency] = 1.0
            else:
                rub_retes[currency] = round(1 / float(rate) * usd_to_rub, 2)
        except (ValueError, ZeroDivisionError):
            logger.warning("Ошибка расчёта курса для %r: %r", currency, rate)
            continue

    logger.info("Словарь, где ключ — код валюты, значение — курс в рублях, успешно сформирован.")
    return rub_retes


def stock_prices(list_stocks: list, dol_price: float) -> list:
    """
    :param list_stocks: Список с акциями.
    :param dol_price: Курс 1 доллар в рублях.

    :return: Список словарей. Пример: {"stock": "AAPL", "price": 15778.5}

    Получает цены на акции, которые указаны в списке.
    Функция запрашивает у API AlphaVantage актуальные цены на акции в долларах США.
    Далее цена в долларах США пересчитывается в рубли.
    """

    url = "https://www.alphavantage.co/query"
    results = []

    for stock in list_stocks:
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": stock,
            "apikey": API_KEY_2,
        }

        try:
            # Ниже отправляю GET-запрос к API с заданными заголовками и параметрами
            response = requests.get(url, params=params)
            # Ниже проверяю статус ответа. Если статус-код указывает на ошибку, raise_for_status() выбросит исключение.
            response.raise_for_status()
            logger.info("Запрос к API успешен для %r", stock)
        except requests.exceptions.RequestException:
            logger.exception("Ошибка при выполнении запроса к %r.", stock)
            continue

        try:
            data = response.json()
            logger.debug("Получен ответ JSON для %r: %s", stock, data)
        except json.JSONDecodeError:
            logger.exception("Невалидный JSON в ответе API для %r", stock)
            continue

        global_quote = data.get("Global Quote", {})
        price_str = global_quote.get("05. price")
        if price_str:
            try:
                price = float(price_str) * dol_price
            except ValueError:
                logger.exception("Ошибка преобразования цены для %r: %r.", stock, price_str)
                continue
            results.append({"stock": stock, "price": price})
        else:
            logger.warning("Данные для %r не получены корректно: %s", stock, data)

    logger.info("Итоговый список словарей с ценами по акциям успешно сформирован.")
    return results


def dollar_to_ruble_price(dict_exchange_rate: dict, currency_str: str = "USD") -> float:
    """Функция получает словарь с курсами валют и возвращает значение по ключу 'USD'"""

    if not isinstance(exchange_rates, dict):
        raise TypeError(f"exchange_rates должен быть dict, а получен {type(exchange_rates).__name__}")
    if not isinstance(currency_str, str):
        raise TypeError(f"currency должен быть str, а получен {type(currency_str).__name__}")

    if currency_str not in dict_exchange_rate:
        raise ValueError(f"Нет курса для валюты: {currency_str}")
    result = float(dict_exchange_rate[currency_str])
    logger.info("Стоимость %s успешно определена.", currency_str)
    return result
