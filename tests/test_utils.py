from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, mock_open, patch

import pandas as pd
import pytest
from pytest import LogCaptureFixture
from requests.exceptions import RequestException

from src.utils import (cards_info, check_column, data_from_time_range, date_range, dollar_to_ruble_price,
                       exchange_rates, filter_negative_transactions, greetings, read_excel_file, read_json_file,
                       stock_prices, top_transactions)


@pytest.mark.parametrize(
    "input_valid_date, expected_start, expected_end",
    [
        (
            "01.01.2025 00:00:00",
            datetime(2025, 1, 1, 0, 0, 0),
            datetime(2025, 1, 1, 0, 0, 0),
        ),
        (
            "15.02.2023 13:45:30",
            datetime(2023, 2, 1, 0, 0, 0),
            datetime(2023, 2, 15, 13, 45, 30),
        ),
        (
            "28.02.2024 23:59:59",  # високосный год
            datetime(2024, 2, 1, 0, 0, 0),
            datetime(2024, 2, 28, 23, 59, 59),
        ),
    ],
)
def test_date_range_valid_dates(input_valid_date: str, expected_start: datetime, expected_end: datetime) -> None:
    """Тест проверяет, что функция правильно отработает, если на вход поступят валидные данные."""

    start, end = date_range(input_valid_date)
    assert start == expected_start
    assert end == expected_end


@pytest.mark.parametrize(
    "invalid_date",
    [
        "2021-01-01 00:00:00",
        "01.01.21 00:00:00",
        "01.13.2021 00:00:00",
        "foo",
    ],
)
def test_date_range_invalid_date(invalid_date: str) -> None:
    """Тест проверяет, что функция выбросит ошибку ValueError, если формат даты будет не правильный."""

    with pytest.raises(ValueError) as exc:
        date_range(invalid_date)

    assert "Неверный формат даты:", "Ожидается '%d.%m.%Y %H:%M:%S'" in str(exc.value)


@pytest.mark.parametrize(
    "not_str",
    [
        11111,
        ["01.01.21 00:00:00"],
        ["01.13.2021 00:00:00"],
        ["abc", 123],
    ],
)
def test_date_range_invalid_type_date(not_str: Any) -> None:
    """Тест проверяет, что будет ошибка, если на вход, функция получит не верный тип данных."""

    with pytest.raises(TypeError) as exc:
        date_range(not_str)

    assert "Дата должна быть строкой(str), а получен" in str(exc.value)


def test_date_range_logging(caplog: LogCaptureFixture) -> None:
    """Тест проверяет логи."""

    sample_input = "01.01.2025 00:00:00"
    date_range(sample_input)

    assert "Полученная от пользователя дата:", "преобразована в datetime." in caplog.text
    assert "Дата начала:", "и дата конца:" in caplog.text


@pytest.mark.parametrize(
    "input_date, result",
    [
        ("01.01.2025 06:00:00", "Доброе утро"),
        ("01.01.2025 10:00:00", "Доброе утро"),
        ("01.01.2025 12:00:00", "Добрый день"),
        ("01.01.2025 16:00:00", "Добрый день"),
        ("01.01.2025 18:00:00", "Добрый вечер"),
        ("01.01.2025 20:00:00", "Добрый вечер"),
        ("01.01.2025 23:00:00", "Доброй ночи"),
        ("01.01.2025 00:00:00", "Доброй ночи"),
        ("01.01.2025 04:00:00", "Доброй ночи"),
    ],
)
def test_greetings_valid_date(input_date: str, result: str, caplog: LogCaptureFixture) -> None:
    """Тест проверяет, что функция greetings правильно работает, если входные данные валидны."""

    assert greetings(input_date) == result

    assert "Время полученное от пользователя:", ", успешно преобразовано в datetime." in caplog.text


@pytest.mark.parametrize(
    "not_str, result",
    [
        (["01.01.2025 12:00:00"], "Добрый день"),
        (1234, "Добрый день"),
        ([123, "abc"], "Добрый день"),
    ],
)
def test_greetings_not_str(not_str: Any, result: str, caplog: LogCaptureFixture) -> None:
    """Тест проверят, что, в случае, неверного типа входных данных, функция вернет значение по умолчанию.
    Также есть проверка лога."""

    assert greetings(not_str) == result

    assert "Ожидали строку, получили" in caplog.text


