"""
Модуль analysis.py
Анализ расходов и визуализация данных.
Обновленная версия с анализом всех путешествий.
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from models import Trip, Expense, ExpenseCategory
import numpy as np
import json


class TravelAnalyzer:
    """Класс для анализа данных о путешествиях и расходах."""
    
    def __init__(self, trips: List[Trip], expenses: List[Expense]):
        self.trips = trips
        self.expenses = expenses
        self.df_trips = self._create_trips_dataframe()
        self.df_expenses = self._create_expenses_dataframe()
    
    def _create_trips_dataframe(self) -> pd.DataFrame:
        """Создание DataFrame из списка путешествий."""
        data = []
        for trip in self.trips:
            data.append({
                'id': trip.id,
                'name': trip.name,
                'destination': trip.destination,
                'start_date': trip.start_date,
                'end_date': trip.end_date,
                'duration_days': trip.duration_days,
                'budget': trip.budget,
                'actual_spent': trip.actual_spent,
                'budget_balance': trip.budget_balance,
                'currency': trip.currency,
                'status': trip.status.value,
                'participants_count': len(trip.participants.split(',')) if trip.participants else 1
            })
        return pd.DataFrame(data)
    
    def _create_expenses_dataframe(self) -> pd.DataFrame:
        """Создание DataFrame из списка расходов."""
        data = []
        for expense in self.expenses:
            data.append({
                'id': expense.id,
                'trip_id': expense.trip_id,
                'amount': expense.amount,
                'currency': expense.currency,
                'category': expense.category.value,
                'date': expense.date,
                'description': expense.description,
                'payment_method': expense.payment_method,
                'location': expense.location
            })
        return pd.DataFrame(data)
    
    # --- Методы для анализа одного путешествия ---
    
    def get_trip_expense_summary(self, trip_id: int) -> Dict[str, Any]:
        """Получение сводки по расходам для конкретного путешествия."""
        if self.df_expenses.empty:
            return {}
        
        trip_expenses = self.df_expenses[self.df_expenses['trip_id'] == trip_id]
        
        if trip_expenses.empty:
            return {
                'total': 0,
                'by_category': {},
                'daily_avg': 0,
                'max_expense': 0,
                'expense_count': 0
            }
        
        total = trip_expenses['amount'].sum()
        by_category = trip_expenses.groupby('category')['amount'].sum().to_dict()
        
        # Средний дневной расход
        trip_dates = trip_expenses['date'].dropna()
        if not trip_dates.empty and len(trip_dates) > 1:
            days = (trip_dates.max() - trip_dates.min()).days + 1
            daily_avg = total / days if days > 0 else total
        else:
            daily_avg = total
        
        max_expense = trip_expenses['amount'].max()
        
        return {
            'total': total,
            'by_category': by_category,
            'daily_avg': daily_avg,
            'max_expense': max_expense,
            'expense_count': len(trip_expenses)
        }
    
    def plot_expense_categories(self, trip_id: int, ax=None) -> plt.Figure:
        """
        Визуализация расходов по категориям (круговая диаграмма).
        Возвращает объект Figure для встраивания в Tkinter.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 5))
        else:
            fig = ax.get_figure()
        
        trip_expenses = self.df_expenses[self.df_expenses['trip_id'] == trip_id]
        
        if trip_expenses.empty:
            ax.text(0.5, 0.5, 'Нет данных о расходах\nдля построения графика', 
                   ha='center', va='center', fontsize=12)
            ax.set_title('Распределение расходов по категориям')
            return fig
        
        category_totals = trip_expenses.groupby('category')['amount'].sum()
        
        if len(category_totals) == 0:
            ax.text(0.5, 0.5, 'Нет данных о расходах\nдля построения графика', 
                   ha='center', va='center', fontsize=12)
            ax.set_title('Распределение расходов по категориям')
            return fig
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(category_totals)))
        wedges, texts, autotexts = ax.pie(
            category_totals.values, 
            labels=category_totals.index, 
            autopct='%1.1f%%', 
            colors=colors, 
            startangle=90,
            pctdistance=0.85
        )
        
        # Улучшаем читаемость текста
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(9)
        
        for text in texts:
            text.set_fontsize(9)
        
        ax.set_title(f'Распределение расходов по категориям\n(Всего: {category_totals.sum():.2f})', 
                    fontsize=11, pad=20)
        
        return fig
    
    def plot_daily_expenses(self, trip_id: int, ax=None) -> plt.Figure:
        """
        График ежедневных расходов.
        Возвращает объект Figure для встраивания в Tkinter.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 5))
        else:
            fig = ax.get_figure()
        
        trip_expenses = self.df_expenses[self.df_expenses['trip_id'] == trip_id].copy()
        
        if trip_expenses.empty:
            ax.text(0.5, 0.5, 'Нет данных о расходах\nдля построения графика', 
                   ha='center', va='center', fontsize=12)
            ax.set_title('Ежедневные расходы')
            return fig
        
        # Группировка по дате
        trip_expenses['date'] = pd.to_datetime(trip_expenses['date'])
        daily_expenses = trip_expenses.groupby('date')['amount'].sum().reset_index()
        
        if len(daily_expenses) < 2:
            ax.text(0.5, 0.5, 'Недостаточно данных\nдля построения графика', 
                   ha='center', va='center', fontsize=12)
            ax.set_title('Ежедневные расходы')
            return fig
        
        ax.plot(daily_expenses['date'], daily_expenses['amount'], 
               marker='o', linewidth=2, markersize=6, color='steelblue')
        
        # Добавляем линию среднего значения
        avg_expense = daily_expenses['amount'].mean()
        ax.axhline(y=avg_expense, color='red', linestyle='--', 
                  linewidth=1.5, alpha=0.7, 
                  label=f'Среднее: {avg_expense:.2f}')
        
        # Настройка внешнего вида
        ax.set_title('Ежедневные расходы во время путешествия', fontsize=11, pad=15)
        ax.set_xlabel('Дата', fontsize=10)
        ax.set_ylabel('Сумма расходов', fontsize=10)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        
        # Поворачиваем подписи дат для лучшей читаемости
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=9)
        plt.setp(ax.get_yticklabels(), fontsize=9)
        
        # Автонастройка макета
        fig.tight_layout()
        
        return fig
    
    def plot_budget_vs_actual(self, trip_id: int, ax=None) -> plt.Figure:
        """
        Сравнение бюджета с фактическими расходами.
        Возвращает объект Figure для встраивания в Tkinter.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 5))
        else:
            fig = ax.get_figure()
        
        trip_info = self.df_trips[self.df_trips['id'] == trip_id]
        
        if trip_info.empty:
            ax.text(0.5, 0.5, 'Информация о путешествии\nне найдена', 
                   ha='center', va='center', fontsize=12)
            ax.set_title('Бюджет vs Фактические расходы')
            return fig
        
        trip = trip_info.iloc[0]
        
        categories = ['Бюджет', 'Фактические\nрасходы']
        values = [trip['budget'], trip['actual_spent']]
        
        colors = ['lightblue', 'lightcoral']
        bars = ax.bar(categories, values, color=colors, edgecolor='black', linewidth=1)
        
        # Добавляем значения на столбцы
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + max(values)*0.02,
                   f'{value:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Настройка внешнего вида
        ax.set_title(f'Бюджет vs Фактические расходы\n{trip["name"]}', 
                    fontsize=11, pad=15)
        ax.set_ylabel('Сумма', fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Устанавливаем разметку оси Y
        ax.tick_params(axis='x', labelsize=10)
        ax.tick_params(axis='y', labelsize=9)
        
        # Добавляем горизонтальную линию для бюджета
        ax.axhline(y=trip['budget'], color='blue', linestyle=':', alpha=0.5, linewidth=1)
        
        return fig
    
    def plot_expense_statistics(self, trip_id: int, ax=None) -> plt.Figure:
        """
        График со статистикой и рекомендациями.
        Возвращает объект Figure для встраивания в Tkinter.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 5))
        else:
            fig = ax.get_figure()
        
        ax.axis('off')  # Отключаем оси
        
        summary = self.get_trip_expense_summary(trip_id)
        recommendations = self.get_trip_recommendations(trip_id)
        
        # Формируем текст статистики
        stats_text = f"📊 Сводка по расходам:\n\n"
        
        if summary.get('expense_count', 0) > 0:
            stats_text += f"• Всего расходов: {summary.get('expense_count', 0)}\n"
            stats_text += f"• Общая сумма: {summary.get('total', 0):.2f}\n"
            stats_text += f"• Средний дневной расход: {summary.get('daily_avg', 0):.2f}\n"
            stats_text += f"• Максимальный расход: {summary.get('max_expense', 0):.2f}\n\n"
            
            # Добавляем распределение по категориям
            if summary.get('by_category'):
                stats_text += "📈 По категориям:\n"
                for category, amount in summary['by_category'].items():
                    percentage = (amount / summary['total'] * 100) if summary['total'] > 0 else 0
                    stats_text += f"  {category}: {amount:.2f} ({percentage:.1f}%)\n"
                stats_text += "\n"
        else:
            stats_text += "Нет данных о расходах\n\n"
        
        # Добавляем рекомендации
        stats_text += "💡 Рекомендации:\n"
        if recommendations:
            for i, rec in enumerate(recommendations[:3], 1):  # Ограничиваем 3 рекомендациями
                stats_text += f"{i}. {rec}\n"
        else:
            stats_text += "Пока нет данных для анализа\n"
        
        # Отображаем текст
        ax.text(0.05, 0.95, stats_text, transform=ax.transAxes,
                fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                family='monospace')
        
        return fig
    
    # --- МЕТОДЫ ДЛЯ АНАЛИЗА ВСЕХ ПУТЕШЕСТВИЙ ---
    
    def get_all_trips_summary(self) -> Dict[str, Any]:
        """Получение сводной статистики по всем путешествиям."""
        if self.df_trips.empty:
            return {}
        
        summary = {
            'total_trips': len(self.df_trips),
            'completed_trips': len(self.df_trips[self.df_trips['status'] == 'Завершено']),
            'in_progress_trips': len(self.df_trips[self.df_trips['status'] == 'В процессе']),
            'planned_trips': len(self.df_trips[self.df_trips['status'] == 'Запланировано']),
            'total_budget': self.df_trips['budget'].sum(),
            'total_actual_spent': self.df_trips['actual_spent'].sum(),
            'total_expenses': len(self.df_expenses),
            'avg_budget_per_trip': self.df_trips['budget'].mean() if len(self.df_trips) > 0 else 0,
            'avg_spent_per_trip': self.df_trips['actual_spent'].mean() if len(self.df_trips) > 0 else 0,
            'trips_by_status': self.df_trips['status'].value_counts().to_dict(),
            'trips_by_currency': self.df_trips['currency'].value_counts().to_dict()
        }
        
        # Анализ расходов по всем путешествиям
        if not self.df_expenses.empty:
            summary['total_expenses_amount'] = self.df_expenses['amount'].sum()
            summary['avg_expense_amount'] = self.df_expenses['amount'].mean()
            summary['expenses_by_category'] = self.df_expenses.groupby('category')['amount'].sum().to_dict()
            summary['expenses_by_payment_method'] = self.df_expenses['payment_method'].value_counts().to_dict()
            
            # Топ-5 самых дорогих путешествий
            expensive_trips = self.df_trips.nlargest(5, 'actual_spent')[['name', 'actual_spent', 'currency']]
            summary['most_expensive_trips'] = expensive_trips.to_dict('records')
            
            # Топ-5 самых экономных путешествий (с наименьшими расходами)
            economical_trips = self.df_trips[self.df_trips['actual_spent'] > 0].nsmallest(5, 'actual_spent')[['name', 'actual_spent', 'currency']]
            summary['most_economical_trips'] = economical_trips.to_dict('records')
        
        return summary
    
    def plot_all_trips_budget_comparison(self, ax=None) -> plt.Figure:
        """
        Сравнение бюджетов и фактических расходов по всем путешествиям.
        Возвращает объект Figure для встраивания в Tkinter.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        else:
            fig = ax.get_figure()
        
        if self.df_trips.empty:
            ax.text(0.5, 0.5, 'Нет данных о путешествиях\nдля построения графика', 
                   ha='center', va='center', fontsize=12)
            ax.set_title('Сравнение бюджетов по всем путешествиям')
            return fig
        
        # Сортируем по названию для лучшей читаемости
        df_sorted = self.df_trips.sort_values('name')
        
        # Создаем группированный столбчатый график
        x = np.arange(len(df_sorted))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, df_sorted['budget'], width, 
                      label='Бюджет', color='lightblue', edgecolor='black')
        bars2 = ax.bar(x + width/2, df_sorted['actual_spent'], width, 
                      label='Фактические расходы', color='lightcoral', edgecolor='black')
        
        # Настройка внешнего вида
        ax.set_xlabel('Путешествия', fontsize=11)
        ax.set_ylabel('Сумма', fontsize=11)
        ax.set_title('Сравнение бюджетов и фактических расходов\nпо всем путешествиям', 
                    fontsize=12, pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(df_sorted['name'], rotation=45, ha='right', fontsize=9)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Добавляем значения на столбцы для крупных сумм
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > df_sorted['budget'].max() * 0.05:  # Добавляем только если достаточно большой
                    ax.text(bar.get_x() + bar.get_width()/2, height,
                           f'{height:,.0f}', ha='center', va='bottom', fontsize=8)
        
        fig.tight_layout()
        return fig
    
    def plot_all_trips_expenses_by_category(self, ax=None) -> plt.Figure:
        """
        Распределение расходов по категориям по всем путешествиям.
        Возвращает объект Figure для встраивания в Tkinter.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 6))
        else:
            fig = ax.get_figure()
        
        if self.df_expenses.empty:
            ax.text(0.5, 0.5, 'Нет данных о расходах\nдля построения графика', 
                   ha='center', va='center', fontsize=12)
            ax.set_title('Распределение расходов по категориям (все путешествия)')
            return fig
        
        # Группируем расходы по категориям
        category_totals = self.df_expenses.groupby('category')['amount'].sum().sort_values(ascending=False)
        
        # Создаем горизонтальную столбчатую диаграмму
        colors = plt.cm.Set3(np.linspace(0, 1, len(category_totals)))
        bars = ax.barh(range(len(category_totals)), category_totals.values, color=colors)
        
        # Настройка внешнего вида
        ax.set_yticks(range(len(category_totals)))
        ax.set_yticklabels(category_totals.index, fontsize=10)
        ax.set_xlabel('Сумма расходов', fontsize=11)
        ax.set_title('Распределение расходов по категориям\nпо всем путешествиям', 
                    fontsize=12, pad=15)
        ax.grid(True, alpha=0.3, axis='x')
        
        # Добавляем значения на столбцы
        for i, (bar, value) in enumerate(zip(bars, category_totals.values)):
            ax.text(value + max(category_totals.values) * 0.01, bar.get_y() + bar.get_height()/2,
                   f'{value:,.2f}', ha='left', va='center', fontsize=9)
        
        fig.tight_layout()
        return fig
    
    def plot_trips_by_status(self, ax=None) -> plt.Figure:
        """
        Круговая диаграмма распределения путешествий по статусам.
        Возвращает объект Figure для встраивания в Tkinter.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 6))
        else:
            fig = ax.get_figure()
        
        if self.df_trips.empty:
            ax.text(0.5, 0.5, 'Нет данных о путешествиях\nдля построения графика', 
                   ha='center', va='center', fontsize=12)
            ax.set_title('Распределение путешествий по статусам')
            return fig
        
        status_counts = self.df_trips['status'].value_counts()
        
        # Цвета для разных статусов
        status_colors = {
            'Завершено': '#4CAF50',  # Зеленый
            'В процессе': '#2196F3',  # Синий
            'Запланировано': '#FF9800',  # Оранжевый
            'Отменено': '#F44336'  # Красный
        }
        
        colors = [status_colors.get(status, '#9E9E9E') for status in status_counts.index]
        
        wedges, texts, autotexts = ax.pie(
            status_counts.values, 
            labels=status_counts.index, 
            autopct='%1.1f%%', 
            colors=colors, 
            startangle=90,
            explode=[0.05] * len(status_counts)  # Немного разделяем секторы
        )
        
        # Улучшаем читаемость текста
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
        
        for text in texts:
            text.set_fontsize(11)
        
        ax.set_title(f'Распределение путешествий по статусам\nВсего: {len(self.df_trips)}', 
                    fontsize=12, pad=20)
        
        return fig
    
    def plot_monthly_expenses_trend(self, ax=None) -> plt.Figure:
        """
        Тренд расходов по месяцам (для всех путешествий).
        Возвращает объект Figure для встраивания в Tkinter.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 5))
        else:
            fig = ax.get_figure()
        
        if self.df_expenses.empty:
            ax.text(0.5, 0.5, 'Нет данных о расходах\nдля построения графика', 
                   ha='center', va='center', fontsize=12)
            ax.set_title('Тренд расходов по месяцам')
            return fig
        
        # Преобразуем даты и извлекаем месяц и год
        df_expenses_copy = self.df_expenses.copy()
        df_expenses_copy['date'] = pd.to_datetime(df_expenses_copy['date'])
        df_expenses_copy['year_month'] = df_expenses_copy['date'].dt.to_period('M')
        
        # Группируем по месяцу
        monthly_expenses = df_expenses_copy.groupby('year_month')['amount'].sum().reset_index()
        monthly_expenses['year_month_str'] = monthly_expenses['year_month'].astype(str)
        
        # Сортируем по дате
        monthly_expenses = monthly_expenses.sort_values('year_month')
        
        # Создаем график
        ax.plot(monthly_expenses['year_month_str'], monthly_expenses['amount'], 
               marker='o', linewidth=2, markersize=8, color='darkorange')
        
        # Заполняем область под графиком
        ax.fill_between(monthly_expenses['year_month_str'], monthly_expenses['amount'], 
                       alpha=0.3, color='darkorange')
        
        # Настройка внешнего вида
        ax.set_title('Тренд расходов по месяцам\n(по всем путешествиям)', 
                    fontsize=12, pad=15)
        ax.set_xlabel('Месяц и год', fontsize=11)
        ax.set_ylabel('Сумма расходов', fontsize=11)
        ax.grid(True, alpha=0.3)
        
        # Поворачиваем подписи дат
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=9)
        plt.setp(ax.get_yticklabels(), fontsize=9)
        
        # Добавляем значения в точках
        for x, y in zip(monthly_expenses['year_month_str'], monthly_expenses['amount']):
            ax.text(x, y, f'{y:,.0f}', ha='center', va='bottom', fontsize=8)
        
        fig.tight_layout()
        return fig
    
    def export_all_trips_to_csv(self, output_file: str = "all_trips_summary.csv") -> str:
        """Экспорт сводной статистики по всем путешествиям в CSV."""
        try:
            # Создаем сводную таблицу
            summary_data = []
            
            for _, trip in self.df_trips.iterrows():
                trip_expenses = self.df_expenses[self.df_expenses['trip_id'] == trip['id']]
                expenses_by_category = trip_expenses.groupby('category')['amount'].sum().to_dict()
                
                # Формируем строку для каждого путешествия
                row = {
                    'id': trip['id'],
                    'name': trip['name'],
                    'destination': trip['destination'],
                    'start_date': trip['start_date'],
                    'end_date': trip['end_date'],
                    'duration_days': trip['duration_days'],
                    'budget': trip['budget'],
                    'actual_spent': trip['actual_spent'],
                    'budget_balance': trip['budget_balance'],
                    'currency': trip['currency'],
                    'status': trip['status'],
                    'expense_count': len(trip_expenses),
                    'avg_daily_expense': trip['actual_spent'] / trip['duration_days'] if trip['duration_days'] > 0 else 0
                }
                
                # Добавляем расходы по категориям
                for category in ExpenseCategory:
                    row[f'category_{category.value}'] = expenses_by_category.get(category.value, 0)
                
                summary_data.append(row)
            
            # Создаем DataFrame и экспортируем в CSV
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            return output_file
            
        except Exception as e:
            print(f"Ошибка при экспорте всех путешествий в CSV: {e}")
            return ""
    
    def export_all_trips_to_json(self, output_file: str = "all_trips_data.json") -> str:
        """Экспорт всех данных о путешествиях и расходах в JSON."""
        try:
            # Подготавливаем данные для экспорта
            export_data = {
                'export_date': datetime.now().isoformat(),
                'total_trips': len(self.df_trips),
                'total_expenses': len(self.df_expenses),
                'summary': self.get_all_trips_summary(),
                'trips': [],
                'aggregated_data': {
                    'expenses_by_category': self.df_expenses.groupby('category')['amount'].sum().to_dict(),
                    'expenses_by_month': self._get_expenses_by_month(),
                    'trips_by_status': self.df_trips['status'].value_counts().to_dict()
                }
            }
            
            # Добавляем данные по каждому путешествию
            for _, trip in self.df_trips.iterrows():
                trip_data = trip.to_dict()
                trip_expenses = self.df_expenses[self.df_expenses['trip_id'] == trip['id']]
                
                trip_data['expenses'] = trip_expenses.to_dict('records')
                trip_data['expenses_summary'] = self.get_trip_expense_summary(trip['id'])
                
                export_data['trips'].append(trip_data)
            
            # Сохраняем в JSON файл
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            
            return output_file
            
        except Exception as e:
            print(f"Ошибка при экспорте всех путешествий в JSON: {e}")
            return ""
    
    def _get_expenses_by_month(self) -> Dict[str, float]:
        """Получение расходов по месяцам."""
        if self.df_expenses.empty:
            return {}
        
        df_copy = self.df_expenses.copy()
        df_copy['date'] = pd.to_datetime(df_copy['date'])
        df_copy['year_month'] = df_copy['date'].dt.strftime('%Y-%m')
        
        return df_copy.groupby('year_month')['amount'].sum().to_dict()
    
    def generate_all_trips_report(self, output_file: str = "all_trips_report.csv"):
        """Генерация полного отчёта по всем путешествиям в CSV."""
        return self.export_all_trips_to_csv(output_file)
    
    def plot_all_analytics(self, trip_id: int) -> Dict[str, plt.Figure]:
        """
        Создание всех графиков аналитики для указанного путешествия.
        Возвращает словарь с объектами Figure.
        """
        figures = {}
        
        # Создаем 4 графика
        fig1, ax1 = plt.subplots(figsize=(6, 5))
        self.plot_expense_categories(trip_id, ax1)
        figures['categories'] = fig1
        
        fig2, ax2 = plt.subplots(figsize=(6, 5))
        self.plot_daily_expenses(trip_id, ax2)
        figures['daily'] = fig2
        
        fig3, ax3 = plt.subplots(figsize=(6, 5))
        self.plot_budget_vs_actual(trip_id, ax3)
        figures['budget'] = fig3
        
        fig4, ax4 = plt.subplots(figsize=(6, 5))
        self.plot_expense_statistics(trip_id, ax4)
        figures['stats'] = fig4
        
        return figures
    
    def plot_all_trips_analytics(self) -> Dict[str, plt.Figure]:
        """
        Создание всех графиков аналитики для всех путешествий.
        Возвращает словарь с объектами Figure.
        """
        figures = {}
        
        # Создаем 4 графика
        fig1, ax1 = plt.subplots(figsize=(8, 6))
        self.plot_all_trips_budget_comparison(ax1)
        figures['all_budget_comparison'] = fig1
        
        fig2, ax2 = plt.subplots(figsize=(8, 6))
        self.plot_all_trips_expenses_by_category(ax2)
        figures['all_expenses_by_category'] = fig2
        
        fig3, ax3 = plt.subplots(figsize=(6, 6))
        self.plot_trips_by_status(ax3)
        figures['trips_by_status'] = fig3
        
        fig4, ax4 = plt.subplots(figsize=(10, 5))
        self.plot_monthly_expenses_trend(ax4)
        figures['monthly_trend'] = fig4
        
        return figures
    
    def generate_expense_report(self, trip_id: int, output_file: str = "expense_report.csv"):
        """Генерация отчёта по расходам в CSV."""
        trip_expenses = self.df_expenses[self.df_expenses['trip_id'] == trip_id]
        
        if trip_expenses.empty:
            print("Нет данных о расходах для генерации отчёта")
            return None
        
        # Группировка по категориям
        category_report = trip_expenses.groupby('category').agg({
            'amount': ['sum', 'count', 'mean', 'max']
        }).round(2)
        
        category_report.columns = ['total', 'count', 'average', 'max']
        category_report = category_report.sort_values('total', ascending=False)
        
        # Экспорт в CSV
        category_report.to_csv(output_file, encoding='utf-8-sig')
        print(f"Отчёт сохранён в {output_file}")
        
        return category_report
    
    def get_trip_recommendations(self, trip_id: int) -> List[str]:
        """Генерация рекомендаций на основе анализа расходов."""
        recommendations = []
        summary = self.get_trip_expense_summary(trip_id)
        
        if not summary or summary.get('expense_count', 0) == 0:
            return ["Пока нет данных о расходах для анализа"]
        
        # Анализ по категориям
        by_category = summary['by_category']
        total = summary['total']
        
        if total > 0:
            # Проверяем, не превышает ли какая-то категория 50% всех расходов
            for category, amount in by_category.items():
                percentage = (amount / total) * 100
                if percentage > 50:
                    recommendations.append(
                        f"Категория '{category}' составляет {percentage:.1f}% всех расходов. "
                        f"Рассмотрите возможность сокращения расходов в этой категории."
                    )
            
            # Рекомендации по дневным расходам
            daily_avg = summary['daily_avg']
            if daily_avg > 200:  # Пример порога
                recommendations.append(
                    f"Средние дневные расходы составляют {daily_avg:.2f}. "
                    f"Это довольно высокий показатель. Попробуйте найти способы экономии."
                )
            elif daily_avg < 50:
                recommendations.append(
                    f"Отличная экономия! Средние дневные расходы всего {daily_avg:.2f}. "
                    f"Продолжайте в том же духе!"
                )
        
        # Если рекомендаций нет, добавляем положительный отзыв
        if not recommendations:
            recommendations.append(
                "Ваши расходы распределены сбалансированно. Продолжайте в том же духе!"
            )
        
        # Ограничиваем количество рекомендаций
        return recommendations[:5]