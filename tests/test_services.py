import json
from pathlib import Path
from typing import Union
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.services import favorable_categories, filter_date, group_categories


@pytest.mark.parametrize(
    "year, month, expected_count",
    [
        (2023, 1, 2),
        ("2023", "2", 1),
        (2022, 1, 1),
        (2023, 3, 1),
        (2024, 1, 0),
    ],
)
def test_filter_date_valid(
    sample_dataframe: pd.DataFrame, year: Union[int, str], month: Union[int, str], expected_count: int
) -> None:
    """
    Проверяет, что функция корректно фильтрует транзакции по году и месяцу.
    """

    result = filter_date(sample_dataframe, year, month)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == expected_count


@pytest.mark.parametrize(
    "year, month",
    [
        ("не год", 1),
        (2023, "не месяц"),
        (None, 1),
        (2023, None),
    ],
)
def test_filter_date_type_errors(sample_dataframe: pd.DataFrame, year: object, month: object) -> None:
    """
    Проверяет, что при передаче некорректных значений года или месяца выбрасывается исключение.
    """

    with pytest.raises(Exception):
        filter_date(sample_dataframe, year, month)  # type: ignore[arg-type]


@patch("src.services.logger")
def test_filter_date_missing_column(mock_logger: Mock) -> None:
    """
    Проверяет, что при отсутствии колонки 'Дата операции' выбрасывается KeyError и логируется ошибка.
    """

    df = pd.DataFrame({"Сумма": [100, 200]})

    with pytest.raises(KeyError):
        filter_date(df, 2023, 1)

    mock_logger.exception.assert_called_once()


@patch("src.services.logger")
def test_filter_date_invalid_date_format(mock_logger: Mock, sample_dataframe: pd.DataFrame) -> None:
    """
    Проверяет, что некорректные строки дат не мешают фильтрации, но логируются.
    """

    result = filter_date(sample_dataframe, 2023, 1)
    assert len(result) == 2
    mock_logger.exception.assert_not_called()  # не должно быть исключения


def test_group_categories_success(cashback_dataframe: pd.DataFrame) -> None:
    """
    Проверяет, что функция корректно группирует кэшбэк по категориям.
    """

    result = group_categories(cashback_dataframe)

    assert isinstance(result, pd.Series)
    assert result["еда"] == pytest.approx(17.5)
    assert result["транспорт"] == pytest.approx(8.0)
    assert result["развлечения"] == pytest.approx(12.0)


def test_group_categories_type_error() -> None:
    """
    Проверяет, что при передаче не-DataFrame выбрасывается TypeError.
    """

    with pytest.raises(TypeError, match="df должен быть pd.DataFrame"):
        group_categories("не датафрейм")  # type: ignore[arg-type]


@patch("src.services.logger")
def test_group_categories_missing_column_category(mock_logger: Mock) -> None:
    """
    Проверяет, что при отсутствии колонки 'Категория' выбрасывается KeyError и логируется.
    """

    df = pd.DataFrame({"Кэшбэк": [10.0, 5.0]})

    with pytest.raises(KeyError):
        group_categories(df)

    mock_logger.exception.assert_called_once()


@patch("src.services.logger")
def test_group_categories_missing_column_cashback(mock_logger: Mock) -> None:
    """
    Проверяет, что при отсутствии колонки 'Кэшбэк' выбрасывается KeyError и логируется.
    """
    df = pd.DataFrame({"Категория": ["еда", "транспорт"]})

    with pytest.raises(KeyError):
        group_categories(df)

    mock_logger.exception.assert_called_once()


def test_favorable_categories_invalid_types() -> None:
    """
    Проверяет, что при неверных типах year/month выбрасывается TypeError.
    """

    with pytest.raises(TypeError, match="Неверный тип входных данных"):
        favorable_categories(Path("test_file.xlsx"), year=3.14, month=["январь"])  # type: ignore[arg-type]


@patch("src.services.read_excel_file")
@patch("src.services.filter_date")
@patch("src.services.group_categories")
@patch("src.services.logger")
def test_favorable_categories_json_error(
    mock_logger: Mock, mock_group: Mock, mock_filter: Mock, mock_read: Mock
) -> None:
    """
    Проверяет, что ошибка сериализации JSON (например, из-за неподдерживаемого типа) логируется и выбрасывается.
    """
    mock_read.return_value = pd.DataFrame()
    mock_filter.return_value = pd.DataFrame()
    mock_group.return_value = pd.Series({"еда": {1, 2}})

    with pytest.raises(TypeError):
        favorable_categories(Path("test_file.xlsx"), year=2024, month=5)

    mock_logger.exception.assert_called_once()


@patch("src.services.read_excel_file", side_effect=RuntimeError("Ошибка чтения файла"))
@patch("src.services.logger")
def test_favorable_categories_unexpected_error(mock_logger: Mock, mock_read: Mock) -> None:
    """
    Проверяет, что неожиданная ошибка логируется и выбрасывается.
    """

    with pytest.raises(RuntimeError, match="Ошибка чтения файла"):
        favorable_categories(Path("test_file.xlsx"), year=2024, month=5)

    mock_logger.exception.assert_called_once()


@patch("src.services.read_excel_file")
@patch("src.services.filter_date")
@patch("src.services.group_categories")
def test_favorable_categories_success(mock_group: Mock, mock_filter: Mock, mock_read: Mock) -> None:
    """
    Проверяет, что функция возвращает корректный JSON при успешной работе.
    """

    mock_read.return_value = pd.DataFrame()
    mock_filter.return_value = pd.DataFrame()
    mock_group.return_value = pd.Series({"еда": 17.5, "транспорт": 8.0})

    result = favorable_categories(Path("test_file.xlsx"), year="2024", month="5")
    parsed = json.loads(result)

    assert parsed["еда"] == pytest.approx(17.5)
    assert parsed["транспорт"] == pytest.approx(8.0)