@pytest.mark.parametrize(
    "invalid_date, result",
    [
        ("01.01.2025", "Добрый день"),
        ("16:00:00", "Добрый день"),
        ("01.01.2025_16:00:00", "Добрый день"),
    ],
)
def test_greetings_invalid_format(invalid_date: str, result: str, caplog: LogCaptureFixture) -> None:
    """Тест проверят, что функция правильно работает, если получит не профильный формат даты и времени."""

    assert greetings(invalid_date) == result

    assert "Неверный формат входа:" in caplog.text


@pytest.mark.parametrize(
    "invalid_date, result",
    [
        ("01.01.2022 99:99:99", "Добрый день"),
        ("02.02.2022 24:00:00", "Добрый день"),
    ],
)
def test_greetings_invalid_date(invalid_date: str, result: str, caplog: LogCaptureFixture) -> None:
    """Тест проверяет, что функция правильно отработает, если на вход поступит не правильная дата."""

    assert greetings(invalid_date) == result

    assert "Ошибка обработки времени:" in caplog.text
    assert invalid_date in caplog.text


def test_read_excel_file_success() -> None:
    """Тест проверяет, что функция правильно работает."""

    expected_df = pd.DataFrame({"a": [1, 2, 3]})
    fake_path = Path("fake.xlsx")

    with patch("src.utils.pd.read_excel", return_value=expected_df) as mock_read:
        result = read_excel_file(fake_path)

    mock_read.assert_called_once_with(fake_path)
    assert result is expected_df


@pytest.mark.parametrize(
    "error, expected_log_msg",
    [
        (FileNotFoundError, "Файл не найден:"),
        (pd.errors.ParserError, "Ошибка парсинга Excel-файла:"),
        (RuntimeError, "Ошибка при чтении Excel-файла."),
    ],
)
def test_read_excel_file_errors(error: type[Exception], expected_log_msg: str, caplog: LogCaptureFixture) -> None:
    """Тест проверяет, что возникнут ошибки, если данные не валидны."""

    fake_path = Path("fake.xlsx")
    caplog.set_level("ERROR")

    with patch("src.utils.pd.read_excel", side_effect=error("файл повреждён")):
        with pytest.raises(error) as exc_info:
            read_excel_file(fake_path)

    assert "файл повреждён" in str(exc_info.value)
    assert expected_log_msg in caplog.text
    assert "файл повреждён" in caplog.text


@pytest.mark.parametrize(
    "dates, time_range, expected_dates, expected_vals",
    [
        (
            ["01.01.2023 00:00:00", "15.01.2023 12:00:00", "31.01.2023 23:59:59"],
            ("01.01.2023 00:00:00", "31.01.2023 23:59:59"),
            ["01.01.2023 00:00:00", "15.01.2023 12:00:00", "31.01.2023 23:59:59"],
            [10, 20, 30],
        ),
        (
            ["31.12.2022 23:59:59", "01.01.2023 00:00:00", "02.01.2023 01:00:00"],
            ("01.01.2023 00:00:00", "02.01.2023 00:00:00"),
            ["01.01.2023 00:00:00"],
            [20],
        ),
    ],
)
def data_from_time_range_success(
    dates: list[str],
    time_range: tuple[str, str],
    expected_dates: list[str],
    expected_vals: list[int],
    caplog: LogCaptureFixture,
) -> None:
    """Тест проверяет успешную фильтрацию."""

    df = pd.DataFrame({"Дата операции": dates, "val": expected_vals[:]})
    result = data_from_time_range(df, time_range)

    res_dates = result["Дата операции"].dt.strftime("%d.%m.%Y %H:%M:%S").tolist()
    assert res_dates == expected_dates
    assert result["val"].tolist() == expected_vals
    assert "DataFrame успешно отфильтрован." in caplog.text


def test_data_from_time_range_error(caplog: LogCaptureFixture) -> None:
    """Тест проверяет появления ошибки."""

    caplog.set_level("ERROR")

    df = pd.DataFrame({"Дата операции": ["01.01.2023 10:00:00"]})
    time_range = ("2023-01-01", "2023-02-01")

    with patch("src.utils.pd.to_datetime", side_effect=Exception("error")):
        with pytest.raises(Exception) as exc_info:
            data_from_time_range(df, time_range)

    assert "error" in str(exc_info.value)

    assert "Ошибка фильтрации по дате." in caplog.text


def test_check_column_success() -> None:
    """Тест проверяет, что функция check_column успешно отработает с правильными данными."""

    df = pd.DataFrame({"Сумма платежа": [100, 200]})
    check_column(df)


def test_check_column_custom_column_success() -> None:
    """Тест проверяет, что функция check_column успешно отработает, если изменить значение expected_column."""

    df = pd.DataFrame({"Итого": [100, 200]})
    check_column(df, expected_column="Итого")


