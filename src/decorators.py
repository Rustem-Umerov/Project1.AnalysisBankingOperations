from datetime import datetime
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

import pandas as pd

from src.logging import get_logger

T = TypeVar("T")
P = ParamSpec("P")


def write_to_file(filename: str | None = None) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Декоратор для функций-отчетов, который записывает в файл результат, который возвращает функция, формирующая отчет.

    Логирует:
      - начало выполнения функции;
      - переданные позиционные и именованные аргументы;
      - успешное завершение с результатом.

    В случае, если возникнет исключение:
      - исключение, если оно возникает, с типом и трассировкой.

    :param filename: Опциональный путь к файлу. Если не указан — используется имя по умолчанию.
    :return: Декоратор, который можно применить к любой функции.
    """

    def my_decorator(func: Callable[P, T]) -> Callable[P, T]:

        module_name = getattr(func, "__module__", __name__)
        logger = get_logger(module_name, log_file=filename)

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            """Обертка для декорируемой функции"""

            logger.info(
                "Starting function %s with arguments: args=%s, kwargs=%s",
                func.__name__,
                args,
                kwargs
            )

            try:
                result = func(*args, **kwargs)

                if isinstance(result, pd.DataFrame):
                    output_filename = filename or datetime.now().strftime("report_%Y%m%d_%H%M%S.json")
                    result.to_json(output_filename, orient="records", force_ascii=False, indent=2)
                    logger.info("Result saved to file: %s", output_filename)
                else:
                    logger.warning(
                        "Function %s returned non-DataFrame result; skipping file write.",
                        func.__name__
                    )

                logger.info("Function %s completed successfully.", func.__name__)
                return result

            except Exception as e:
                logger.exception(
                    "Error in function %s. Error type: %s. Arguments: args=%s, kwargs=%s",
                    func.__name__,
                    type(e).__name__,
                    args,
                    kwargs,
                )
                raise

        return wrapper

    return my_decorator
