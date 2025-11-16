# 📰 Архитектура Новостной Интеграции

## 📋 Обзор

Система новостей построена на **провайдерной архитектуре**, что позволяет:
- ✅ Легко переключаться между провайдерами
- ✅ Добавлять новые провайдеры без изменения основного кода
- ✅ Использовать заглушку (mock) для тестирования
- ✅ Поддерживать разные рынки и источники

---

## 🏗️ Структура Компонентов

### 1. **NewsProvider** (базовый интерфейс)

```python
class NewsProvider(ABC):
    @abstractmethod
    def search_news(self, ticker: str, max_results: int = 5) -> List[Dict]:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass
```

**Что это?**
- Абстрактный класс, который определяет интерфейс для всех провайдеров
- Гарантирует одинаковую сигнатуру методов
- Позволяет подменять провайдеров в runtime

---

### 2. **MockNewsProvider** (заглушка)

```python
class MockNewsProvider(NewsProvider):
    def search_news(self, ticker: str, max_results: int = 5) -> List[Dict]:
        return []  # Всегда возвращает пусто
```

**Когда использовать:**
- 🔧 Тестирование системы без API вызовов
- 📊 Отладка логики рекомендаций
- ✅ Быстрые прогоны анализа
- 🚀 По умолчанию (сейчас, для РФ рынка)

**Используется сейчас** ← потому что Finnhub не покрывает MOEX

---

### 3. **FinnhubNewsProvider** (для US рынка)

```python
class FinnhubNewsProvider(NewsProvider):
    def search_news(self, ticker: str, max_results: int = 5) -> List[Dict]:
        # Запрос к https://finnhub.io/api/v1/company-news
        # Работает только для US тикеров!
```

**Когда использовать:**
- 🇺🇸 Анализ американских акций
- 📡 Надёжный источник финансовых новостей
- ⚡ 60 запросов/минуту

**Когда НЕ использовать:**
- ❌ Российские акции (нет данных)
- ❌ Другие рынки

---

## 🔄 Как Переключать Провайдеры

### Текущее состояние

```python
# news_integration.py
news_integration = NewsIntegration()  # Использует Mock по умолчанию
```

### Переключение на Finnhub

```python
from news_integration import NewsIntegration, FinnhubNewsProvider

# Создаём провайдер с API key
finnhub = FinnhubNewsProvider(api_key="ваш_реальный_токен")

# Передаём в NewsIntegration
news_integration = NewsIntegration(provider=finnhub)

# Теперь поиск будет через Finnhub
news = news_integration.search_news("AAPL")
```

### Использование в main.py

```python
from news_integration import NewsIntegration, FinnhubNewsProvider

# Option 1: Mock (по умолчанию, новостей нет)
news_integration = NewsIntegration()

# Option 2: Finnhub (для US акций)
# finnhub = FinnhubNewsProvider(api_key="YOUR_KEY")
# news_integration = NewsIntegration(provider=finnhub)

# Option 3: Собственный провайдер (см. ниже)
# custom = MyCustomNewsProvider()
# news_integration = NewsIntegration(provider=custom)
```

---

## 🛠️ Как Добавить Новый Провайдер

### Шаг 1: Создать класс, наследующий NewsProvider

