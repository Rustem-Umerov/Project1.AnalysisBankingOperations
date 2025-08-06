import pytest
import json
from unittest.mock import patch, Mock
from src.views import output_final_result


@patch("src.views.greetings", return_value="Доброе утро")
@patch("src.views.date_range", return_value=("2024-01-01", "2024-01-31"))
@patch("src.views.read_excel_file")
@patch("src.views.data_from_time_range")
@patch("src.views.check_column")
@patch("src.views.filter_negative_transactions")
@patch("src.views.cards_info", return_value={"Visa": 2, "MasterCard": 1})
@patch("src.views.top_transactions", return_value=[
    {
        "Дата платежа": "2024-01-10",
        "Сумма платежа": -150.0,
        "Категория": "еда",
        "Описание": "кафе"
    }
])
@patch("src.views.read_json_file", return_value={
    "user_currencies": ["USD", "EUR"],
    "user_stocks": ["AAPL", "TSLA"]
})
@patch("src.views.exchange_rates", return_value={"USD": 90.5, "EUR": 98.2})
@patch("src.views.dollar_to_ruble_price", return_value=90.5)
@patch("src.views.stock_prices", return_value={"AAPL": 18000, "TSLA": 22000})
def test_output_final_result_success(
    mock_greet: Mock,
    mock_range: Mock,
    mock_read: Mock,
    mock_filter: Mock,
    mock_check: Mock,
    mock_negative: Mock,
    mock_cards: Mock,
    mock_top: Mock,
    mock_json: Mock,
    mock_rates: Mock,
    mock_dollar: Mock,
    mock_stocks: Mock
) -> None:
    """
    Проверяет успешное выполнение функции output_final_result и корректность структуры JSON.
    """

    result = output_final_result("2024-01-15 08:00:00")
    parsed = json.loads(result)

    assert parsed["greeting"] == "Доброе утро"
    assert "cards" in parsed
    assert "top_transactions" in parsed
    assert "currency_rates" in parsed
    assert "stock_prices" in parsed
    assert parsed["currency_rates"][0]["currency"] == "USD"
    assert parsed["currency_rates"][0]["rate"] == 90.5


@patch("src.views.greetings", side_effect=RuntimeError("Ошибка приветствия"))
@patch("src.views.logger")
def test_output_final_result_exception(
    mock_logger: Mock,
    mock_greet: Mock
) -> None:
    """
    Проверяет, что при исключении внутри функции возвращается JSON с ключом 'error' и логируется ошибка.
    """
    result = output_final_result("2024-01-15 08:00:00")
    parsed = json.loads(result)

    assert "error" in parsed
    assert "Ошибка приветствия" in parsed["error"]
    mock_logger.error.assert_called_once()