def test_check_column_missing_column() -> None:
    """Тест проверяет, что будет ошибка KeyError, если в DataFrame нет нужной колонки."""

    df = pd.DataFrame({"Другое": [100, 200]})
    with pytest.raises(KeyError, match="Колонка 'Сумма платежа' не найдена"):
        check_column(df)


def test_check_column_wrong_df_type() -> None:
    """Тест проверяет, что будет ошибка TypeError, если передать не DataFrame."""

    not_a_df = {"Сумма платежа": [100, 200]}
    with pytest.raises(TypeError, match="DataFrame должен быть pd.DataFrame"):
        check_column(not_a_df)  # type: ignore[arg-type]


def test_check_column_wrong_column_type() -> None:
    """Тест проверяет, что будет ошибка TypeError, если передать название ошибки не строкой."""

    df = pd.DataFrame({"Сумма платежа": [100, 200]})
    with pytest.raises(TypeError, match="Название колонки должно быть str"):
        check_column(df, expected_column=123)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "col_name, expected_count",
    [
        ("Сумма платежа", 2),
    ],
)
def test_filter_negative_transactions_valid(sample_df: pd.DataFrame, col_name: str, expected_count: int) -> None:
    """Тест проверяет правильную фильтрацию."""

    result = filter_negative_transactions(sample_df, col_amount=col_name)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == expected_count
    assert all(result[col_name] < 0)


def test_filter_negative_transactions_missing_column(sample_df: pd.DataFrame) -> None:
    """Тест проверяет ошибку KeyError, в случае отсутствия колонки."""

    with patch("src.utils.logger") as mock_logger:
        with pytest.raises(KeyError):
            filter_negative_transactions(sample_df, col_amount="Нет такой")
        mock_logger.exception.assert_called_once_with("Ошибка: отсутствует необходимый ключ в данных.")


def test_filter_negative_transactions_wrong_column_type(sample_df: pd.DataFrame) -> None:
    """Тест проверяет ошибку TypeError, в случае неправильного типа данных."""

    sample_df["Сумма платежа"] = "не числа"
    with patch("src.utils.logger") as mock_logger:
        with pytest.raises(TypeError):
            filter_negative_transactions(sample_df)
        mock_logger.exception.assert_called_once_with("Ошибка типа данных при фильтрации.")


@pytest.mark.parametrize("bad_input", [123, "строка", None])
def test_filter_negative_transactions_invalid_input(bad_input: list) -> None:
    """Тест проверяет ошибку Exception, если на вход поступил не DataFrame."""

    with patch("src.utils.logger") as mock_logger:
        with pytest.raises(Exception):
            filter_negative_transactions(bad_input)  # type: ignore[arg-type]
        mock_logger.exception.assert_called_once_with("Неожиданная ошибка при фильтрации.")


def test_cards_info_valid(cards_df: pd.DataFrame) -> None:
    """Тест проверяет корректную работу функции cards_info."""

    result = cards_info(cards_df)
    assert isinstance(result, list)
    assert len(result) == 2

    for item in result:
        assert "last_digits" in item
        assert "total_spent" in item
        assert "cashback" in item
        assert isinstance(item["last_digits"], str)
        assert isinstance(item["total_spent"], (float, int))
        assert isinstance(item["cashback"], (float, int))

    # Проверка конкретных значений
    card_1234 = next(filter(lambda x: x["last_digits"] == "1234", result))
    assert card_1234["total_spent"] == 300.0
    assert card_1234["cashback"] == 3.0


@pytest.mark.parametrize("bad_input", [123, "строка", None, [1, 2, 3]])
def test_cards_info_invalid_input_type(bad_input: list) -> None:
    """Тест проверяет ошибку TypeError, если на вход поступил не DataFrame."""

    with pytest.raises(TypeError, match="Ожидался pd.DataFrame"):
        cards_info(bad_input)  # type: ignore[arg-type]


def test_cards_info_logging(cards_df: pd.DataFrame) -> None:
    """Тест проверяет логирование успешной работы функции cards_info."""

    with patch("src.utils.logger") as mock_logger:
        cards_info(cards_df)
        mock_logger.info.assert_called_once_with("Транзакции успешно сгруппированы по номеру карты.")


def test_cards_info_missing_column() -> None:
    """Тест проверяет появление ошибки, если отсутвтвует нужная колонка."""

    df = pd.DataFrame({"Другое": [1, 2, 3]})
    with patch("src.utils.logger") as mock_logger:
        with pytest.raises(Exception):
            cards_info(df)
        mock_logger.exception.assert_called_once_with("Ошибка обработки транзакции.")


