"""
Модуль api_client.py
Работа с внешними API (курсы валют, погода, карты).
"""
import aiohttp
import asyncio
import json
from typing import Dict, Optional, Any
from datetime import datetime
import logging


class TravelAPIClient:
    """Класс для работы с внешними API."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        await self.create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()
    
    async def create_session(self):
        """Создание асинхронной сессии."""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Закрытие асинхронной сессии."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_exchange_rates(self, base_currency: str = "USD") -> Optional[Dict[str, float]]:
        """
        Получение текущих курсов валют.
        Используется бесплатный API exchangerate-api.com
        """
        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('rates', {})
                else:
                    self.logger.error(f"Ошибка получения курсов валют: {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Ошибка при запросе курсов валют: {e}")
            return None
    
    async def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """Конвертация суммы из одной валюты в другую."""
        rates = await self.get_exchange_rates(from_currency)
        
        if rates and to_currency in rates:
            rate = rates[to_currency]
            return amount * rate
        
        return None
    
    async def get_weather_forecast(self, city: str, days: int = 3) -> Optional[Dict[str, Any]]:
        """
        Получение прогноза погоды.
        Используется бесплатный API OpenWeatherMap (требуется API ключ).
        """
        # В реальном приложении здесь должен быть ваш API ключ
        api_key = "YOUR_API_KEY"  # Заменить на реальный ключ
        if api_key == "YOUR_API_KEY":
            self.logger.warning("API ключ для погоды не установлен")
            return None
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/forecast"
            params = {
                'q': city,
                'appid': api_key,
                'units': 'metric',
                'cnt': days * 8  # 8 записей в день на 3 дня
            }
            
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Обработка данных прогноза
                    forecast = []
                    for item in data.get('list', [])[:days*3]:  # Берем по 3 записи в день
                        forecast.append({
                            'datetime': datetime.fromtimestamp(item['dt']),
                            'temp': item['main']['temp'],
                            'feels_like': item['main']['feels_like'],
                            'humidity': item['main']['humidity'],
                            'description': item['weather'][0]['description'],
                            'icon': item['weather'][0]['icon']
                        })
                    
                    return {
                        'city': data['city']['name'],
                        'country': data['city']['country'],
                        'forecast': forecast
                    }
                else:
                    self.logger.error(f"Ошибка получения погоды: {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Ошибка при запросе погоды: {e}")
            return None
    
    async def get_travel_advisory(self, country_code: str) -> Optional[Dict[str, Any]]:
        """
        Получение туристических рекомендаций для страны.
        Используется API Travel Advisory.
        """
        try:
            url = f"https://www.travel-advisory.info/api"
            params = {'countrycode': country_code}
            
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {}).get(country_code.upper(), {})
                else:
                    self.logger.error(f"Ошибка получения рекомендаций: {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Ошибка при запросе рекомендаций: {e}")
            return None


# Синхронные обёртки для удобства использования в синхронном коде
class SyncTravelAPIClient:
    """Синхронная обёртка для асинхронного API клиента."""
    
    def __init__(self):
        self.client = TravelAPIClient()
    
    def get_exchange_rates(self, base_currency: str = "USD") -> Optional[Dict[str, float]]:
        """Синхронная версия получения курсов валют."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(self.client.get_exchange_rates(base_currency))
        finally:
            loop.close()
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """Синхронная версия конвертации валют."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(
                self.client.convert_currency(amount, from_currency, to_currency)
            )
        finally:
            loop.close()