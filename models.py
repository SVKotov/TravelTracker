"""
Модуль models.py
Определяет основные классы данных приложения TravelTracker.
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, List
from enum import Enum


class ExpenseCategory(Enum):
    """Категории расходов во время путешествия."""
    TRANSPORT = "Транспорт"
    ACCOMMODATION = "Жильё"
    FOOD = "Еда"
    ENTERTAINMENT = "Развлечения"
    SHOPPING = "Шоппинг"
    SIGHTSEEING = "Достопримечательности"
    OTHER = "Другое"


class TripStatus(Enum):
    """Статусы путешествия."""
    PLANNED = "Запланировано"
    IN_PROGRESS = "В процессе"
    COMPLETED = "Завершено"
    CANCELLED = "Отменено"


@dataclass
class Trip:
    """Класс, описывающий путешествие."""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: float = 0.0
    actual_spent: float = 0.0
    currency: str = "USD"
    destination: str = ""
    status: TripStatus = TripStatus.PLANNED
    participants: str = ""  # Список участников через запятую
    
    @property
    def duration_days(self) -> int:
        """Расчёт продолжительности поездки в днях."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    @property
    def budget_balance(self) -> float:
        """Остаток бюджета."""
        return self.budget - self.actual_spent


@dataclass
class Expense:
    """Класс, описывающий расход во время путешествия."""
    id: Optional[int] = None
    trip_id: int = 0
    amount: float = 0.0
    currency: str = "USD"
    category: ExpenseCategory = ExpenseCategory.OTHER
    date: Optional[date] = None
    description: str = ""
    payment_method: str = "Наличные"  # Карта, наличные и т.д.
    location: str = ""  # Место совершения расхода
    
    def __post_init__(self):
        """Валидация данных."""
        if self.amount <= 0:
            raise ValueError("Сумма расхода должна быть положительной")