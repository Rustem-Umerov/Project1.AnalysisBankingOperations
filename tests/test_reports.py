from datetime import date
from typing import Optional
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.reports import date_range_calculation, spending_by_category


@pytest.mark.parametrize(
    "date_str, expected",
    [
        ("01.01.2023", date(2023, 1, 1)),
        ("15.08.2022", date(2022, 8, 15)),
        ("31.12.2020", date(2020, 12, 31)),
    ],
)
def test_date_range_calculation_valid(date_str: str, expected: date) -> None:
    """Проверяет корректную конвертацию строки в дату."""

    result = date_range_calculation(date_str)
    assert result == expected


@pytest.mark.parametrize(
    "date_str, frmt, expected",
    [
        ("2023-01-01", "%Y-%m-%d", date(2023, 1, 1)),
        ("08/15/2022", "%m/%d/%Y", date(2022, 8, 15)),
    ],
)
def test_date_range_calculation_custom_format(date_str: str, frmt: str, expected: date) -> None:
    """Проверяет работу функции с нестандартными форматами дат."""

    result = date_range_calculation(date_str, frmt)
    assert result == expected


@pytest.mark.parametrize("date_str", ["2023/01/01", "15-08-2022", "31.13.2020"])
def test_date_range_calculation_invalid_format(date_str: str) -> None:
    """Проверяет, что при неверном формате выбрасывается ValueError."""

    with pytest.raises(ValueError):
        date_range_calculation(date_str)


@pytest.mark.parametrize("bad_input", [123, 3.14, ["01.01.2023"], {"date": "01.01.2023"}])
def test_date_range_calculation_type_error(bad_input: Optional[str]) -> None:
    """Проверяет, что при неверном типе аргумента выбрасывается TypeError."""

    with pytest.raises(TypeError, match="date_str должен быть str или None"):
        date_range_calculation(bad_input)  # type: ignore[arg-type]


@patch("src.reports.date")
def test_date_range_calculation_default_today(mock_date: Mock) -> None:
    """Проверяет, что при отсутствии аргумента возвращается текущая дата."""

    mock_date.today.return_value = date(2024, 1, 1)
    result = date_range_calculation(None)
    assert result == date(2024, 1, 1)
    mock_date.today.assert_called_once()


@pytest.mark.parametrize(
    "input_category, expected_count",
    [
        ("еда", 3),
        ("Еда", 3),
        ("  еда  ", 3),
        ("транспорт", 1),
        ("развлечения", 1),
        ("неизвестно", 0),
    ],
)
def test_spending_by_category_filtering(
    sample_transactions: pd.DataFrame, input_category: str, expected_count: int
) -> None:
    """
    Проверяет, что функция корректно фильтрует транзакции по категории,
    независимо от регистра, пробелов и отсутствующих значений.
    """

    result = spending_by_category(sample_transactions, input_category)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == expected_count


@pytest.mark.parametrize(
    "transactions, category, error_type",
    [
        ("не DataFrame", "еда", TypeError),
        (pd.DataFrame(), 123, TypeError),
    ],
)
def test_spending_by_category_type_errors(transactions: object, category: object, error_type: type[Exception]) -> None:
    """
    Проверяет, что функция выбрасывает TypeError при передаче аргументов неверного типа.
    """

    with pytest.raises(error_type):
        spending_by_category(transactions, category)  # type: ignore[arg-type]


@patch("src.reports.logger")
def test_spending_by_category_logs_exception(mock_logger: Mock, sample_transactions: pd.DataFrame) -> None:
    """
    Проверяет, что при возникновении исключения функция логирует ошибку.
    """

    broken_df = sample_transactions.rename(columns={"Категория": "WrongColumn"})

    with pytest.raises(Exception):
        spending_by_category(broken_df, "еда")

    mock_logger.exception.assert_called_once()
    assert "еда" in str(mock_logger.exception.call_args)
