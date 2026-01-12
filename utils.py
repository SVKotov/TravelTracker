"""
Модуль utils.py
Вспомогательные функции для валидации и обработки данных.
"""
import re
from datetime import datetime, date
from typing import Optional, Tuple
import pandas as pd


def validate_date_range(start_date_str: str, end_date_str: str) -> Tuple[bool, str]:
    """
    Проверка корректности диапазона дат.
    Возвращает (успех, сообщение_об_ошибке)
    """
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        if start_date > end_date:
            return False, "Дата начала не может быть позже даты окончания"
        
        if start_date < date.today():
            return False, "Дата начала не может быть в прошлом (для новых поездок)"
        
        return True, ""
    except ValueError:
        return False, "Неверный формат даты. Используйте ГГГГ-ММ-ДД"


def validate_currency_amount(amount_str: str) -> Tuple[bool, float, str]:
    """
    Проверка и преобразование суммы.
    Возвращает (успех, значение, сообщение_об_ошибке)
    """
    # Удаляем пробелы и заменяем запятые на точки
    clean_str = amount_str.strip().replace(',', '.')
    
    # Проверяем формат с помощью регулярного выражения
    pattern = r'^\d+(\.\d{1,2})?$'
    if not re.match(pattern, clean_str):
        return False, 0.0, "Неверный формат суммы. Используйте числа с максимум двумя знаками после запятой"
    
    try:
        amount = float(clean_str)
        if amount <= 0:
            return False, 0.0, "Сумма должна быть положительной"
        
        return True, amount, ""
    except ValueError:
        return False, 0.0, "Неверный формат суммы"


def validate_email(email: str) -> bool:
    """Проверка корректности email (для будущих функций отправки отчетов)."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_input(text: str, max_length: int = 500) -> str:
    """Очистка вводимых данных от потенциально опасных символов."""
    # Удаляем лишние пробелы
    text = text.strip()
    
    # Обрезаем до максимальной длины
    if len(text) > max_length:
        text = text[:max_length]
    
    # Экранируем специальные символы HTML (для безопасности в веб-версии)
    text = (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    return text


def format_currency(amount: float, currency: str = "USD") -> str:
    """Форматирование денежной суммы."""
    currency_symbols = {
        "USD": "$",
        "EUR": "€",
        "RUB": "₽",
        "GBP": "£"
    }
    
    symbol = currency_symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def calculate_daily_budget(total_budget: float, days: int) -> float:
    """Расчёт дневного бюджета."""
    if days <= 0:
        return 0.0
    return total_budget / days