```python
from news_integration import NewsProvider

class MOEXNewsProvider(NewsProvider):
    """Провайдер новостей для MOEX (когда появится API)."""
    
    MOEX_API_URL = "https://api.moex.com/news"  # Гипотетический URL
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        logger.info("📰 Инициализирован MOEXNewsProvider")
    
    def search_news(self, ticker: str, max_results: int = 5) -> List[Dict]:
        """Запрашивает новости из MOEX API."""
        try:
            params = {
                'ticker': ticker,
                'limit': max_results,
                'lang': 'ru'
            }
            
            response = requests.get(self.MOEX_API_URL, params=params)
            response.raise_for_status()
            
            articles = response.json()
            
            news_list = []
            for article in articles:
                news_item = {
                    'title': article.get('headline', ''),
                    'description': article.get('summary', ''),
                    'date': article.get('date', ''),
                    'source': 'MOEX',
                    'url': article.get('url', ''),
                    'sentiment': self._analyze_sentiment(article.get('headline', ''))
                }
                news_list.append(news_item)
            
            return news_list
        except Exception as e:
            logger.error(f"Ошибка MOEX провайдера: {e}")
            return []
    
    def _analyze_sentiment(self, text: str) -> str:
        """Анализирует sentiment текста."""
        # Твоя логика анализа
        return 'NEUTRAL'
    
    def get_name(self) -> str:
        return "MOEXNewsProvider"
```

### Шаг 2: Использовать в коде

```python
from news_integration import NewsIntegration, MOEXNewsProvider

moex_provider = MOEXNewsProvider(api_key="moex_key")
news_integration = NewsIntegration(provider=moex_provider)

# Теперь работает!
news = news_integration.search_news("SBER")
```

### Шаг 3: Зарегистрировать в документации

Обновить этот файл с новым провайдером.

---

## 📊 Формат Возвращаемых Новостей

Все провайдеры возвращают один и тот же формат:

```python
[
    {
        'title': 'Сбербанк повысил дивиденды',
        'description': 'Полная информация о новости...',
        'date': '2025-11-16',
        'source': 'Reuters',  # или 'MOEX', 'Finnhub', и т.д.
        'url': 'https://...',
        'sentiment': 'POSITIVE'  # или 'NEGATIVE', 'NEUTRAL'
    },
    # ... остальные новости
]
```

**Поля обязательны** для совместимости с `NewsIntegration` и `promt.txt`.

---

## 🔌 Интеграция с main.py

### Текущий поток

```
1. python main.py analyze
   ↓
2. analyze_data() вызывает NewsIntegration()
   ↓
3. NewsIntegration использует MockNewsProvider (по умолчанию)
   ↓
4. Новостей нет → stock_news.json пусто
   ↓
5. HTML отчёт создан БЕЗ новостей (ладно, техника работает)
```

### Будущий поток (с MOEX API)

```
1. python main.py analyze
   ↓
2. analyze_data() создаёт NewsIntegration(provider=MOEXNewsProvider())
   ↓
3. Идёт поиск новостей для BUY акций
   ↓
4. Результаты сохранены в stock_news.json
   ↓
5. HTML отчёт содержит новостной фон!
```

---

## ✅ Текущее Состояние

### 🟡 Активно (Mock провайдер)
- Новостей нет
- Анализ работает без них
- HTML создаётся без раздела "📰 Новостной фон"

### 🔴 Неактивно (Finnhub)
- Не поддерживает российские акции
- Оставлен для примера и будущего использования

### ⏳ Планируется
- [ ] MOEX API (когда появится)
- [ ] Интеграция с финансовыми порталами РФ
- [ ] Кэширование новостей (уже реализовано)
- [ ] Анализ sentiment на NLP (вместо keyword-based)

---

## 🚀 Миграция на MOEX (когда будет готово)

1. **Создать MOEXNewsProvider** (см. Шаг 1 выше)
2. **Обновить main.py:**
```python
from news_integration import NewsIntegration, MOEXNewsProvider

moex = MOEXNewsProvider()
news_integration = NewsIntegration(provider=moex)
```

3. **Тестировать:**
```bash
python main.py analyze
```

4. **Готово!** Все новости из MOEX теперь в отчёте.

---

## 📝 Примечания

- **Кэширование**: NewsIntegration кэширует результаты на 24 часа
- **Обработка ошибок**: Все провайдеры возвращают `[]` при ошибке (graceful fail)
- **Sentiment анализ**: Простой keyword-based (можно улучшить с NLP позже)
- **Скорость**: Mock провайдер идеален для dev/testing

