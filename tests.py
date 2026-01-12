"""
Модуль tests.py
Unit-тесты для приложения TravelTracker.
"""
import unittest
import os
import tempfile
from datetime import date
from models import Trip, Expense, ExpenseCategory, TripStatus
from storage import TravelStorage
from utils import validate_date_range, validate_currency_amount
from analysis import TravelAnalyzer


class TestModels(unittest.TestCase):
    """Тесты для моделей данных."""
    
    def test_trip_creation(self):
        """Тест создания объекта Trip."""
        trip = Trip(
            name="Отпуск в Париже",
            destination="Париж, Франция",
            start_date=date(2024, 6, 1),
            end_date=date(2024, 6, 10),
            budget=2000.0,
            currency="USD"
        )
        
        self.assertEqual(trip.name, "Отпуск в Париже")
        self.assertEqual(trip.duration_days, 10)
        self.assertEqual(trip.budget_balance, 2000.0)
    
    def test_expense_validation(self):
        """Тест валидации расхода."""
        # Корректный расход
        expense = Expense(
            amount=100.0,
            category=ExpenseCategory.FOOD,
            date=date(2024, 6, 2)
        )
        
        # Неверная сумма (должна вызывать исключение)
        with self.assertRaises(ValueError):
            Expense(amount=-50.0)


class TestStorage(unittest.TestCase):
    """Тесты для работы с хранилищем."""
    
    def setUp(self):
        """Создание временной базы данных для тестов."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.storage = TravelStorage(self.db_path)
    
    def tearDown(self):
        """Удаление временной базы данных."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_add_and_get_trip(self):
        """Тест добавления и получения путешествия."""
        trip = Trip(
            name="Тестовое путешествие",
            destination="Тест",
            budget=1000.0
        )
        
        trip_id = self.storage.add_trip(trip)
        self.assertGreater(trip_id, 0)
        
        trips = self.storage.get_all_trips()
        self.assertEqual(len(trips), 1)
        self.assertEqual(trips[0].name, "Тестовое путешествие")
    
    def test_add_expense(self):
        """Тест добавления расхода."""
        # Сначала создаем путешествие
        trip = Trip(name="Тест", budget=1000.0)
        trip_id = self.storage.add_trip(trip)
        
        # Добавляем расход
        expense = Expense(
            trip_id=trip_id,
            amount=150.0,
            category=ExpenseCategory.TRANSPORT
        )
        
        expense_id = self.storage.add_expense(expense)
        self.assertGreater(expense_id, 0)
        
        # Проверяем, что расход добавился
        expenses = self.storage.get_expenses_by_trip(trip_id)
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses[0].amount, 150.0)


class TestUtils(unittest.TestCase):
    """Тесты вспомогательных функций."""
    
    def test_validate_date_range(self):
        """Тест валидации диапазона дат."""
        # Корректный диапазон
        success, message = validate_date_range("2024-06-01", "2024-06-10")
        self.assertTrue(success)
        self.assertEqual(message, "")
        
        # Неверный формат даты
        success, message = validate_date_range("2024-13-01", "2024-06-10")
        self.assertFalse(success)
        
        # Дата начала позже даты окончания
        success, message = validate_date_range("2024-06-10", "2024-06-01")
        self.assertFalse(success)
        self.assertIn("не может быть позже", message)
    
    def test_validate_currency_amount(self):
        """Тест валидации денежной суммы."""
        # Корректная сумма
        success, value, message = validate_currency_amount("150.50")
        self.assertTrue(success)
        self.assertEqual(value, 150.50)
        self.assertEqual(message, "")
        
        # Неверный формат
        success, value, message = validate_currency_amount("150.555")
        self.assertFalse(success)
        
        # Отрицательная сумма
        success, value, message = validate_currency_amount("-100")
        self.assertFalse(success)


class TestAnalysis(unittest.TestCase):
    """Тесты анализа данных."""
    
    def test_expense_summary(self):
        """Тест сводки по расходам."""
        # Создаем тестовые данные
        trip = Trip(id=1, name="Тест", budget=1000.0)
        
        expenses = [
            Expense(trip_id=1, amount=100.0, category=ExpenseCategory.FOOD),
            Expense(trip_id=1, amount=200.0, category=ExpenseCategory.TRANSPORT),
            Expense(trip_id=1, amount=50.0, category=ExpenseCategory.FOOD)
        ]
        
        analyzer = TravelAnalyzer([trip], expenses)
        summary = analyzer.get_trip_expense_summary(1)
        
        self.assertEqual(summary['total'], 350.0)
        self.assertEqual(summary['by_category']['Еда'], 150.0)
        self.assertEqual(summary['by_category']['Транспорт'], 200.0)
        self.assertEqual(summary['expense_count'], 3)


if __name__ == '__main__':
    unittest.main()