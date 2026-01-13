"""
Настройка логирования для приложения.
Простое логирование в файл и консоль.
"""
import logging
import os


def setup_logging():
    """
    Настраивает логирование: в файл logs/app.log и в консоль.
    Уровень: INFO
    Формат: "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    """
    # Создаем директорию для логов, если её нет
    logs_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    log_file = os.path.join(logs_dir, 'app.log')
    
    # Формат логов
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    
    # Настраиваем root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Удаляем существующие handlers, если есть
    logger.handlers.clear()
    
    # Handler для файла
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Handler для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

