# Stock Data Manager - Шпаргалка

## 🚀 Установка

```bash
pip install -r requirements.txt
```

## ⚡ Базовый код

```python
from stock_data_manager import StockDataManager

manager = StockDataManager()
```

## 📥 Загрузка данных

```python
# За период
data = manager.download_stock_data('SBER', '2024-01-01', '2024-12-31')

# Последний год
data = manager.download_stock_data('GAZP')

# Сохранить
manager.save_to_csv('SBER', data)
```

## 🔄 Обновление

```python
# Одна акция (новые данные автоматически)
manager.update_watchlist(['SBER'])

# Несколько акций
manager.update_watchlist(['SBER', 'GAZP', 'LKOH', 'NVTK', 'TATN'])

# Результаты
results = manager.update_watchlist(['SBER'])
# {'SBER': True}  - успешно или False - ошибка
```

## 📊 Получение данных

```python
# Получить DataFrame
df = manager.get_data('SBER')
print(df.head())

# Вывести CSV
df.to_csv('my_data.csv', index=False)

# Работа с Pandas
print(df['CLOSE'].mean())
print(df['CLOSE'].max())
print(df.tail(10))
```

## 📈 Статистика

```python
stats = manager.get_statistics('SBER')

# Доступные поля:
stats['total_records']      # Кол-во записей
stats['date_from']          # Первая дата
stats['date_to']            # Последняя дата
stats['avg_price']          # Средняя цена
stats['min_price']          # Минимум
stats['max_price']          # Максимум
stats['total_volume']       # Объем торгов
```

## 🔍 Анализ

```python
from data_analyzer import DataAnalyzer

analyzer = DataAnalyzer()

# Волатильность
vol = analyzer.get_volatility('SBER')  # %

# Скользящее среднее
ma = analyzer.get_moving_average('SBER', window=20)

# Дневные изменения
changes = analyzer.get_daily_changes('SBER')

# Диапазон цен
range_data = analyzer.get_price_range('SBER')

# Сравнить акции
comparison = analyzer.compare_tickers(['SBER', 'GAZP', 'LKOH'])
print(comparison)

# Экспортировать
analyzer.export_comparison(['SBER', 'GAZP'])
analyzer.export_ticker_data('SBER')
```

## 🎯 Популярные тикеры

```python
# Основные
['SBER', 'GAZP', 'LKOH', 'NVTK', 'TATN']

# Расширенный список
manager.update_watchlist([
    'SBER',    # Сбербанк
    'GAZP',    # Газпром
    'LKOH',    # Лукойл
    'NVTK',    # Новатэк
    'TATN',    # Татнефть
    'PLZL',    # Полюс Золото
    'PHOR',    # Фармакор
])
```

## 🔧 Конфигурация

```python
# Изменить папку данных (в config.py)
DATA_DIR = Path("my_stocks")

# Изменить список акций по умолчанию
DEFAULT_WATCHLIST = ['SBER', 'GAZP']

# Начальный период (дни)
INITIAL_PERIOD_DAYS = 365
```

## 📝 Примеры одной строки

```python
# Загрузить и сохранить
m = StockDataManager()
d = m.download_stock_data('SBER')
m.save_to_csv('SBER', d)

# Получить среднюю цену
print(m.get_statistics('SBER')['avg_price'])

# Все акции за раз
m.update_watchlist(['SBER', 'GAZP', 'LKOH'])
```

## 📋 CSV файлы

```
stock_data/
├── SBER_full.csv
├── GAZP_full.csv
└── ...

Формат: DATE,OPEN,HIGH,LOW,CLOSE,VOLUME
```

## 🚀 Автоматизация

### cron (Linux/Mac)
```bash
# Каждый день в 11:00
0 11 * * * cd /home/roman/projects/ai/trading && python daily_update.py
```

## 🧪 Тесты

```bash
python test_manager.py
```

## 📖 Полная документация

- `README.md` - полная справка
- `QUICKSTART.md` - быстрый старт
- `INSTALL.md` - установка
- `PROJECT_OVERVIEW.md` - описание проекта

## 🔗 API

### StockDataManager

| Метод | Параметры | Возвращает |
|-------|-----------|-----------|
| `download_stock_data()` | ticker, from_date, to_date | DataFrame |
| `update_watchlist()` | tickers_list | Dict[str, bool] |
| `save_to_csv()` | ticker, data | bool |
| `get_data()` | ticker | DataFrame |
| `get_statistics()` | ticker | Dict |

### DataAnalyzer

| Метод | Параметры | Возвращает |
|-------|-----------|-----------|
| `get_volatility()` | ticker, window=20 | float |
| `get_moving_average()` | ticker, window=20 | DataFrame |
| `get_daily_changes()` | ticker | DataFrame |
| `get_price_range()` | ticker | Dict |
| `compare_tickers()` | tickers | DataFrame |

## 🌐 API Endpoint

```
https://iss.moex.com/iss/history/engines/stock/markets/shares/securities/{ticker}.json
```

## 📊 Пример полного рабочего кода

```python
from stock_data_manager import StockDataManager
from data_analyzer import DataAnalyzer

# Загрузить
manager = StockDataManager()
manager.update_watchlist(['SBER', 'GAZP'])

# Проанализировать
analyzer = DataAnalyzer()

for ticker in ['SBER', 'GAZP']:
    stats = manager.get_statistics(ticker)
    vol = analyzer.get_volatility(ticker)
    
    print(f"{ticker}")
    print(f"  Ср. цена: {stats['avg_price']:.2f}")
    print(f"  Волатильность: {vol:.2f}%")

# Сравнить
df = analyzer.compare_tickers(['SBER', 'GAZP'])
print(df)

# Экспортировать
analyzer.export_comparison(['SBER', 'GAZP'], 'report.csv')
```

## 💡 Советы

- **Первый запуск медленный** - загружается вся история
- **Обновления быстрые** - только новые данные
- **Используйте cron** - для автоматизации
- **Проверяйте логи** - `tail stock_data_manager.log`
- **Сохраняйте CSV** - для архивирования и архива

## ⚠️ Возможные ошибки

```python
# Тикер не существует
# → Проверьте написание (SBER, GAZP, LKOH)

# API не отвечает
# → Проверьте интернет, подождите и повторите

# Пустой DataFrame
# → Проверьте диапазон дат

# "No such file"
# → Запустите первый раз обновление
```

## 🎓 Быстрый старт за 2 минуты

```bash
# 1. Установка
pip install -r requirements.txt

# 2. Python код
python -c "
from stock_data_manager import StockDataManager
m = StockDataManager()
m.update_watchlist(['SBER', 'GAZP', 'LKOH'])
"

# 3. Готово! Данные в stock_data/
```

---

**Все просто!** 🚀

Больше примеров в `example_usage.py`

