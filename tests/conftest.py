from typing import Any, Dict, List

import pandas as pd
import pytest


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Базовый DataFrame"""

    return pd.DataFrame({"Сумма платежа": [-100, 0, 200, -50], "Описание": ["a", "b", "c", "d"]})


@pytest.fixture
def cards_df() -> pd.DataFrame:
    """Фикстура с транзакциями по карте."""

    return pd.DataFrame(
        {"Номер карты": ["*1234", "*1234", "*5678", "*5678", "*5678"], "Сумма платежа": [-100, -200, -50, -50, -50]}
    )


@pytest.fixture
def cards_df_2() -> pd.DataFrame:
    """Фикстура с транзакциями по карте."""

    return pd.DataFrame(
        [
            {"Сумма платежа": 100, "Имя": "Алиса"},
            {"Сумма платежа": 300, "Имя": "Боб"},
            {"Сумма платежа": 200, "Имя": "Чарли"},
        ]
    )


@pytest.fixture
def valid_json_content() -> str:
    """Фикстура возвращает строку с валидным JSON-содержимым."""

    return '{"key": "value", "number": 42}'


@pytest.fixture
def parsed_json_data() -> Dict[str, Any]:
    """Возвращает словарь, соответствующий валидному JSON."""

    return {"key": "value", "number": 42}


@pytest.fixture
def mock_api_response() -> Dict[str, Dict[str, str]]:
    """Имитация JSON-ответа от API CurrencyFreaks."""

    return {"rates": {"USD": "1.0", "EUR": "0.85", "JPY": "110.0", "RUB": "90.0"}}


@pytest.fixture
def currency_list() -> List[str]:
    """Возвращает список валют для теста."""

    return ["USD", "EUR"]


@pytest.fixture
def stock_list() -> List[str]:
    """Фикстура: список акций"""

    return ["AAPL", "MSFT"]


@pytest.fixture
def mock_stock_response() -> Dict[str, Dict[str, str]]:
    """Фикстура: успешный ответ от API"""

    return {"Global Quote": {"01. symbol": "AAPL", "05. price": "175.32"}}


@pytest.fixture
def exchange_rates() -> dict:
    """Возвращает фиктивные курсы валют."""

    return {"USD": "90.5", "EUR": "98.2", "JPY": "0.62"}


@pytest.fixture
def valid_dates() -> dict[str, str]:
    """Возвращает словарь с корректными строками дат и ожидаемыми результатами."""
    return {
        "01.01.2023": "2023-01-01",
        "15.08.2022": "2022-08-15",
        "31.12.2020": "2020-12-31"
    }


@pytest.fixture
def sample_transactions() -> pd.DataFrame:
    """Фикстура: возвращает тестовый DataFrame с транзакциями, содержащими разные категории."""

    return pd.DataFrame({
        "Категория": ["еда", "транспорт", "Еда", "  еда  ", None, "развлечения"],
        "Сумма": [100, 50, 75, 120, 200, 300]
    })


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """
    Возвращает DataFrame с транзакциями, содержащими даты в разных месяцах и годах.
    """
    return pd.DataFrame({
        "Дата операции": [
            "01.01.2023 12:00:00",
            "15.01.2023 08:30:00",
            "20.02.2023 14:45:00",
            "05.01.2022 10:00:00",
            "10.03.2023 09:15:00",
            "invalid_date"
        ],
        "Сумма": [100, 200, 150, 300, 250, 999]
    })


@pytest.fixture
def cashback_dataframe() -> pd.DataFrame:
    """
    Возвращает DataFrame с транзакциями и кэшбэком по категориям.
    """
    return pd.DataFrame({
        "Категория": ["еда", "транспорт", "еда", "развлечения", "транспорт"],
        "Кэшбэк": [10.0, 5.0, 7.5, 12.0, 3.0]
    })
