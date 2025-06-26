import logging
from typing import Literal
from pathlib import Path

LogLevel = int | Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def get_logger(
    name: str,
    level: LogLevel = "INFO",
    log_file: str | None = None,
    fmt: str = "%(asctime)s [%(levelname)-5s] %(module)s.%(funcName)s:%(lineno)d - %(message)s",
    mode: str = "w",
) -> logging.Logger:
    """
    Универсальная настройка логгера для конкретного модуля.

    :param name: Имя логгера (обычно __name__)
    :param level: Уровень логирования (например, "INFO")
    :param log_file: Путь к лог-файлу (если нужно писать логи в файл)
    :param fmt: Формат сообщения
    :param mode: Режим записи логов
    :return: Настроенный логгер
    """
    logger = logging.getLogger(name)

    # Если у логгера еще нет обработчиков, добавляем их.
    if not logger.handlers:
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(level)
        formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")

        # # Добавляем обработчик для консоли
        # console_handler = logging.StreamHandler()
        # console_handler.setFormatter(formatter)
        # logger.addHandler(console_handler)

        # Добавляем обработчик для файла, если указано
        if log_file:
            logs_dir = Path(__file__).resolve().parent.parent / "logs"
            log_path = logs_dir / log_file
            file_handler = logging.FileHandler(log_path, mode=mode, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
