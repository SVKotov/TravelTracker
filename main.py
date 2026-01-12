"""
Модуль main.py
Главный файл приложения TravelTracker.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Добавляем текущую директорию в путь для импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from gui import TravelTrackerApp
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print(f"Текущая директория: {current_dir}")
    print(f"Содержимое директории: {os.listdir(current_dir)}")
    raise


def main():
    """Основная функция запуска приложения."""
    try:
        root = tk.Tk()
        
        # Настройка окна
        root.title("TravelTracker - Планировщик путешествий")
        root.geometry("1200x800")
        
        # Иконка приложения (если есть)
        try:
            root.iconbitmap(default='icon.ico')
        except:
            pass
        
        # Создание и запуск приложения
        app = TravelTrackerApp(root)
        
        # Центрирование окна
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Запуск главного цикла
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Критическая ошибка",  # ИСПРАВЛЕНО: shakerror -> showerror
                           f"Не удалось запустить приложение:\n{str(e)}")


if __name__ == "__main__":
    main()