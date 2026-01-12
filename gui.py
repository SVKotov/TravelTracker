"""
Модуль gui.py
Графический интерфейс приложения TravelTracker на Tkinter.
Обновленная версия с встроенными графиками аналитики и анализом всех путешествий.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import os
import sys
import re

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Trip, Expense, ExpenseCategory, TripStatus
from storage import TravelStorage
from analysis import TravelAnalyzer
from utils import validate_date_range, validate_currency_amount


class TravelTrackerApp:
    """Основной класс графического интерфейса приложения TravelTracker."""

    def __init__(self, root):
        self.root = root
        self.root.title("TravelTracker - Планировщик путешествий")
        self.root.geometry("1200x800")
        
        # Инициализация хранилища
        self.storage = TravelStorage()
        
        # Текущие данные
        self.current_trips = []
        self.current_trip = None
        self.current_expenses = []
        
        # Создание виджетов
        self._setup_ui()
        self._load_trips()
        
        # Установка стилей
        self._setup_styles()
    
    def _setup_styles(self):
        """Настройка стилей для виджетов."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Настройка цветов
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('Treeview', font=('Segoe UI', 10))
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
        
        # Акцентная кнопка
        style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'))
    
    def _setup_ui(self):
        """Настройка пользовательского интерфейса."""
        # Создаем Notebook для вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Вкладка 1: Путешествия
        self.trips_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.trips_frame, text='🗺️ Путешествия')
        self._setup_trips_tab()
        
        # Вкладка 2: Расходы
        self.expenses_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.expenses_frame, text='💰 Расходы')
        self._setup_expenses_tab()
        
        # Вкладка 3: Аналитика
        self.analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analytics_frame, text='📊 Аналитика')
        self._setup_analytics_tab()
        
        # Вкладка 4: Экспорт
        self.export_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.export_frame, text='📤 Экспорт')
        self._setup_export_tab()
    
    def _setup_trips_tab(self):
        """Настройка вкладки путешествий."""
        # Левая панель: Список путешествий
        list_frame = ttk.LabelFrame(self.trips_frame, text="Мои путешествия", padding="10")
        list_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Treeview для отображения путешествий
        columns = ("ID", "Название", "Направление", "Даты", "Бюджет", "Статус")
        self.trips_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        # Настройка колонок
        col_widths = [50, 200, 150, 150, 100, 100]
        for col, width in zip(columns, col_widths):
            self.trips_tree.heading(col, text=col)
            self.trips_tree.column(col, width=width)
        
        # Скроллбар
        trips_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.trips_tree.yview)
        self.trips_tree.configure(yscrollcommand=trips_scrollbar.set)
        
        self.trips_tree.grid(row=0, column=0, sticky='nsew')
        trips_scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Настройка веса строки для Treeview
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Кнопки управления списком
        trips_buttons = ttk.Frame(list_frame)
        trips_buttons.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(trips_buttons, text="Обновить", 
                  command=self._load_trips).pack(side='left', padx=5)
        ttk.Button(trips_buttons, text="Удалить", 
                  command=self._delete_trip).pack(side='left', padx=5)
        
        # Правая панель: Форма добавления/редактирования
        form_frame = ttk.LabelFrame(self.trips_frame, text="Добавить/Редактировать путешествие", padding="10")
        form_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Поля формы
        self.trip_form_vars = {}
        fields = [
            ("Название:", "name", "entry"),
            ("Направление:", "destination", "entry"),
            ("Дата начала (ГГГГ-ММ-ДД):", "start_date", "entry"),
            ("Дата окончания (ГГГГ-ММ-ДД):", "end_date", "entry"),
            ("Бюджет:", "budget", "entry"),
            ("Валюта:", "currency", "combobox"),
            ("Статус:", "status", "combobox"),
            ("Участники (через запятую):", "participants", "entry"),
            ("Описание:", "description", "text")
        ]
        
        for i, (label, field, field_type) in enumerate(fields):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, sticky='w', pady=5)
            
            if field_type == "entry":
                var = tk.StringVar()
                entry = ttk.Entry(form_frame, textvariable=var, width=40)
                entry.grid(row=i, column=1, pady=5, padx=(10, 0))
                self.trip_form_vars[field] = var
            
            elif field_type == "combobox":
                var = tk.StringVar()
                if field == "currency":
                    values = ["USD", "EUR", "RUB", "GBP", "JPY", "KRW", "AED", "CNY"]
                elif field == "status":
                    values = [status.value for status in TripStatus]
                else:
                    values = []
                
                combobox = ttk.Combobox(form_frame, textvariable=var, 
                                       values=values, width=37, state='readonly')
                combobox.grid(row=i, column=1, pady=5, padx=(10, 0))
                self.trip_form_vars[field] = var
                
                # Установка значений по умолчанию
                if field == "currency":
                    var.set("USD")
                elif field == "status":
                    var.set(TripStatus.PLANNED.value)
            
            elif field_type == "text":
                text_widget = tk.Text(form_frame, height=4, width=40)
                text_widget.grid(row=i, column=1, pady=5, padx=(10, 0))
                self.trip_form_vars[field] = text_widget
        
        # Кнопки формы
        form_buttons = ttk.Frame(form_frame)
        form_buttons.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        ttk.Button(form_buttons, text="Добавить", 
                  command=self._add_trip, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(form_buttons, text="Обновить", 
                  command=self._update_trip).pack(side='left', padx=5)
        ttk.Button(form_buttons, text="Очистить", 
                  command=self._clear_trip_form).pack(side='left', padx=5)
        
        # Событие выбора в Treeview
        self.trips_tree.bind('<<TreeviewSelect>>', self._on_trip_select)
    
    def _setup_expenses_tab(self):
        """Настройка вкладки расходов."""
        # Верхняя панель: Выбор путешествия
        trip_select_frame = ttk.Frame(self.expenses_frame)
        trip_select_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(trip_select_frame, text="Выберите путешествие:").pack(side='left')
        self.selected_trip_var = tk.StringVar()
        self.trip_combobox = ttk.Combobox(trip_select_frame, 
                                         textvariable=self.selected_trip_var,
                                         width=50, state='readonly')
        self.trip_combobox.pack(side='left', padx=10)
        self.trip_combobox.bind('<<ComboboxSelected>>', self._on_trip_combobox_select)
        
        # Основная часть с двумя колонками
        main_expenses_frame = ttk.Frame(self.expenses_frame)
        main_expenses_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Левая колонка: Форма добавления расхода
        expense_form_frame = ttk.LabelFrame(main_expenses_frame, 
                                           text="Добавить расход", padding="10")
        expense_form_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        self.expense_form_vars = {}
        expense_fields = [
            ("Сумма:", "amount", "entry"),
            ("Валюта:", "currency", "combobox"),
            ("Категория:", "category", "combobox"),
            ("Дата (ГГГГ-ММ-ДД):", "date", "entry"),
            ("Способ оплаты:", "payment_method", "combobox"),
            ("Место:", "location", "entry"),
            ("Описание:", "description", "text")
        ]
        
        for i, (label, field, field_type) in enumerate(expense_fields):
            ttk.Label(expense_form_frame, text=label).grid(row=i, column=0, 
                                                          sticky='w', pady=5)
            
            if field_type == "entry":
                var = tk.StringVar()
                entry = ttk.Entry(expense_form_frame, textvariable=var, width=40)
                entry.grid(row=i, column=1, pady=5, padx=(10, 0))
                self.expense_form_vars[field] = var
            
            elif field_type == "combobox":
                var = tk.StringVar()
                if field == "currency":
                    values = ["USD", "EUR", "RUB", "GBP", "KRW", "AED", "CNY"]
                elif field == "category":
                    values = [cat.value for cat in ExpenseCategory]
                elif field == "payment_method":
                    values = ["Наличные", "Кредитная карта", "Дебетовая карта", 
                             "Мобильный платеж", "Другое"]
                else:
                    values = []
                
                combobox = ttk.Combobox(expense_form_frame, textvariable=var,
                                       values=values, width=37)
                combobox.grid(row=i, column=1, pady=5, padx=(10, 0))
                self.expense_form_vars[field] = var
                
                # Установка значений по умолчанию
                if field == "currency":
                    var.set("USD")
                elif field == "category":
                    var.set(ExpenseCategory.FOOD.value)
                elif field == "payment_method":
                    var.set("Наличные")
            
            elif field_type == "text":
                text_widget = tk.Text(expense_form_frame, height=3, width=40)
                text_widget.grid(row=i, column=1, pady=5, padx=(10, 0))
                self.expense_form_vars[field] = text_widget
        
        # Кнопки формы расходов
        expense_buttons = ttk.Frame(expense_form_frame)
        expense_buttons.grid(row=len(expense_fields), column=0, 
                            columnspan=2, pady=20)
        
        ttk.Button(expense_buttons, text="Добавить расход",
                  command=self._add_expense, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(expense_buttons, text="Очистить форму",
                  command=self._clear_expense_form).pack(side='left', padx=5)
        
        # Правая колонка: Список расходов
        expenses_list_frame = ttk.LabelFrame(main_expenses_frame,
                                           text="Расходы выбранного путешествия",
                                           padding="10")
        expenses_list_frame.pack(side='right', fill='both', expand=True, 
                                padx=(5, 0))
        
        # Treeview для расходов
        columns = ("ID", "Дата", "Категория", "Сумма", "Валюта", "Место", "Описание")
        self.expenses_tree = ttk.Treeview(expenses_list_frame, columns=columns,
                                         show="headings", height=15)
        
        col_widths = [50, 100, 120, 80, 60, 120, 150]
        for col, width in zip(columns, col_widths):
            self.expenses_tree.heading(col, text=col)
            self.expenses_tree.column(col, width=width)
        
        # Скроллбар
        expenses_scrollbar = ttk.Scrollbar(expenses_list_frame,
                                          orient='vertical',
                                          command=self.expenses_tree.yview)
        self.expenses_tree.configure(yscrollcommand=expenses_scrollbar.set)
        
        self.expenses_tree.grid(row=0, column=0, sticky='nsew')
        expenses_scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Настройка веса для Treeview
        expenses_list_frame.grid_rowconfigure(0, weight=1)
        expenses_list_frame.grid_columnconfigure(0, weight=1)
        
        # Кнопки управления расходами
        expense_list_buttons = ttk.Frame(expenses_list_frame)
        expense_list_buttons.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(expense_list_buttons, text="Обновить список",
                  command=self._load_expenses).pack(side='left', padx=5)
        ttk.Button(expense_list_buttons, text="Удалить выбранный",
                  command=self._delete_expense).pack(side='left', padx=5)
    
    def _setup_analytics_tab(self):
        """Настройка вкладки аналитики."""
        # Верхняя панель: Выбор путешествия для анализа
        analytics_top_frame = ttk.Frame(self.analytics_frame)
        analytics_top_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(analytics_top_frame, 
                 text="Выберите путешествие для анализа:").pack(side='left')
        
        self.analytics_trip_var = tk.StringVar()
        
        # Создаем Combobox сначала
        self.analytics_trip_combobox = ttk.Combobox(analytics_top_frame,
                                                   textvariable=self.analytics_trip_var,
                                                   width=50, state='readonly')
        self.analytics_trip_combobox.pack(side='left', padx=10)
        
        # ТОЛЬКО ПОСЛЕ создания combobox обновляем его значения
        self._update_analytics_combobox()
        
        ttk.Button(analytics_top_frame, text="Обновить графики",
                  command=self._update_analytics,
                  style='Accent.TButton').pack(side='left', padx=5)
        
        ttk.Button(analytics_top_frame, text="Очистить",
                  command=self._clear_analytics).pack(side='left', padx=5)
        
        # Основная область для графиков
        self.analytics_canvas_frame = ttk.Frame(self.analytics_frame)
        self.analytics_canvas_frame.pack(fill='both', expand=True, 
                                        padx=10, pady=(0, 10))
        
        # Изначально показываем инструкцию
        self._show_analytics_instructions()
    
    def _update_analytics_combobox(self):
        """Обновление Combobox для аналитики, включая 'Все путешествия'."""
        trip_names = ["Все путешествия"] + [f"{trip.id}: {trip.name} ({trip.destination})" 
                     for trip in self.current_trips]
        
        self.analytics_trip_combobox['values'] = trip_names
        if trip_names:
            self.analytics_trip_combobox.current(0)
    
    def _show_analytics_instructions(self):
        """Показать инструкцию перед отображением графиков."""
        for widget in self.analytics_canvas_frame.winfo_children():
            widget.destroy()
        
        instruction_frame = ttk.Frame(self.analytics_canvas_frame)
        instruction_frame.pack(expand=True, fill='both')
        
        # Центрируем содержимое
        instruction_frame.grid_rowconfigure(0, weight=1)
        instruction_frame.grid_rowconfigure(3, weight=1)
        instruction_frame.grid_columnconfigure(0, weight=1)
        instruction_frame.grid_columnconfigure(2, weight=1)
        
        ttk.Label(instruction_frame, 
                 text="📊 Аналитика путешествий",
                 font=('Segoe UI', 16, 'bold')).grid(row=1, column=1, pady=(0, 20))
        
        instructions = (
            "Для отображения графиков аналитики:\n\n"
            "1. Выберите путешествие из списка выше\n"
            "2. Нажмите кнопку 'Обновить графики'\n\n"
            "Будут показаны 4 графика:\n"
            "• 📈 Распределение расходов по категориям\n"
            "• 📅 Ежедневные расходы\n"
            "• 💰 Сравнение бюджета с фактическими расходами\n"
            "• 📋 Статистика и рекомендации\n\n"
            "Каждый график имеет панель инструментов для:\n"
            "• Масштабирования и панорамирования\n"
            "• Сохранения изображения\n"
            "• Возврата к исходному виду"
        )
        
        ttk.Label(instruction_frame,
                 text=instructions,
                 font=('Segoe UI', 11),
                 justify='center').grid(row=2, column=1, pady=10)
    
    def _clear_analytics(self):
        """Очистка графиков аналитики."""
        # Закрываем все фигуры matplotlib для освобождения памяти
        plt.close('all')
        
        for widget in self.analytics_canvas_frame.winfo_children():
            widget.destroy()
        
        self._show_analytics_instructions()
    
    def _setup_export_tab(self):
        """Настройка вкладки экспорта."""
        export_frame = ttk.Frame(self.export_frame)
        export_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Выбор путешествия для экспорта
        ttk.Label(export_frame, text="Выберите путешествие для экспорта:",
                 font=('Segoe UI', 11, 'bold')).pack(pady=(0, 10))
        
        self.export_trip_var = tk.StringVar()
        
        # Обновляем Combobox, чтобы включить "Все путешествия"
        export_trip_names = ["Все путешествия"] + [f"{trip.id}: {trip.name} ({trip.destination})" 
                          for trip in self.current_trips]
        self.export_trip_combobox = ttk.Combobox(export_frame,
                                                textvariable=self.export_trip_var,
                                                values=export_trip_names,
                                                width=60, state='readonly')
        if export_trip_names:
            self.export_trip_combobox.current(0)
        self.export_trip_combobox.pack(pady=(0, 20))
        
        # Опции экспорта
        options_frame = ttk.LabelFrame(export_frame, text="Опции экспорта", padding="15")
        options_frame.pack(fill='x', pady=10)
        
        self.export_format_var = tk.StringVar(value="JSON")
        
        ttk.Radiobutton(options_frame, text="JSON формат (полные данные)", 
                       variable=self.export_format_var, value="JSON").pack(anchor='w', pady=5)
        ttk.Radiobutton(options_frame, text="CSV формат (табличные данные)", 
                       variable=self.export_format_var, value="CSV").pack(anchor='w', pady=5)
        
        # Дополнительные опции
        ttk.Checkbutton(options_frame, text="Включить сводную статистику",
                       variable=tk.BooleanVar(value=True)).pack(anchor='w', pady=5)
        ttk.Checkbutton(options_frame, text="Включить графики (если возможно)",
                       variable=tk.BooleanVar(value=False)).pack(anchor='w', pady=5)
        
        # Кнопки экспорта
        buttons_frame = ttk.Frame(export_frame)
        buttons_frame.pack(pady=20)
        
        ttk.Button(buttons_frame, text="📤 Экспортировать данные",
                  command=self._export_data, width=30,
                  style='Accent.TButton').pack(pady=10)
        
        ttk.Button(buttons_frame, text="📊 Экспорт сводного отчета (CSV)",
                  command=self._export_summary_report, width=30).pack(pady=10)
        
        ttk.Button(buttons_frame, text="📁 Экспорт всех данных (JSON)",
                  command=self._export_all_data_json, width=30).pack(pady=10)
        
        ttk.Button(buttons_frame, text="📂 Открыть папку с данными",
                  command=self._open_data_folder, width=30).pack(pady=10)
        
        # Статус экспорта
        self.export_status_label = ttk.Label(export_frame, text="", font=('Segoe UI', 9))
        self.export_status_label.pack(pady=10)
    
    # --- Методы работы с данными ---
    
    def _load_trips(self):
        """Загрузка списка путешествий."""
        try:
            # Очищаем Treeview
            for item in self.trips_tree.get_children():
                self.trips_tree.delete(item)
            
            # Загружаем данные
            self.current_trips = self.storage.get_all_trips()
            
            # Заполняем Treeview
            for trip in self.current_trips:
                date_range = f"{trip.start_date} - {trip.end_date}" if trip.start_date and trip.end_date else "Не указано"
                
                # Форматируем бюджет
                budget_text = f"{trip.budget:.2f} {trip.currency}"
                if len(budget_text) > 15:
                    budget_text = f"{trip.budget:,.0f} {trip.currency}"
                
                # Иконка статуса
                status_icons = {
                    TripStatus.PLANNED: "📅",
                    TripStatus.IN_PROGRESS: "🔄",
                    TripStatus.COMPLETED: "✅",
                    TripStatus.CANCELLED: "❌"
                }
                status_text = f"{status_icons.get(trip.status, '')} {trip.status.value}"
                
                self.trips_tree.insert('', 'end', values=(
                    trip.id,
                    trip.name,
                    trip.destination,
                    date_range,
                    budget_text,
                    status_text
                ))
            
            # Обновляем все Combobox'ы с "Все путешествия"
            self._update_all_comboboxes()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить путешествия: {e}")
    
    def _update_all_comboboxes(self):
        """Обновление всех Combobox с путешествиями, включая 'Все путешествия'."""
        # Общие значения для всех Combobox
        all_trips_option = ["Все путешествия"]
        trip_names = [f"{trip.id}: {trip.name} ({trip.destination})" 
                     for trip in self.current_trips]
        all_values = all_trips_option + trip_names
        
        # Обновляем все combobox'ы
        comboboxes = [
            (self.trip_combobox, 0),  # Для выбора путешествия в расходах
            (self.analytics_trip_combobox, 0),  # Для аналитики
            (self.export_trip_combobox, 0)  # Для экспорта
        ]
        
        for combobox, default_index in comboboxes:
            if combobox:  # Проверяем, что combobox существует
                combobox['values'] = all_values
                if all_values:
                    combobox.current(default_index)
    
    def _on_trip_select(self, event):
        """Обработка выбора путешествия в Treeview."""
        selection = self.trips_tree.selection()
        if not selection:
            return
        
        item = self.trips_tree.item(selection[0])
        trip_id = item['values'][0]
        
        # Находим выбранное путешествие
        for trip in self.current_trips:
            if trip.id == trip_id:
                self.current_trip = trip
                self._fill_trip_form(trip)
                break
    
    def _fill_trip_form(self, trip: Trip):
        """Заполнение формы данными выбранного путешествия."""
        # Заполняем поля формы
        self.trip_form_vars['name'].set(trip.name)
        self.trip_form_vars['destination'].set(trip.destination)
        self.trip_form_vars['start_date'].set(str(trip.start_date) if trip.start_date else "")
        self.trip_form_vars['end_date'].set(str(trip.end_date) if trip.end_date else "")
        self.trip_form_vars['budget'].set(str(trip.budget))
        self.trip_form_vars['currency'].set(trip.currency)
        self.trip_form_vars['status'].set(trip.status.value)
        self.trip_form_vars['participants'].set(trip.participants)
        
        # Очищаем и заполняем текстовое поле описания
        description_widget = self.trip_form_vars['description']
        description_widget.delete('1.0', tk.END)
        description_widget.insert('1.0', trip.description or "")
    
    def _add_trip(self):
        """Добавление нового путешествия."""
        try:
            # Валидация данных
            name = self.trip_form_vars['name'].get().strip()
            if not name:
                messagebox.showwarning("Внимание", "Введите название путешествия")
                return
            
            # Проверка дат
            start_date_str = self.trip_form_vars['start_date'].get()
            end_date_str = self.trip_form_vars['end_date'].get()
            
            if start_date_str and end_date_str:
                success, message = validate_date_range(start_date_str, end_date_str)
                if not success:
                    messagebox.showwarning("Внимание", message)
                    return
            
            # Проверка бюджета
            budget_str = self.trip_form_vars['budget'].get()
            if budget_str:
                success, budget, message = validate_currency_amount(budget_str)
                if not success:
                    messagebox.showwarning("Внимание", message)
                    return
            else:
                budget = 0.0
            
            # Создание объекта Trip
            trip = Trip(
                name=name,
                destination=self.trip_form_vars['destination'].get(),
                start_date=date.fromisoformat(start_date_str) if start_date_str else None,
                end_date=date.fromisoformat(end_date_str) if end_date_str else None,
                budget=budget,
                currency=self.trip_form_vars['currency'].get(),
                status=TripStatus(self.trip_form_vars['status'].get()),
                participants=self.trip_form_vars['participants'].get(),
                description=self.trip_form_vars['description'].get('1.0', tk.END).strip()
            )
            
            # Сохранение в БД
            trip_id = self.storage.add_trip(trip)
            if trip_id > 0:
                messagebox.showinfo("Успех", "Путешествие успешно добавлено!")
                self._clear_trip_form()
                self._load_trips()
            else:
                messagebox.showerror("Ошибка", "Не удалось добавить путешествие")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при добавлении путешествия: {e}")
    
    def _update_trip(self):
        """Обновление выбранного путешествия."""
        if not self.current_trip:
            messagebox.showwarning("Внимание", "Выберите путешествие для редактирования")
            return
        
        try:
            # Обновление данных
            self.current_trip.name = self.trip_form_vars['name'].get().strip()
            self.current_trip.destination = self.trip_form_vars['destination'].get()
            
            # Обновление дат
            start_date_str = self.trip_form_vars['start_date'].get()
            end_date_str = self.trip_form_vars['end_date'].get()
            if start_date_str:
                self.current_trip.start_date = date.fromisoformat(start_date_str)
            else:
                self.current_trip.start_date = None
            if end_date_str:
                self.current_trip.end_date = date.fromisoformat(end_date_str)
            else:
                self.current_trip.end_date = None
            
            # Обновление бюджета
            budget_str = self.trip_form_vars['budget'].get()
            if budget_str:
                success, budget, message = validate_currency_amount(budget_str)
                if success:
                    self.current_trip.budget = budget
            
            self.current_trip.currency = self.trip_form_vars['currency'].get()
            self.current_trip.status = TripStatus(self.trip_form_vars['status'].get())
            self.current_trip.participants = self.trip_form_vars['participants'].get()
            self.current_trip.description = self.trip_form_vars['description'].get('1.0', tk.END).strip()
            
            # Обновляем в БД
            success = self.storage.update_trip(self.current_trip)
            if success:
                messagebox.showinfo("Успех", "Путешествие успешно обновлено!")
                self._load_trips()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить путешествие")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при обновлении путешествия: {e}")
    
    def _delete_trip(self):
        """Удаление выбранного путешествия."""
        selection = self.trips_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите путешествие для удаления")
            return
        
        item = self.trips_tree.item(selection[0])
        trip_id = item['values'][0]
        trip_name = item['values'][1]
        
        if messagebox.askyesno("Подтверждение", 
                              f"Вы действительно хотите удалить путешествие '{trip_name}'?\n\n"
                              f"Все связанные расходы также будут удалены."):
            success = self.storage.delete_trip(trip_id)
            if success:
                messagebox.showinfo("Успех", "Путешествие успешно удалено!")
                self._load_trips()
                self._clear_trip_form()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить путешествие")
    
    def _clear_trip_form(self):
        """Очистка формы путешествия."""
        for var in self.trip_form_vars.values():
            if isinstance(var, tk.StringVar):
                var.set("")
            elif isinstance(var, tk.Text):
                var.delete('1.0', tk.END)
        
        # Установка значений по умолчанию
        self.trip_form_vars['currency'].set("USD")
        self.trip_form_vars['status'].set(TripStatus.PLANNED.value)
        
        # Снимаем выделение с Treeview
        for item in self.trips_tree.selection():
            self.trips_tree.selection_remove(item)
        
        self.current_trip = None
    
    # --- Методы для работы с расходами ---
    
    def _on_trip_combobox_select(self, event):
        """Обработка выбора путешествия в combobox."""
        selected = self.selected_trip_var.get()
        if selected and ':' in selected:
            trip_id = int(selected.split(':')[0])
            self._load_expenses_for_trip(trip_id)
    
    def _load_expenses_for_trip(self, trip_id: int):
        """Загрузка расходов для указанного путешествия."""
        try:
            # Очищаем Treeview
            for item in self.expenses_tree.get_children():
                self.expenses_tree.delete(item)
            
            # Загружаем расходы
            self.current_expenses = self.storage.get_expenses_by_trip(trip_id)
            
            # Заполняем Treeview
            for expense in self.current_expenses:
                # Обрезаем длинное описание
                description = expense.description
                if len(description) > 50:
                    description = description[:47] + "..."
                
                self.expenses_tree.insert('', 'end', values=(
                    expense.id,
                    expense.date,
                    expense.category.value,
                    f"{expense.amount:.2f}",
                    expense.currency,
                    expense.location,
                    description
                ))
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить расходы: {e}")
    
    def _load_expenses(self):
        """Загрузка расходов для выбранного путешествия."""
        selected = self.selected_trip_var.get()
        if selected and ':' in selected:
            trip_id = int(selected.split(':')[0])
            self._load_expenses_for_trip(trip_id)
        else:
            messagebox.showwarning("Внимание", "Выберите путешествие")
    
    def _add_expense(self):
        """Добавление нового расхода."""
        try:
            # Проверяем, выбрано ли путешествие
            selected = self.selected_trip_var.get()
            if not selected:
                messagebox.showwarning("Внимание", "Сначала выберите путешествие")
                return
            
            trip_id = int(selected.split(':')[0])
            
            # Валидация суммы
            amount_str = self.expense_form_vars['amount'].get()
            success, amount, message = validate_currency_amount(amount_str)
            if not success:
                messagebox.showwarning("Внимание", message)
                return
            
            # Валидация даты
            date_str = self.expense_form_vars['date'].get()
            expense_date = None
            if date_str:
                try:
                    expense_date = date.fromisoformat(date_str)
                except ValueError:
                    messagebox.showwarning("Внимание", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")
                    return
            else:
                expense_date = date.today()
            
            # Создание объекта Expense
            expense = Expense(
                trip_id=trip_id,
                amount=amount,
                currency=self.expense_form_vars['currency'].get(),
                category=ExpenseCategory(self.expense_form_vars['category'].get()),
                date=expense_date,
                description=self.expense_form_vars['description'].get('1.0', tk.END).strip(),
                payment_method=self.expense_form_vars['payment_method'].get(),
                location=self.expense_form_vars['location'].get()
            )
            
            # Сохранение в БД
            expense_id = self.storage.add_expense(expense)
            if expense_id > 0:
                messagebox.showinfo("Успех", "Расход успешно добавлен!")
                self._clear_expense_form()
                self._load_expenses()
            else:
                messagebox.showerror("Ошибка", "Не удалось добавить расход")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при добавлении расхода: {e}")
    
    def _delete_expense(self):
        """Удаление выбранного расхода."""
        selection = self.expenses_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите расход для удаления")
            return
        
        item = self.expenses_tree.item(selection[0])
        expense_id = item['values'][0]
        
        if messagebox.askyesno("Подтверждение", "Вы действительно хотите удалить этот расход?"):
            success = self.storage.delete_expense(expense_id)
            if success:
                messagebox.showinfo("Успех", "Расход успешно удален!")
                self._load_expenses()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить расход")
    
    def _clear_expense_form(self):
        """Очистка формы расхода."""
        for var in self.expense_form_vars.values():
            if isinstance(var, tk.StringVar):
                var.set("")
            elif isinstance(var, tk.Text):
                var.delete('1.0', tk.END)
        
        # Установка значений по умолчанию
        self.expense_form_vars['currency'].set("USD")
        self.expense_form_vars['category'].set(ExpenseCategory.FOOD.value)
        self.expense_form_vars['payment_method'].set("Наличные")
        self.expense_form_vars['date'].set(str(date.today()))
    
    # --- Методы аналитики ---
    
    def _update_analytics(self):
        """Обновление графиков аналитики."""
        selected = self.analytics_trip_var.get()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите путешествие для анализа")
            return
        
        try:
            # Закрываем старые графики
            plt.close('all')
            
            if selected == "Все путешествия":
                # Анализ всех путешествий
                self._analyze_all_trips()
            else:
                # Анализ конкретного путешествия
                trip_id = int(selected.split(':')[0])
                self._analyze_single_trip(trip_id)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при обновлении графиков: {e}")
    
    def _analyze_single_trip(self, trip_id: int):
        """Анализ конкретного путешествия."""
        # Загружаем данные
        trips = self.storage.get_all_trips()
        expenses = self.storage.get_expenses_by_trip(trip_id)
        
        if not expenses:
            self._show_no_data_message("Для выбранного путешествия нет данных о расходах.")
            return
        
        # Создаем анализатор
        analyzer = TravelAnalyzer(trips, expenses)
        
        # Создаем графики для одного путешествия
        self._create_single_trip_analytics(analyzer, trip_id)
    
    def _analyze_all_trips(self):
        """Анализ всех путешествий."""
        # Загружаем все данные
        trips = self.storage.get_all_trips()
        all_expenses = []
        
        # Получаем все расходы для всех путешествий
        for trip in trips:
            expenses = self.storage.get_expenses_by_trip(trip.id)
            all_expenses.extend(expenses)
        
        if not all_expenses:
            self._show_no_data_message("Нет данных о расходах для анализа всех путешествий.")
            return
        
        # Создаем анализатор
        analyzer = TravelAnalyzer(trips, all_expenses)
        
        # Создаем графики для всех путешествий
        self._create_all_trips_analytics(analyzer)
    
    def _create_single_trip_analytics(self, analyzer: TravelAnalyzer, trip_id: int):
        """Создание и отображение графиков для одного путешествия."""
        # Очищаем старые графики
        for widget in self.analytics_canvas_frame.winfo_children():
            widget.destroy()
        
        try:
            # Создаем сетку 2x2 для графиков
            self.analytics_canvas_frame.grid_rowconfigure(0, weight=1)
            self.analytics_canvas_frame.grid_rowconfigure(1, weight=1)
            self.analytics_canvas_frame.grid_columnconfigure(0, weight=1)
            self.analytics_canvas_frame.grid_columnconfigure(1, weight=1)
            
            # График 1: Распределение расходов по категориям
            frame1 = ttk.Frame(self.analytics_canvas_frame)
            frame1.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
            
            fig1 = analyzer.plot_expense_categories(trip_id)
            canvas1 = FigureCanvasTkAgg(fig1, frame1)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill='both', expand=True)
            
            # Добавляем тулбар для графика 1
            toolbar1 = NavigationToolbar2Tk(canvas1, frame1)
            toolbar1.update()
            canvas1.get_tk_widget().pack(fill='both', expand=True)
            
            # График 2: Ежедневные расходы
            frame2 = ttk.Frame(self.analytics_canvas_frame)
            frame2.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
            
            fig2 = analyzer.plot_daily_expenses(trip_id)
            canvas2 = FigureCanvasTkAgg(fig2, frame2)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill='both', expand=True)
            
            # Добавляем тулбар для графика 2
            toolbar2 = NavigationToolbar2Tk(canvas2, frame2)
            toolbar2.update()
            canvas2.get_tk_widget().pack(fill='both', expand=True)
            
            # График 3: Сравнение бюджета с фактическими расходами
            frame3 = ttk.Frame(self.analytics_canvas_frame)
            frame3.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
            
            fig3 = analyzer.plot_budget_vs_actual(trip_id)
            canvas3 = FigureCanvasTkAgg(fig3, frame3)
            canvas3.draw()
            canvas3.get_tk_widget().pack(fill='both', expand=True)
            
            # Добавляем тулбар для графика 3
            toolbar3 = NavigationToolbar2Tk(canvas3, frame3)
            toolbar3.update()
            canvas3.get_tk_widget().pack(fill='both', expand=True)
            
            # График 4: Статистика и рекомендации
            frame4 = ttk.Frame(self.analytics_canvas_frame)
            frame4.grid(row=1, column=1, padx=5, pady=5, sticky='nsew')
            
            fig4 = analyzer.plot_expense_statistics(trip_id)
            canvas4 = FigureCanvasTkAgg(fig4, frame4)
            canvas4.draw()
            canvas4.get_tk_widget().pack(fill='both', expand=True)
            
            # Добавляем тулбар для графика 4
            toolbar4 = NavigationToolbar2Tk(canvas4, frame4)
            toolbar4.update()
            canvas4.get_tk_widget().pack(fill='both', expand=True)
            
            # Добавляем кнопку для сохранения всех графиков
            save_frame = ttk.Frame(self.analytics_canvas_frame)
            save_frame.grid(row=2, column=0, columnspan=2, pady=10)
            
            # Получаем имя путешествия для имени файла
            selected = self.analytics_trip_var.get()
            trip_name = selected.split(':', 1)[1].strip() if ':' in selected else f"trip_{trip_id}"
            
            ttk.Button(save_frame, text="💾 Сохранить все графики",
                      command=lambda: self._save_all_graphs([fig1, fig2, fig3, fig4], 
                                                           trip_id, trip_name),
                      style='Accent.TButton').pack()
            
        except Exception as e:
            print(f"Ошибка при создании графиков: {e}")
            self._show_error_message(f"Ошибка при создании графиков:\n{str(e)}")
    
    def _create_all_trips_analytics(self, analyzer: TravelAnalyzer):
        """Создание и отображение графиков для всех путешествий."""
        # Очищаем старые графики
        for widget in self.analytics_canvas_frame.winfo_children():
            widget.destroy()
        
        try:
            # Создаем сетку 2x2 для графиков
            self.analytics_canvas_frame.grid_rowconfigure(0, weight=1)
            self.analytics_canvas_frame.grid_rowconfigure(1, weight=1)
            self.analytics_canvas_frame.grid_columnconfigure(0, weight=1)
            self.analytics_canvas_frame.grid_columnconfigure(1, weight=1)
            
            # Получаем все графики для всех путешествий
            figures = analyzer.plot_all_trips_analytics()
            
            # График 1: Сравнение бюджетов по всем путешествиям
            if 'all_budget_comparison' in figures:
                frame1 = ttk.Frame(self.analytics_canvas_frame)
                frame1.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
                
                canvas1 = FigureCanvasTkAgg(figures['all_budget_comparison'], frame1)
                canvas1.draw()
                canvas1.get_tk_widget().pack(fill='both', expand=True)
                
                toolbar1 = NavigationToolbar2Tk(canvas1, frame1)
                toolbar1.update()
                canvas1.get_tk_widget().pack(fill='both', expand=True)
            
            # График 2: Расходы по категориям (все путешествия)
            if 'all_expenses_by_category' in figures:
                frame2 = ttk.Frame(self.analytics_canvas_frame)
                frame2.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
                
                canvas2 = FigureCanvasTkAgg(figures['all_expenses_by_category'], frame2)
                canvas2.draw()
                canvas2.get_tk_widget().pack(fill='both', expand=True)
                
                toolbar2 = NavigationToolbar2Tk(canvas2, frame2)
                toolbar2.update()
                canvas2.get_tk_widget().pack(fill='both', expand=True)
            
            # График 3: Распределение путешествий по статусам
            if 'trips_by_status' in figures:
                frame3 = ttk.Frame(self.analytics_canvas_frame)
                frame3.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
                
                canvas3 = FigureCanvasTkAgg(figures['trips_by_status'], frame3)
                canvas3.draw()
                canvas3.get_tk_widget().pack(fill='both', expand=True)
                
                toolbar3 = NavigationToolbar2Tk(canvas3, frame3)
                toolbar3.update()
                canvas3.get_tk_widget().pack(fill='both', expand=True)
            
            # График 4: Тренд расходов по месяцам
            if 'monthly_trend' in figures:
                frame4 = ttk.Frame(self.analytics_canvas_frame)
                frame4.grid(row=1, column=1, padx=5, pady=5, sticky='nsew')
                
                canvas4 = FigureCanvasTkAgg(figures['monthly_trend'], frame4)
                canvas4.draw()
                canvas4.get_tk_widget().pack(fill='both', expand=True)
                
                toolbar4 = NavigationToolbar2Tk(canvas4, frame4)
                toolbar4.update()
                canvas4.get_tk_widget().pack(fill='both', expand=True)
            
            # Добавляем сводную статистику и кнопки
            summary_frame = ttk.Frame(self.analytics_canvas_frame)
            summary_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky='nsew')
            
            # Получаем сводную статистику
            summary = analyzer.get_all_trips_summary()
            
            # Отображаем ключевую статистику
            stats_text = f"📈 Сводная статистика по всем путешествиям:\n\n"
            stats_text += f"• Всего путешествий: {summary.get('total_trips', 0)}\n"
            stats_text += f"• Завершено: {summary.get('completed_trips', 0)} | В процессе: {summary.get('in_progress_trips', 0)} | Запланировано: {summary.get('planned_trips', 0)}\n"
            stats_text += f"• Общий бюджет: {summary.get('total_budget', 0):,.2f}\n"
            stats_text += f"• Фактические расходы: {summary.get('total_actual_spent', 0):,.2f}\n"
            stats_text += f"• Всего расходов: {summary.get('total_expenses', 0)}\n"
            
            if 'total_expenses_amount' in summary:
                stats_text += f"• Сумма всех расходов: {summary.get('total_expenses_amount', 0):,.2f}\n"
                stats_text += f"• Средний расход: {summary.get('avg_expense_amount', 0):,.2f}\n"
            
            stats_label = ttk.Label(summary_frame, text=stats_text, font=('Segoe UI', 10))
            stats_label.pack(pady=5)
            
            # Добавляем кнопки для экспорта
            buttons_frame = ttk.Frame(summary_frame)
            buttons_frame.pack(pady=10)
            
            ttk.Button(buttons_frame, text="📊 Экспорт сводного отчета (CSV)",
                      command=lambda: self._export_all_trips_report(analyzer),
                      width=30).pack(side='left', padx=5)
            
            ttk.Button(buttons_frame, text="📁 Экспорт всех данных (JSON)",
                      command=lambda: self._export_all_trips_json(analyzer),
                      width=30).pack(side='left', padx=5)
            
            ttk.Button(buttons_frame, text="💾 Сохранить все графики",
                      command=lambda: self._save_all_graphs(list(figures.values()), 
                                                           "all", "all_trips"),
                      style='Accent.TButton').pack(side='left', padx=5)
            
        except Exception as e:
            print(f"Ошибка при создании графиков для всех путешествий: {e}")
            self._show_error_message(f"Ошибка при создании графиков:\n{str(e)}")
    
    def _export_all_trips_report(self, analyzer: TravelAnalyzer):
        """Экспорт сводного отчета по всем путешествиям в CSV."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Сохранить сводный отчет по всем путешествиям",
                initialfile="all_trips_summary.csv"
            )
            
            if not filename:
                return
            
            exported_file = analyzer.export_all_trips_to_csv(filename)
            if exported_file:
                messagebox.showinfo(
                    "Успех",
                    f"Сводный отчет по всем путешествиям успешно экспортирован:\n\n{exported_file}"
                )
            else:
                messagebox.showerror("Ошибка", "Не удалось экспортировать отчет")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при экспорте отчета: {e}")
    
    def _export_all_trips_json(self, analyzer: TravelAnalyzer):
        """Экспорт всех данных в JSON."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Сохранить все данные в JSON",
                initialfile="all_trips_data.json"
            )
            
            if not filename:
                return
            
            exported_file = analyzer.export_all_trips_to_json(filename)
            if exported_file:
                messagebox.showinfo(
                    "Успех",
                    f"Все данные успешно экспортированы в JSON:\n\n{exported_file}"
                )
            else:
                messagebox.showerror("Ошибка", "Не удалось экспортировать данные")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при экспорте данных: {e}")
    
    def _save_all_graphs(self, figures, trip_id, trip_name="trip"):
        """Сохранение всех графиков в файлы."""
        try:
            # Создаем папку для графиков, если её нет
            export_dir = "data/graphs"
            os.makedirs(export_dir, exist_ok=True)
            
            # Убираем недопустимые символы в имени файла
            import re
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', trip_name)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            saved_files = []
            
            # Сохраняем каждый график
            for i, fig in enumerate(figures, 1):
                if trip_id == "all":
                    filename = os.path.join(export_dir, f"all_trips_graph_{i}_{timestamp}.png")
                else:
                    filename = os.path.join(export_dir, f"{safe_name}_graph_{i}_{timestamp}.png")
                
                fig.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
                saved_files.append(filename)
                print(f"График сохранен: {filename}")
            
            # Показываем сообщение об успехе
            messagebox.showinfo(
                "Графики сохранены",
                f"Все графики успешно сохранены в папку:\n{export_dir}\n\n"
                f"Сохранено файлов: {len(saved_files)}"
            )
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить графики: {e}")
    
    def _show_no_data_message(self, message: str):
        """Показать сообщение об отсутствии данных."""
        for widget in self.analytics_canvas_frame.winfo_children():
            widget.destroy()
        
        no_data_frame = ttk.Frame(self.analytics_canvas_frame)
        no_data_frame.pack(expand=True, fill='both')
        
        # Центрируем
        no_data_frame.grid_rowconfigure(0, weight=1)
        no_data_frame.grid_rowconfigure(2, weight=1)
        no_data_frame.grid_columnconfigure(0, weight=1)
        no_data_frame.grid_columnconfigure(2, weight=1)
        
        ttk.Label(no_data_frame,
                 text="📭 Нет данных для анализа",
                 font=('Segoe UI', 14, 'bold')).grid(row=1, column=1, pady=10)
        
        ttk.Label(no_data_frame,
                 text=f"{message}\n\nДобавьте расходы во вкладке 'Расходы' для анализа.",
                 font=('Segoe UI', 11),
                 justify='center').grid(row=2, column=1, pady=20)
    
    def _show_error_message(self, error_text: str):
        """Показать сообщение об ошибке."""
        for widget in self.analytics_canvas_frame.winfo_children():
            widget.destroy()
        
        error_frame = ttk.Frame(self.analytics_canvas_frame)
        error_frame.pack(expand=True, fill='both')
        
        ttk.Label(error_frame,
                 text=error_text,
                 foreground='red',
                 justify='center').pack(expand=True)
    
    # --- Методы экспорта ---
    
    def _export_data(self):
        """Экспорт данных выбранного путешествия или всех путешествий."""
        selected = self.export_trip_var.get()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите путешествие для экспорта")
            return
        
        try:
            export_format = self.export_format_var.get()
            
            if selected == "Все путешествия":
                # Экспорт всех путешествий
                self._export_all_trips_data(export_format)
            else:
                # Экспорт конкретного путешествия
                trip_id = int(selected.split(':')[0])
                self._export_single_trip_data(trip_id, export_format)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при экспорте данных: {e}")
    
    def _export_single_trip_data(self, trip_id: int, export_format: str):
        """Экспорт данных одного путешествия."""
        try:
            # Открываем диалог сохранения файла
            if export_format == "JSON":
                filetypes = [("JSON files", "*.json"), ("All files", "*.*")]
                default_ext = ".json"
            else:
                filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
                default_ext = ".csv"
            
            filename = filedialog.asksaveasfilename(
                defaultextension=default_ext,
                filetypes=filetypes,
                title="Сохранить данные путешествия"
            )
            
            if not filename:
                return
            
            # Экспорт данных
            if export_format == "JSON":
                success = self.storage.export_trip_to_json(trip_id, filename)
                if success:
                    self.export_status_label.config(
                        text=f"✅ Данные успешно экспортированы в:\n{filename}",
                        foreground='green'
                    )
                else:
                    messagebox.showerror("Ошибка", "Не удалось экспортировать данные")
            else:
                # Для CSV используем анализатор
                trips = self.storage.get_all_trips()
                expenses = self.storage.get_expenses_by_trip(trip_id)
                analyzer = TravelAnalyzer(trips, expenses)
                analyzer.generate_expense_report(trip_id, filename)
                self.export_status_label.config(
                    text=f"✅ Отчёт успешно экспортирован в:\n{filename}",
                    foreground='green'
                )
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при экспорте данных: {e}")
    
    def _export_all_trips_data(self, export_format: str):
        """Экспорт данных всех путешествий."""
        try:
            # Открываем диалог сохранения файла
            if export_format == "JSON":
                filetypes = [("JSON files", "*.json"), ("All files", "*.*")]
                default_ext = ".json"
                initialfile = "all_trips_data.json"
            else:
                filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
                default_ext = ".csv"
                initialfile = "all_trips_summary.csv"
            
            filename = filedialog.asksaveasfilename(
                defaultextension=default_ext,
                filetypes=filetypes,
                title="Сохранить все данные путешествий",
                initialfile=initialfile
            )
            
            if not filename:
                return
            
            # Загружаем все данные
            trips = self.storage.get_all_trips()
            all_expenses = []
            
            for trip in trips:
                expenses = self.storage.get_expenses_by_trip(trip.id)
                all_expenses.extend(expenses)
            
            # Создаем анализатор
            analyzer = TravelAnalyzer(trips, all_expenses)
            
            # Экспорт данных
            if export_format == "JSON":
                exported_file = analyzer.export_all_trips_to_json(filename)
                if exported_file:
                    self.export_status_label.config(
                        text=f"✅ Все данные успешно экспортированы в:\n{exported_file}",
                        foreground='green'
                    )
                else:
                    messagebox.showerror("Ошибка", "Не удалось экспортировать данные")
            else:
                exported_file = analyzer.export_all_trips_to_csv(filename)
                if exported_file:
                    self.export_status_label.config(
                        text=f"✅ Сводный отчет успешно экспортирован в:\n{exported_file}",
                        foreground='green'
                    )
                else:
                    messagebox.showerror("Ошибка", "Не удалось экспортировать отчет")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при экспорте всех данных: {e}")
    
    def _export_summary_report(self):
        """Экспорт сводного отчета по всем путешествиям."""
        try:
            # Загружаем все данные
            trips = self.storage.get_all_trips()
            all_expenses = []
            
            for trip in trips:
                expenses = self.storage.get_expenses_by_trip(trip.id)
                all_expenses.extend(expenses)
            
            if not trips:
                messagebox.showinfo("Информация", "Нет данных для экспорта")
                return
            
            # Создаем анализатор
            analyzer = TravelAnalyzer(trips, all_expenses)
            
            # Открываем диалог сохранения файла
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Сохранить сводный отчет",
                initialfile="travel_summary_report.csv"
            )
            
            if not filename:
                return
            
            # Экспортируем отчет
            exported_file = analyzer.export_all_trips_to_csv(filename)
            if exported_file:
                messagebox.showinfo(
                    "Успех",
                    f"Сводный отчет успешно экспортирован:\n\n{exported_file}"
                )
                self.export_status_label.config(
                    text=f"✅ Сводный отчет экспортирован в:\n{exported_file}",
                    foreground='green'
                )
            else:
                messagebox.showerror("Ошибка", "Не удалось экспортировать отчет")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при экспорте отчета: {e}")
    
    def _export_all_data_json(self):
        """Экспорт всех данных в JSON."""
        try:
            # Загружаем все данные
            trips = self.storage.get_all_trips()
            all_expenses = []
            
            for trip in trips:
                expenses = self.storage.get_expenses_by_trip(trip.id)
                all_expenses.extend(expenses)
            
            if not trips:
                messagebox.showinfo("Информация", "Нет данных для экспорта")
                return
            
            # Создаем анализатор
            analyzer = TravelAnalyzer(trips, all_expenses)
            
            # Открываем диалог сохранения файла
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Сохранить все данные в JSON",
                initialfile="all_travel_data.json"
            )
            
            if not filename:
                return
            
            # Экспортируем данные
            exported_file = analyzer.export_all_trips_to_json(filename)
            if exported_file:
                messagebox.showinfo(
                    "Успех",
                    f"Все данные успешно экспортированы в JSON:\n\n{exported_file}"
                )
                self.export_status_label.config(
                    text=f"✅ Все данные экспортированы в:\n{exported_file}",
                    foreground='green'
                )
            else:
                messagebox.showerror("Ошибка", "Не удалось экспортировать данные")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при экспорте данных: {e}")
    
    def _open_data_folder(self):
        """Открытие папки с данными."""
        try:
            data_dir = "data"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # Открываем папку в проводнике
            if os.name == 'nt':  # Windows
                os.startfile(data_dir)
            elif os.name == 'posix':  # macOS, Linux
                import subprocess
                subprocess.run(['open', data_dir] if sys.platform == 'darwin' else ['xdg-open', data_dir])
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку с данными: {e}")