@patch("src.utils.logger")
def test_top_transactions_returns_sorted(mock_logger: MagicMock, cards_df_2: pd.DataFrame) -> None:
    """Тест проверяет корректное сортирование по убыванию."""

    result = top_transactions(cards_df_2, number_best_transactions=2, reverse=False)

    assert len(result) == 2
    assert result[0]["Имя"] == "Боб"  # 300
    assert result[1]["Имя"] == "Чарли"  # 200

    mock_logger.info.assert_called_once_with("Топ %s транзакций определен.", 2)


@patch("src.utils.logger")
def test_top_transactions_reverse_false(mock_logger: MagicMock, cards_df_2: pd.DataFrame) -> None:
    """Тест проверяет корректное сортирование по возростанию."""

    result = top_transactions(cards_df_2, number_best_transactions=2, reverse=True)

    assert result[0]["Имя"] == "Алиса"  # 100
    assert result[1]["Имя"] == "Чарли"  # 200


@patch("src.utils.logger")
def test_top_transactions_raises_and_logs(mock_logger: MagicMock) -> None:
    """Ошибка: нет нужного столбца."""

    broken_df = pd.DataFrame([{"Имя": "Алиса"}])  # нет нужного столбца

    with pytest.raises(Exception):
        top_transactions(broken_df, number_best_transactions=2)

    mock_logger.exception.assert_called_once_with("Ошибка получения топ транзакций.")


@pytest.mark.parametrize(
    "json_text,expected",
    [
        ('{"a": 1}', {"a": 1}),
        ('{"b": "text", "c": [1, 2]}', {"b": "text", "c": [1, 2]}),
    ],
)
def test_read_json_file_success(json_text: str, expected: Dict[str, Any]) -> None:
    """Проверяет успешное чтение JSON-файла и корректность возвращаемых данных."""

    mock_path = Path("dummy.json")

    with patch("builtins.open", mock_open(read_data=json_text)):
        with patch("src.utils.logger") as mock_logger:
            result = read_json_file(mock_path)
            assert result == expected
            mock_logger.info.assert_called_once_with("Json-файл: %s, успешно прочитан.", mock_path)


def test_read_json_file_failure() -> None:
    """Проверяет, что при ошибке чтения JSON-файла вызывается логгер и выбрасывается исключение."""

    mock_path = Path("invalid.json")

    with patch("builtins.open", side_effect=OSError("File error")):
        with patch("src.utils.logger") as mock_logger:
            mock_logger.exception = Mock()

            with pytest.raises(OSError):
                read_json_file(mock_path)

            mock_logger.exception.assert_called_once_with("Ошибка при чтении Json-файла.")


@pytest.mark.parametrize(
    "currencies, expected_keys",
    [
        (["USD", "EUR"], {"USD", "EUR", "JPY", "RUB"}),
        (["JPY"], {"USD", "EUR", "JPY", "RUB"}),
    ],
)
@patch("src.utils.requests.get")
@patch("src.utils.logger")
def test_exchange_rates_success(
    mock_logger: Mock,
    mock_get: Mock,
    currencies: list[str],
    expected_keys: set,
    mock_api_response: Dict[str, Dict[str, str]],
) -> None:
    """Проверяет успешную обработку ответа от API и корректный пересчёт курсов."""

    mock_response = Mock()
    mock_response.json.return_value = mock_api_response
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = exchange_rates(currencies)

    assert isinstance(result, dict)
    assert set(result.keys()) == expected_keys
    assert result["RUB"] == 1.0
    assert all(isinstance(v, float) for v in result.values())
    mock_logger.info.assert_called_once()


@patch("src.utils.requests.get", side_effect=RequestException("API error"))
@patch("src.utils.logger")
def test_exchange_rates_api_failure(mock_logger: Mock, mock_get: Mock, currency_list: list[str]) -> None:
    """Проверяет, что при ошибке запроса возвращается пустой словарь и логируется исключение."""

    result = exchange_rates(currency_list)
    assert result == {}
    mock_logger.exception.assert_called_once_with("Ошибка при обращении к API конвертации.")


@patch("src.utils.requests.get")
@patch("src.utils.logger")
def test_exchange_rates_json_failure(mock_logger: Mock, mock_get: Mock, currency_list: list[str]) -> None:
    """Проверяет, что при ошибке обработки JSON возвращается пустой словарь и логируется исключение."""

    mock_response = Mock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = exchange_rates(currency_list)
    assert result == {}
    mock_logger.exception.assert_called_once_with("Ошибка обработки данных от API.")


