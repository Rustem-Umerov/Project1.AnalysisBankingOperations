import json
import os
from pathlib import Path

from dotenv import load_dotenv

from src.logging import get_logger
from src.utils import (cards_info, check_column, data_from_time_range, date_range, dollar_to_ruble_price,
                       exchange_rates, filter_negative_transactions, greetings, read_excel_file, read_json_file,
                       stock_prices, top_transactions)

logger = get_logger(__name__)

SRC_DIR = Path(__file__).resolve().parent
EXCEL_PATH = SRC_DIR.parent / "data" / "operations.xlsx"
JSON_PATH = SRC_DIR.parent / "user_settings.json"

load_dotenv()
API_KEY_1 = os.getenv("API_KEY_1")
API_KEY_2 = os.getenv("API_KEY_2")


def output_final_result(date: str) -> str:
    """
    :param date: Дата и время в формате YYYY-MM-DD HH:MM:SS
    :return: JSON-ответ.

    Данная функция - это главная функция, которая объединяет второстепенные функции.
    Функция получает дату и время в формате YYYY-MM-DD HH:MM:SS.

    Далее функция greetings в зависимости от времени выводит приветствие.
    Далее функция date_range функция определяет временной диапазон.
    Далее функция read_excel_file читает excel-файл.
    Далее функция data_from_time_range фильтрует по временному диапазону полученному из функции date_range.
    Далее функция check_column проверяет DataFrame на наличие столбца "Сумма платежа".
    Далее функция filter_negative_transactions фильтрует транзакции и оставляет в DataFrame только те строки,
    где значение в колонке "Сумма платежа" < 0.
    Далее функция cards_info выводит информацию о картах.
    Далее функция top_transactions выводит топ транзакции, в данном случае топ 5.
    Далее функция read_json_file читает json-файл.
    Далее функция exchange_rates определят курс валют.
    Далее функция dollar_to_ruble_price выводит цену за 1 доллар в рублях.
    Далее функция stock_prices определяет стоимость акции.
    """

    try:
        greeting = greetings(date)  # функция приветствия
        logger.info("Функция greetings успешно отработала.")

        range_date = date_range(date)  # функция определяющая временной диапазон
        logger.info("Функция date_range успешно отработала.")

        df = read_excel_file(EXCEL_PATH)  # функция читающая excel-файл
        logger.info("Функция read_excel_file успешно отработала.")

        filter_by_time_range = data_from_time_range(df, range_date)  # фильтрация по дате
        logger.info("Функция data_from_time_range успешно отработала.")

        check_column(filter_by_time_range)  # проверка на наличие столбца "Сумма платежа"
        logger.info("Функция check_column успешно отработала.")

        # Ниже оставляет в DataFrame только те строки, где значение в колонке "Сумма платежа" < 0
        negative_transactions = filter_negative_transactions(filter_by_time_range)
        logger.info("Функция filter_negative_transactions успешно отработала.")

        cards_information = cards_info(negative_transactions)  # информация о картах
        logger.info("Функция cards_info успешно отработала.")

        # Ниже выводит топ 5 транзакции
        top_five_transactions = top_transactions(negative_transactions, 5)
        logger.info("Функция top_transactions успешно отработала.")
        result_top_five_transactions = [
            {
                "date": transaction["Дата платежа"],
                "amount": abs(transaction["Сумма платежа"]),
                "category": transaction["Категория"],
                "description": transaction["Описание"],
            }
            for transaction in top_five_transactions
        ]
        logger.info("Список - топ 5 транзакции, сформирован.")

        json_file = read_json_file(JSON_PATH)  # читает json-файл
        logger.info("Функция read_json_file успешно отработала.")

        list_currencies = json_file["user_currencies"]  # выводит список валют
        logger.info("Список валют сформирован.")

        currency_rates = exchange_rates(list_currencies)  # определят курс валют
        logger.info("Функция exchange_rates успешно отработала.")

        dol_price = dollar_to_ruble_price(currency_rates)  # выводит цену за 1 доллар в рублях
        logger.info("Функция dollar_to_ruble_price успешно отработала.")

        # Ниже создаю итоговые словари с валютами
        result_currency_rates = [
            {"currency": "USD", "rate": currency_rates.get("USD", "ошибка")},
            {"currency": "EUR", "rate": currency_rates.get("EUR", "ошибка")},
        ]
        logger.info("Список итоговых словарей со стоимостью USD и EUR успешно сформирован.")

        list_stocks = json_file["user_stocks"]  # выводи список акции
        stocks_prices = stock_prices(list_stocks, dol_price)  # определяет стоимость акции
        logger.info("Функция stock_prices успешно отработала.")

        # ниже вывожу итоговый результат
        final_result = {
            "greeting": greeting,
            "cards": cards_information,
            "top_transactions": result_top_five_transactions,
            "currency_rates": result_currency_rates,
            "stock_prices": stocks_prices,
        }

        return json.dumps(final_result, indent=4, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)
