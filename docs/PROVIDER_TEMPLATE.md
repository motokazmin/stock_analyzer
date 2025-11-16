# 🔌 Шаблон для Собственного Провайдера Новостей

Используй этот файл как основу для создания нового провайдера.

---

## 📋 Минимальный Шаблон

Сохрани это в `news_providers/my_provider.py`:

```python
"""
Пример провайдера новостей для [Название сервиса/рынка].
"""

from abc import ABC
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MyNewsProvider(NewsProvider):
    """Провайдер новостей для [Название]."""
    
    API_URL = "https://api.example.com/news"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: API ключ от сервиса
        """
        self.api_key = api_key or "default_key"
        
        if self.api_key == "default_key":
            logger.warning(f"⚠️ {self.get_name()} использует стандартный ключ!")
    
    def search_news(self, ticker: str, max_results: int = 5) -> List[Dict]:
        """
        Ищет новости по тикеру.
        
        Args:
            ticker: Тикер акции (например, "SBER", "AAPL")
            max_results: Максимум результатов
            
        Returns:
            Список новостей. ОБЯЗАТЕЛЬНЫЙ ФОРМАТ:
            [
                {
                    'title': str,
                    'description': str,
                    'date': str (YYYY-MM-DD),
                    'source': str,
                    'url': str,
                    'sentiment': str ('POSITIVE', 'NEGATIVE', 'NEUTRAL')
                },
                ...
            ]
        """
        logger.info(f"🔍 Ищу новости {ticker} через {self.get_name()}")
        
        try:
            # ТУТ ТВОЙ КОД: Запрос к API, парсинг данных
            # Пример:
            # response = requests.get(self.API_URL, params=...)
            # data = response.json()
            # ... обработка ...
            
            news_list = []  # Заполни это
            
            logger.info(f"✅ Найдено {len(news_list)} новостей")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return []  # Всегда возвращай пустой список при ошибке!
    
    def _analyze_sentiment(self, text: str) -> str:
        """
        Анализирует sentiment текста.
        
        Args:
            text: Текст для анализа
            
        Returns:
            'POSITIVE', 'NEGATIVE' или 'NEUTRAL'
        """
        text_lower = text.lower()
        
        # Твоя логика анализа
        positive_words = ['хороший', 'рост', 'прибыль']
        negative_words = ['плохой', 'падение', 'убыток']
        
        pos = sum(1 for w in positive_words if w in text_lower)
        neg = sum(1 for w in negative_words if w in text_lower)
        
        if pos > neg:
            return 'POSITIVE'
        elif neg > pos:
            return 'NEGATIVE'
        else:
            return 'NEUTRAL'
    
    def get_name(self) -> str:
        """Возвращает имя провайдера."""
        return "MyNewsProvider"
```

---

## 📝 Полный Пример: MOEX Провайдер

Когда MOEX выпустит API, вот как это может выглядеть:

```python
"""
Провайдер новостей для MOEX (МосБиржа).
Источник: https://www.moex.com/ru/news/
"""

import requests
from datetime import datetime
from typing import Dict, List
from news_integration import NewsProvider
import logging

logger = logging.getLogger(__name__)


class MOEXNewsProvider(NewsProvider):
    """
    Провайдер новостей с МосБиржи.
    
    API документация: https://www.moex.com/en/dev/
    """
    
    # Гипотетический API endpoint
    MOEX_API_URL = "https://api.moex.com/v1/news"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "public"
        logger.info("📰 Инициализирован MOEXNewsProvider")
    
    def search_news(self, ticker: str, max_results: int = 5) -> List[Dict]:
        """Запрашивает новости по тикеру с МосБиржи."""
        
        logger.info(f"🔍 Ищу новости {ticker} на MOEX...")
        
        try:
            params = {
                'ticker': ticker,  # MOEX использует ticker напрямую
                'lang': 'ru',
                'limit': max_results,
                'token': self.api_key
            }
            
            response = requests.get(
                f"{self.MOEX_API_URL}",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data or 'error' in data:
                logger.warning(f"⚠️ MOEX вернул пусто или ошибку")
                return []
            
            news_list = []
            for article in data.get('news', [])[:max_results]:
                # MOEX может возвращать дату в разных форматах
                # Нормализуем в YYYY-MM-DD
                date_str = article.get('date', '')
                try:
                    parsed_date = datetime.fromisoformat(date_str).strftime('%Y-%m-%d')
                except:
                    parsed_date = date_str[:10] if date_str else 'Unknown'
                
                news_item = {
                    'title': article.get('headline', '') or article.get('title', ''),
                    'description': article.get('summary', '') or article.get('text', ''),
                    'date': parsed_date,
                    'source': 'MOEX',
                    'url': article.get('url', '') or f"https://moex.com/ru/news/{article.get('id', '')}",
                    'sentiment': self._analyze_sentiment(
                        article.get('headline', '') + ' ' + article.get('summary', '')
                    )
                }
                news_list.append(news_item)
            
            logger.info(f"✅ Найдено {len(news_list)} новостей по {ticker}")
            return news_list
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ MOEX API не отвечает (timeout)")
            return []
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Ошибка подключения к MOEX")
            return []
        except Exception as e:
            logger.error(f"❌ Ошибка при запросе к MOEX: {e}")
            return []
    
    def _analyze_sentiment(self, text: str) -> str:
        """Анализирует sentiment текста на русском."""
        text_lower = text.lower()
        
        # Расширенный словарь для русского языка
        positive_words = [
            'рост', 'прибыль', 'доход', 'успех', 'хороший', 'отличный',
            'увеличение', 'подъём', 'восстановление', 'улучшение',
            'выплата', 'дивиденд', 'контракт', 'сделка', 'инвестиции',
            'развитие', 'расширение', 'новый рекорд'
        ]
        
        negative_words = [
            'падение', 'убыток', 'потеря', 'снижение', 'плохой',
            'кризис', 'санкции', 'штраф', 'критика', 'проблема',
            'скандал', 'банкротство', 'задолженность', 'дефолт',
            'конфликт', 'риск', 'опасность'
        ]
        
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        
        if pos_count > neg_count:
            return 'POSITIVE'
        elif neg_count > pos_count:
            return 'NEGATIVE'
        else:
            return 'NEUTRAL'
    
    def get_name(self) -> str:
        return "MOEXNewsProvider"
```

