"""
Модуль storage.py
Работа с базой данных SQLite.
"""
import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import date
from models import Trip, Expense, ExpenseCategory, TripStatus


class TravelStorage:
    """Класс для работы с базой данных путешествий."""
    
    def __init__(self, db_path: str = "data/traveltracker.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Инициализация базы данных, создание таблиц."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица путешествий
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    budget REAL,
                    actual_spent REAL DEFAULT 0,
                    currency TEXT,
                    destination TEXT,
                    status TEXT,
                    participants TEXT
                )
            ''')
            
            # Таблица расходов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trip_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT,
                    category TEXT,
                    date TEXT,
                    description TEXT,
                    payment_method TEXT,
                    location TEXT,
                    FOREIGN KEY (trip_id) REFERENCES trips (id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
    
    def add_trip(self, trip: Trip) -> int:
        """Добавление путешествия в базу данных."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trips (name, description, start_date, end_date, budget, 
                                  actual_spent, currency, destination, status, participants)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trip.name,
                trip.description,
                trip.start_date.isoformat() if trip.start_date else None,
                trip.end_date.isoformat() if trip.end_date else None,
                trip.budget,
                trip.actual_spent,
                trip.currency,
                trip.destination,
                trip.status.value,
                trip.participants
            ))
            
            trip_id = cursor.lastrowid
            conn.commit()
            
            return trip_id if trip_id else 0
    
    def add_expense(self, expense: Expense) -> int:
        """Добавление расхода в базу данных."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO expenses (trip_id, amount, currency, category, date, 
                                     description, payment_method, location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                expense.trip_id,
                expense.amount,
                expense.currency,
                expense.category.value,
                expense.date.isoformat() if expense.date else None,
                expense.description,
                expense.payment_method,
                expense.location
            ))
            
            expense_id = cursor.lastrowid
            conn.commit()
            
            # Обновляем actual_spent в путешествии
            cursor.execute('''
                UPDATE trips
                SET actual_spent = (
                    SELECT COALESCE(SUM(amount), 0)
                    FROM expenses
                    WHERE trip_id = ?
                )
                WHERE id = ?
            ''', (expense.trip_id, expense.trip_id))
            
            conn.commit()
            
            return expense_id if expense_id else 0
    
    def get_all_trips(self) -> List[Trip]:
        """Получение всех путешествий."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM trips ORDER BY id DESC')
            rows = cursor.fetchall()
            
            trips = []
            for row in rows:
                trip = Trip(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    start_date=date.fromisoformat(row[3]) if row[3] else None,
                    end_date=date.fromisoformat(row[4]) if row[4] else None,
                    budget=row[5],
                    actual_spent=row[6],
                    currency=row[7],
                    destination=row[8],
                    status=TripStatus(row[9]),
                    participants=row[10]
                )
                trips.append(trip)
            
            return trips
    
    def get_expenses_by_trip(self, trip_id: int) -> List[Expense]:
        """Получение всех расходов по ID путешествия."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM expenses
                WHERE trip_id = ?
                ORDER BY date DESC
            ''', (trip_id,))
            
            rows = cursor.fetchall()
            
            expenses = []
            for row in rows:
                expense = Expense(
                    id=row[0],
                    trip_id=row[1],
                    amount=row[2],
                    currency=row[3],
                    category=ExpenseCategory(row[4]),
                    date=date.fromisoformat(row[5]) if row[5] else None,
                    description=row[6],
                    payment_method=row[7],
                    location=row[8]
                )
                expenses.append(expense)
            
            return expenses
    
    def delete_trip(self, trip_id: int) -> bool:
        """Удаление путешествия по ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM trips WHERE id = ?', (trip_id,))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def delete_expense(self, expense_id: int) -> bool:
        """Удаление расхода по ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def update_trip(self, trip: Trip) -> bool:
        """Обновление данных о путешествии."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE trips
                SET name = ?, description = ?, start_date = ?, end_date = ?, 
                    budget = ?, actual_spent = ?, currency = ?, destination = ?, 
                    status = ?, participants = ?
                WHERE id = ?
            ''', (
                trip.name,
                trip.description,
                trip.start_date.isoformat() if trip.start_date else None,
                trip.end_date.isoformat() if trip.end_date else None,
                trip.budget,
                trip.actual_spent,
                trip.currency,
                trip.destination,
                trip.status.value,
                trip.participants,
                trip.id
            ))
            
            conn.commit()
            
            return cursor.rowcount > 0
    
    def get_total_expenses_by_trip(self, trip_id: int) -> float:
        """Получение суммы расходов по путешествию."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0)
                FROM expenses
                WHERE trip_id = ?
            ''', (trip_id,))
            
            result = cursor.fetchone()
            return result[0] if result else 0.0
    
    def export_trip_to_json(self, trip_id: int, filename: str) -> bool:
        """Экспорт данных о путешествии в JSON файл."""
        try:
            # Получаем данные о путешествии
            trips = self.get_all_trips()
            trip = None
            for t in trips:
                if t.id == trip_id:
                    trip = t
                    break
            
            if not trip:
                return False
            
            # Получаем расходы
            expenses = self.get_expenses_by_trip(trip_id)
            
            # Формируем структуру данных
            data = {
                'trip': {
                    'id': trip.id,
                    'name': trip.name,
                    'description': trip.description,
                    'start_date': trip.start_date.isoformat() if trip.start_date else None,
                    'end_date': trip.end_date.isoformat() if trip.end_date else None,
                    'budget': trip.budget,
                    'actual_spent': trip.actual_spent,
                    'currency': trip.currency,
                    'destination': trip.destination,
                    'status': trip.status.value,
                    'participants': trip.participants,
                    'duration_days': trip.duration_days,
                    'budget_balance': trip.budget_balance
                },
                'expenses': [
                    {
                        'id': exp.id,
                        'trip_id': exp.trip_id,
                        'amount': exp.amount,
                        'currency': exp.currency,
                        'category': exp.category.value,
                        'date': exp.date.isoformat() if exp.date else None,
                        'description': exp.description,
                        'payment_method': exp.payment_method,
                        'location': exp.location
                    }
                    for exp in expenses
                ]
            }
            
            # Сохраняем в файл
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Ошибка при экспорте в JSON: {e}")
            return False
    
    def get_trip_by_id(self, trip_id: int) -> Optional[Trip]:
        """Получение путешествия по ID."""
        trips = self.get_all_trips()
        for trip in trips:
            if trip.id == trip_id:
                return trip
        return None