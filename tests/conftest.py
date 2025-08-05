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
