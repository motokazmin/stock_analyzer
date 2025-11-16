"""
Интеграция новостей для улучшения анализа акций.

Архитектура:
- NewsProvider: базовый интерфейс для провайдеров новостей
- MockNewsProvider: заглушка для тестирования (используется по умолчанию)
- FinnhubNewsProvider: провайдер для Finnhub API (для будущего использования)
- NewsIntegration: фасад, управляющий провайдерами

Это позволяет легко переключаться между провайдерами и добавлять новые.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import requests

logger = logging.getLogger(__name__)


class NewsProvider(ABC):
    """Базовый интерфейс для провайдеров новостей."""
    
    @abstractmethod
    def search_news(self, ticker: str, max_results: int = 5) -> List[Dict]:
        """
        Ищет новости по тикеру.
        
        Args:
            ticker: Тикер акции
            max_results: Максимум результатов
            
        Returns:
            Список новостей с полями: title, description, date, source, url, sentiment
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Возвращает имя провайдера."""
        pass


class MockNewsProvider(NewsProvider):
    """
    Заглушка провайдера новостей.
    Возвращает пустой список (новостей нет).
    
    Используется как:
    1. Default провайдер (нет реальных новостей для РФ акций)
    2. Базис для быстрого тестирования без API вызовов
    3. Плейсхолдер для будущих интеграций
    """
    
    def __init__(self):
        """Инициализирует Mock провайдер."""
        logger.info("📰 Используется Mock провайдер новостей (заглушка). Новости отключены.")
    
    def search_news(self, ticker: str, max_results: int = 5) -> List[Dict]:
        """
        Возвращает пустой список новостей.
        
        Args:
            ticker: Тикер акции
            max_results: Максимум результатов
            
        Returns:
            Пустой список
        """
        logger.debug(f"MockNewsProvider: запрос новостей по {ticker} (заглушка)")
        return []
    
    def get_name(self) -> str:
        """Возвращает имя провайдера."""
        return "MockNewsProvider"


class FinnhubNewsProvider(NewsProvider):
    """
    Провайдер новостей через Finnhub API.
    
    ⚠️ ВАЖНО: Finnhub не содержит новостей по российским акциям.
    Используется только для тестирования и будущих расширений.
    
    Setup:
    1. Зарегистрируйся на https://finnhub.io
    2. Скопируй API Token
    3. Передай в конструктор: FinnhubNewsProvider(api_key="token")
    """
    
    FINNHUB_URL = "https://finnhub.io/api/v1/company-news"
    
    def __init__(self, api_key: str = "demo"):
        """
        Args:
            api_key: API token от Finnhub.io
        """
        self.api_key = api_key
        
        if api_key == "demo":
            logger.warning(
                "⚠️ FinnhubNewsProvider использует demo key! "
                "Зарегистрируйся на https://finnhub.io для реального API key."
            )
    
    def search_news(self, ticker: str, max_results: int = 5) -> List[Dict]:
        """
        Ищет новости по тикеру через Finnhub API.
        
        ⚠️ Работает только для США тикеров!
        
        Args:
            ticker: Тикер акции
            max_results: Максимум результатов
            
        Returns:
            Список новостей или пустой список при ошибке
        """
        logger.info(f"🔍 Ищу новости по {ticker} через Finnhub...")
        
        try:
            params = {
                'symbol': ticker,
                'token': self.api_key
            }
            
            response = requests.get(self.FINNHUB_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, dict) and 'error' in data:
                logger.warning(f"⚠️ Finnhub ошибка: {data.get('error')}")
                return []
            
            articles = data if isinstance(data, list) else []
            
            news_list = []
            for article in articles[:max_results]:
                timestamp = article.get('datetime', 0)
                if timestamp:
                    article_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                else:
                    article_date = 'Unknown'
                
                news_item = {
                    'title': article.get('headline', ''),
                    'description': article.get('summary', ''),
                    'date': article_date,
                    'source': article.get('source', 'Unknown'),
                    'url': article.get('url', ''),
                    'sentiment': self._analyze_sentiment(
                        article.get('headline', '') + ' ' + article.get('summary', '')
                    )
                }
                news_list.append(news_item)
            
            logger.info(f"✅ Найдено {len(news_list)} новостей по {ticker}")
            return news_list
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout при поиске новостей {ticker}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка сети: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return []
    
    def _analyze_sentiment(self, text: str) -> str:
        """Анализирует sentiment текста."""
        text_lower = text.lower()
        
        positive_words = ['рост', 'прибыль', 'доход', 'успех', 'хороший', 'отличный', 
                         'увеличение', 'подъём', 'восстановление', 'улучшение']
        negative_words = ['падение', 'убыток', 'потеря', 'снижение', 'плохой', 
                         'кризис', 'санкции', 'штраф', 'критика', 'проблема']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'POSITIVE'
        elif negative_count > positive_count:
            return 'NEGATIVE'
        else:
            return 'NEUTRAL'
    
    def get_name(self) -> str:
        """Возвращает имя провайдера."""
        return "FinnhubNewsProvider"


class NewsIntegration:
    """
    Главный класс для управления новостями.
    
    Использует провайдер (по умолчанию Mock) для получения новостей.
    Легко переключаемся между провайдерами.
    """
    
    def __init__(self, provider: Optional[NewsProvider] = None):
        """
        Args:
            provider: Провайдер новостей (если None, используется MockNewsProvider)
        """
        self.provider = provider or MockNewsProvider()
        logger.info(f"📰 NewsIntegration инициализирована с провайдером: {self.provider.get_name()}")
        
        self.cache_file = Path("stock_news_cache.json")
        self.cache = self._load_cache()
        self.cache_hours = 24
    
    def _load_cache(self) -> Dict:
        """Загружает кэш новостей с диска."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.debug(f"Ошибка загрузки кэша: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Сохраняет кэш новостей на диск."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша: {e}")
    
    def _is_cache_fresh(self, ticker: str) -> bool:
        """Проверяет, свежий ли кэш для тикера."""
        if ticker not in self.cache:
            return False
        
        try:
            cached_time = datetime.fromisoformat(self.cache[ticker]['cached_at'])
            age_hours = (datetime.now() - cached_time).total_seconds() / 3600
            return age_hours < self.cache_hours
        except Exception:
            return False
    
    def search_news(self, ticker: str, max_results: int = 5) -> List[Dict]:
        """
        Ищет новости по тикеру через активный провайдер.
        
        Args:
            ticker: Тикер акции
            max_results: Максимум результатов
            
        Returns:
            Список новостей
        """
        # Проверяем кэш
        if self._is_cache_fresh(ticker):
            logger.debug(f"📰 Новости {ticker} загружены из кэша")
            return self.cache[ticker]['news']
        
        # Получаем из провайдера
        news_list = self.provider.search_news(ticker, max_results)
        
        # Кэшируем результат
        self.cache[ticker] = {
            'news': news_list,
            'cached_at': datetime.now().isoformat()
        }
        self._save_cache()
        
        return news_list
    
    def get_news_for_analysis(self, tickers: List[str]) -> Dict[str, List[Dict]]:
        """
        Получает новости для всех тикеров.
        
        Args:
            tickers: Список тикеров
            
        Returns:
            Словарь {ticker: [news]}
        """
        news_by_ticker = {}
        
        for ticker in tickers:
            news = self.search_news(ticker)
            if news:
                news_by_ticker[ticker] = news
                logger.info(f"✅ Найдено {len(news)} новостей по {ticker}")
            else:
                logger.debug(f"⚠️ Новостей не найдено для {ticker}")
        
        return news_by_ticker
    
    def format_news_for_report(self, ticker: str, news: List[Dict]) -> str:
        """
        Форматирует новости для включения в отчёт.
        
        Args:
            ticker: Тикер акции
            news: Список новостей
            
        Returns:
            Отформатированная строка новостей
        """
        if not news:
            return f"*Нет актуальных новостей по {ticker}*"
        
        formatted = f"### 📰 Новости {ticker}\n\n"
        
        for i, item in enumerate(news[:3], 1):
            title = item.get('title', 'Без названия')
            date = item.get('date', 'Дата неизвестна')
            sentiment = item.get('sentiment', 'NEUTRAL')
            source = item.get('source', 'Источник')
            
            emoji = {
                'POSITIVE': '🟢',
                'NEGATIVE': '🔴',
                'NEUTRAL': '⚪'
            }.get(sentiment, '⚪')
            
            formatted += f"{i}. {emoji} **{title}** ({date}) - [{source}]\n"
        
        return formatted
    
    def analyze_sentiment(self, news_list: List[Dict]) -> str:
        """
        Анализирует общий sentiment по новостям.
        
        Args:
            news_list: Список новостей
            
        Returns:
            'POSITIVE', 'NEGATIVE' или 'NEUTRAL'
        """
        if not news_list:
            return 'NEUTRAL'
        
        positive_count = sum(1 for n in news_list if n.get('sentiment') == 'POSITIVE')
        negative_count = sum(1 for n in news_list if n.get('sentiment') == 'NEGATIVE')
        
        if positive_count > negative_count:
            return 'POSITIVE'
        elif negative_count > positive_count:
            return 'NEGATIVE'
        else:
            return 'NEUTRAL'
    
    def get_provider_info(self) -> str:
        """Возвращает информацию об активном провайдере."""
        return f"Активный провайдер: {self.provider.get_name()}"


def get_news_context_for_buy_signals(buy_signals: List[Dict]) -> Dict[str, str]:
    """
    Вспомогательная функция для получения новостей по BUY сигналам.
    
    ⚠️ СЕЙЧАС ВОЗВРАЩАЕТ ПУСТО (новости отключены).
    
    Args:
        buy_signals: Список BUY сигналов из отчёта
        
    Returns:
        Словарь {ticker: news_context}
    """
    # Используем Mock провайдер (новостей нет)
    news_integration = NewsIntegration()
    news_context = {}
    
    # Ничего не добавляем, так как провайдер вернёт пусто
    logger.debug("⚠️ get_news_context_for_buy_signals: новости отключены (используется Mock провайдер)")
    
    return news_context