@patch("src.utils.requests.get")
@patch("src.utils.logger")
def test_exchange_rates_calculation_error(mock_logger: Mock, mock_get: Mock) -> None:
    """Проверяет, что ошибка расчёта курса логируется и игнорируется."""

    mock_response = Mock()
    mock_response.json.return_value = {"rates": {"USD": "0", "RUB": "90.0"}}  # вызовет ZeroDivisionError
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = exchange_rates(["USD"])
    assert result == {"RUB": 1.0}
    mock_logger.warning.assert_called_once()


@patch("src.utils.requests.get")
@patch("src.utils.logger")
def test_stock_prices_success(
    mock_logger: Mock, mock_get: Mock, stock_list: List[str], mock_stock_response: Dict[str, Dict[str, str]]
) -> None:
    """Проверяет успешный запрос и пересчёт цены в рубли."""

    mock_response = Mock()
    mock_response.json.return_value = mock_stock_response
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = stock_prices(stock_list, dol_price=90.0)

    assert isinstance(result, list)
    assert len(result) == len(stock_list)
    for item in result:
        assert "stock" in item and "price" in item
        assert isinstance(item["price"], float)
    mock_logger.info.assert_called()


@patch("src.utils.logger")
@patch("src.utils.requests.get")
def test_stock_prices_request_failure(mock_get: Mock, mock_logger: Mock, stock_list: List[str]) -> None:
    """Проверяет, что при ошибке запроса акции пропускаются."""
    # Каждый вызов get выбрасывает RequestException
    mock_get.side_effect = [RequestException("API error") for _ in stock_list]

    result = stock_prices(stock_list, dol_price=90.0)

    assert result == []
    assert mock_logger.exception.call_count == len(stock_list)


@patch("src.utils.requests.get")
@patch("src.utils.logger")
def test_stock_prices_conversion_error(mock_logger: Mock, mock_get: Mock) -> None:
    """Тест проверяет ошибку преобразования цены."""

    mock_response = Mock()
    mock_response.json.return_value = {"Global Quote": {"05. price": "not-a-number"}}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = stock_prices(["AAPL"], dol_price=90.0)
    assert result == []
    mock_logger.exception.assert_called_once()


@patch("src.utils.requests.get")
@patch("src.utils.logger")
def test_stock_prices_missing_data(mock_logger: Mock, mock_get: Mock) -> None:
    """Тест проверяет работу функции, если отсутствуют данные по акциям."""

    mock_response = Mock()
    mock_response.json.return_value = {"Global Quote": {}}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = stock_prices(["AAPL"], dol_price=90.0)
    assert result == []
    mock_logger.warning.assert_called_once()


@pytest.mark.parametrize(
    "currency, expected",
    [
        ("USD", 90.5),
        ("EUR", 98.2),
        ("JPY", 0.62),
    ],
)
@patch("src.utils.logger")
def test_dollar_to_ruble_price_success(
    mock_logger: Mock, exchange_rates: dict, currency: str, expected: float
) -> None:
    """Проверяет корректное извлечение курса валюты и логгирование."""

    result = dollar_to_ruble_price(exchange_rates, currency)
    assert result == expected
    mock_logger.info.assert_called_once_with("Стоимость %s успешно определена.", currency)


@patch("src.utils.logger")
def test_dollar_to_ruble_price_type_error_dict(_: Mock) -> None:
    """Проверяет, что при неверном типе словаря выбрасывается TypeError."""

    with pytest.raises(TypeError, match="dict_exchange_rate должен быть dict"):
        dollar_to_ruble_price(["USD", "90.5"], "USD")  # type: ignore[arg-type]


@patch("src.utils.logger")
def test_dollar_to_ruble_price_type_error_currency(_: Mock, exchange_rates: dict) -> None:
    """Проверяет, что при неверном типе валюты выбрасывается TypeError."""

    with pytest.raises(TypeError, match="currency должен быть str"):
        dollar_to_ruble_price(exchange_rates, 123)  # type: ignore[arg-type]


@patch("src.utils.logger")
def test_dollar_to_ruble_price_missing_currency(_: Mock, exchange_rates: dict) -> None:
    """Проверяет, что при отсутствии валюты выбрасывается ValueError."""

    with pytest.raises(ValueError, match="Нет курса для валюты: GBP"):
        dollar_to_ruble_price(exchange_rates, "GBP")