---

## 🚀 Как Использовать Новый Провайдер

### 1. Создай файл

Сохрани провайдер в `news_providers/moex_provider.py`

### 2. Обнови main.py

```python
from news_integration import NewsIntegration
from news_providers.moex_provider import MOEXNewsProvider

# Используем MOEX вместо Mock
moex = MOEXNewsProvider(api_key="твой_key_если_нужен")
news_integration = NewsIntegration(provider=moex)

# Теперь работает!
```

### 3. Тестируй

```bash
python main.py analyze
```

### 4. Готово!

Новости теперь поступают с MOEX.

---

## ✅ Чек-лист для Нового Провайдера

- [ ] Класс наследует `NewsProvider`
- [ ] Реализован метод `search_news()` с правильной сигнатурой
- [ ] Реализован метод `get_name()`
- [ ] Возвращаемый формат соответствует стандарту (все поля)
- [ ] При ошибке возвращается `[]` (graceful fail)
- [ ] Дата в формате `YYYY-MM-DD`
- [ ] Sentiment в верхнем регистре: `POSITIVE`, `NEGATIVE`, `NEUTRAL`
- [ ] Логирование добавлено (logger.info, logger.error)
- [ ] API key передаётся в конструктор (не в коде)
- [ ] Timeout установлен (10 секунд)

---

## 🔗 Интеграция с Фреймворком

**Шаг 1:** Добавить импорт в `news_integration.py`:

```python
from news_providers.moex_provider import MOEXNewsProvider
```

**Шаг 2:** Обновить документацию:

- [ ] Обновить `docs/NEWS_ARCHITECTURE.md`
- [ ] Добавить в секцию "Доступные провайдеры"
- [ ] Описать setup инструкции

**Шаг 3:** Обновить `.cursorules`:

```
6. **News Integration**: Используй MOEXNewsProvider для MOEX новостей
```

---

## 📞 Поддержка Нескольких Провайдеров Одновременно

Если нужно комбинировать новости из нескольких источников:

```python
class MultiNewsProvider(NewsProvider):
    """Комбинирует результаты от нескольких провайдеров."""
    
    def __init__(self, providers: List[NewsProvider]):
        self.providers = providers
    
    def search_news(self, ticker: str, max_results: int = 5) -> List[Dict]:
        all_news = []
        
        for provider in self.providers:
            try:
                news = provider.search_news(ticker, max_results=3)
                all_news.extend(news)
            except:
                continue
        
        # Сортируем по дате (новые первыми)
        all_news.sort(key=lambda x: x['date'], reverse=True)
        
        return all_news[:max_results]
    
    def get_name(self) -> str:
        return "MultiNewsProvider"

# Использование:
multi = MultiNewsProvider([
    MOEXNewsProvider(),
    FinnhubNewsProvider(),
])
news_integration = NewsIntegration(provider=multi)
```

---

## 🎯 Что Дальше?

Когда MOEX выпустит новый API:
1. Создай `MOEXNewsProvider` по этому шаблону
2. Протестируй `python main.py analyze`
3. Радуйся новостям в отчётах! 🎉

