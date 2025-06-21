from datetime import datetime, time
from pathlib import Path
import json
import pandas as pd
import requests
from dotenv import load_dotenv
import os
from typing import Any


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

    try:
        date_obj = datetime.strptime(input_date, "%d.%m.%Y %H:%M:%S")
    except ValueError:
        raise ValueError(f"Неверный формат даты: {input_date}. Ожидается '%d.%m.%Y %H:%M:%S'")

    start_date = datetime(date_obj.year, date_obj.month, 1)

    return start_date, date_obj


def greetings(str_date_time: str) -> str:
    """Возвращает приветствие в зависимости от полученного времени.

    Интервалы определяются следующим образом:
      - Доброе утро: с 05:00 до 12:00 (включительно 05:00, исключая 12:00)
      - Добрый день: с 12:00 до 18:00
      - Добрый вечер: с 18:00 до 23:00
      - Доброй ночи: с 23:00 до 05:00 (включая ночной интервал через полночь)"""

    str_time = str_date_time.split()[1]
    time_dt = datetime.strptime(str_time, "%H:%M:%S").time()

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


def read_excel_file(excel_file_path: Path) -> pd.DataFrame:
    """Читает Excel-файл по указанному пути и возвращает DataFrame."""

    try:
        return pd.read_excel(excel_file_path)
    except Exception as e:
        print(f"Ошибка при чтении Excel-файла: {e}")
        raise


def data_from_time_range(dataframe: pd.DataFrame, time_range: tuple) -> pd.DataFrame:
    """Фильтрует строки DataFrame по столбцу 'Дата операции',
    возвращая только те, где дата лежит в диапазоне (start, end)."""

    expected_column = "Дата операции"

    df = dataframe.copy()
    df[expected_column] = pd.to_datetime(df[expected_column], format="%d.%m.%Y %H:%M:%S")

    start, end = pd.to_datetime(time_range[0]), pd.to_datetime(time_range[1])

    mask = (df[expected_column] >= start) & (df[expected_column] <= end)
    filtered_df: pd.DataFrame = df.loc[mask]

    return filtered_df


def check_column(df: pd.DataFrame, expected_column: str = "Сумма платежа") -> None:
    """Проверяет DataFrame на наличие столбца. Название столбца функция принимает, как аргумент,
    по умолчанию expected_column = 'Сумма платежа'"""

    if expected_column not in df.columns:
        raise KeyError(f"Колонка '{expected_column}' не найдена")


def filter_negative_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Оставляет в DataFrame только те строки, где значение в колонке col < 0."""

    expected_column = "Сумма платежа"
    return df[df[expected_column] < 0]


def cards_info(dataframe: pd.DataFrame) -> list:
    """Группирует транзакции по номеру карты, считает суммарные траты (по модулю) и
    вычисляет кэшбэк (1₽ за каждые 100₽).
    Возвращает список словарей в виде: [{"Номер карты": ..., "Сумма потрачено": ..., "Кешбэк": ...}]"""

    card_grouped = dataframe.groupby("Номер карты")["Сумма платежа"].sum()

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


def top_transactions(
    df: pd.DataFrame, number_best_transactions: int, reverse: bool = True, expected_column: str = "Сумма платежа"
) -> list:
    """Выбирает топ транзакций из Excel-файла, сортируя по значению ключа 'Сумма платежа'"""

    sorted_df = df.sort_values(by=expected_column, ascending=reverse)
    top_transactions_list = sorted_df.head(number_best_transactions).to_dict("records")

    return top_transactions_list


def read_json_file(json_file_path: Path) -> dict[str, Any]:
    """Читает Json-файл по указанному пути и возвращает словарь с данными."""

    try:
        with open(json_file_path) as f:
            data: dict[Any, Any] = json.load(f)
            return data
    except Exception as e:
        print(f"Ошибка при чтении Json-файла: {e}")
        raise


def exchange_rates(list_currencies: list) -> dict:
    """ """

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

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при обращении к API конвертации: {e}")
        return {}

    # Преобразую ответ API из JSON в словарь.
    result = response.json()
    rates_key = result.get("rates", {})

    usd_to_rub = float(rates_key["RUB"])

    rub_retes = {}

    for currency, rate in rates_key.items():
        if currency == "RUB":
            rub_retes[currency] = 1.0
        else:
            rub_retes[currency] = round(1 / float(rate) * usd_to_rub, 2)

    return rub_retes


def stock_prices(list_stocks: list) -> list:
    """ """

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

            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при обращении к API для {stock}: {e}")
            continue
        except json.JSONDecodeError:
            raise

        global_quote = data.get("Global Quote", {})
        price_str = global_quote.get("05. price")
        if price_str:
            try:
                price = float(price_str)
            except ValueError:
                print(f"Ошибка преобразования цены для {stock}: {price_str}")
                continue
            results.append({"stock": stock, "price": price})
        else:
            print(f"Данные для {stock} не получены корректно: {data}")

    return results


def output_final_result(date: str) -> str:
    """ """

    greeting = greetings(date)  # функция приветствия

    range_date = date_range(date)  # функция определяющая временной диапазон
    df = read_excel_file(EXCEL_PATH)  # функция читающая excel-файл
    filter_by_time_range = data_from_time_range(df, range_date)  # фильтрация по дате
    check_column(filter_by_time_range)  # проверка на наличие столбца "Сумма платежа"
    # Ниже оставляет в DataFrame только те строки, где значение в колонке "Сумма платежа" < 0
    negative_transactions = filter_negative_transactions(filter_by_time_range)
    cards_information = cards_info(negative_transactions)  # информация о картах

    # Ниже выводит топ 5 транзакции
    top_five_transactions = top_transactions(negative_transactions, 5)
    result_top_five_transactions = [
        {
            "date": transaction["Дата платежа"],
            "amount": abs(transaction["Сумма платежа"]),
            "category": transaction["Категория"],
            "description": transaction["Описание"],
        }
        for transaction in top_five_transactions
    ]

    json_file = read_json_file(JSON_PATH)  # читает json-файл

    list_currencies = json_file["user_currencies"]  # выводит список валют
    currency_rates = exchange_rates(list_currencies)  # определят курс валют

    # иже создаю итоговые словари с валютами
    result_currency_rates = [
        {"currency": "USD", "rate": currency_rates.get("USD", "ошибка")},
        {"currency": "EUR", "rate": currency_rates.get("EUR", "ошибка")},
    ]

    list_stocks = json_file["user_stocks"]  # выводи список акции
    stocks_prices = stock_prices(list_stocks)  # определяет стоимость акции

    # ниже вывожу итоговый результат
    final_result = {
        "greeting": greeting,
        "cards": cards_information,
        "top_transactions": result_top_five_transactions,
        "currency_rates": result_currency_rates,
        "stock_prices": stocks_prices,
    }

    return json.dumps(final_result, indent=4, ensure_ascii=False)


print(output_final_result("20.05.2020 19:22:11"))
