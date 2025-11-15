# Stock Data Manager - Загрузчик данных Мосбиржи

Автоматический скрипт для загрузки и управления данными акций с Московской биржи (Мосбиржи) через официальный API ISS.

## Особенности

✅ **Полная автоматизация** - загрузка данных одной командой  
✅ **Интеллектуальное обновление** - загружает только новые данные  
✅ **Обработка ошибок** - автоматические повторные попытки при сбое API  
✅ **Логирование** - детальное логирование всех операций в файл и консоль  
✅ **CSV сохранение** - удобный формат для анализа в Excel или Python  
✅ **Пакетная обработка** - одновременное обновление списка акций  
✅ **Статистика** - получение базовой статистики по акциям  

## Установка

### Требования
- Python 3.7+
- pip

### Шаги установки

1. Клонируйте/скопируйте проект:
```bash
cd /home/roman/projects/ai/trading
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Использование

### Базовый пример

```python
from stock_data_manager import StockDataManager

# Инициализация менеджера
manager = StockDataManager()

# Обновление списка акций
tickers = ['SBER', 'GAZP', 'NVTK']
results = manager.update_watchlist(tickers)
```

### Загрузка данных за период

```python
manager = StockDataManager()

# Загрузить данные за конкретный период
data = manager.download_stock_data(
    ticker='SBER',
    from_date='2024-01-01',
    to_date='2024-12-31'
)

print(data.head())
```

### Получение статистики

```python
stats = manager.get_statistics('SBER')
print(f"Средняя цена: {stats['avg_price']:.2f} ₽")
print(f"Макс. цена: {stats['max_price']:.2f} ₽")
print(f"Мин. цена: {stats['min_price']:.2f} ₽")
```

### Получение сохраненных данных

```python
df = manager.get_data('SBER')
print(df.head())
```

## API Класса StockDataManager

### Методы

#### `download_stock_data(ticker, from_date=None, to_date=None)`
Скачивает данные по акции с API Мосбиржи.

**Параметры:**
- `ticker` (str) - тикер акции (например, 'SBER')
- `from_date` (str, опционально) - начальная дата в формате 'YYYY-MM-DD'
- `to_date` (str, опционально) - конечная дата в формате 'YYYY-MM-DD'

**Возвращает:** pandas.DataFrame с колонками [DATE, OPEN, HIGH, LOW, CLOSE, VOLUME]

**Пример:**
```python
data = manager.download_stock_data('GAZP', '2024-01-01', '2024-12-31')
```

---

#### `update_watchlist(tickers_list)`
Обновляет данные для списка акций. Автоматически определяет последнюю дату и загружает только новые данные.

**Параметры:**
- `tickers_list` (List[str]) - список тикеров

**Возвращает:** Dict со статусом обновления каждого тикера

**Пример:**
```python
results = manager.update_watchlist(['SBER', 'GAZP', 'LKOH'])
# {'SBER': True, 'GAZP': True, 'LKOH': True}
```

---

#### `save_to_csv(ticker, data)`
Сохраняет данные в CSV файл.

**Параметры:**
- `ticker` (str) - тикер акции
- `data` (pd.DataFrame) - DataFrame для сохранения

**Возвращает:** bool - успешность сохранения

**Файлы сохраняются в:** `stock_data/{ticker}_full.csv`

---

#### `get_data(ticker)`
Получает сохраненные данные по тикеру из CSV файла.

**Параметры:**
- `ticker` (str) - тикер акции

**Возвращает:** pandas.DataFrame или None если данные не найдены

---

#### `get_statistics(ticker)`
Получает базовую статистику по акции.

**Параметры:**
- `ticker` (str) - тикер акции

**Возвращает:** Dict с полями:
- `ticker` - тикер
- `total_records` - количество записей
- `date_from` - первая дата
- `date_to` - последняя дата
- `avg_price` - средняя цена закрытия
- `min_price` - минимальная цена
- `max_price` - максимальная цена
- `total_volume` - общий объем торгов

## Формат CSV

Данные сохраняются в формате:

```
DATE,OPEN,HIGH,LOW,CLOSE,VOLUME
2024-01-01,105.50,106.25,105.00,106.00,12500000
2024-01-02,106.00,107.50,105.75,107.25,15300000
```

Где:
- **DATE** - дата торгов (YYYY-MM-DD)
- **OPEN** - цена открытия
- **HIGH** - максимальная цена за день
- **LOW** - минимальная цена за день
- **CLOSE** - цена закрытия
- **VOLUME** - объем торгов

## API Мосбиржи

Используется официальное API ISS Мосбиржи:

```
https://iss.moex.com/iss/history/engines/stock/markets/shares/securities/{ticker}.json
```

**Параметры:**
- `start` - начальная позиция (для пагинации)
- `limit` - количество записей за раз (макс. 100)

## Логирование

Все операции логируются в:
- **Консоль** - в реальном времени
- **Файл** - `stock_data_manager.log`

Формат логов:
```
2024-11-13 10:30:45,123 - stock_data_manager - INFO - StockDataManager инициализирован
2024-11-13 10:30:46,234 - stock_data_manager - INFO - Начинаем загрузку данных для SBER
```

## Примеры использования

Смотрите файл `example_usage.py` для 5 полных примеров:

1. **example_1_simple_download()** - простая загрузка данных
2. **example_2_update_watchlist()** - обновление списка акций
3. **example_3_get_statistics()** - получение статистики
4. **example_4_get_latest_data()** - последние данные
5. **example_5_incremental_update()** - инкрементальное обновление

Запуск примера:
```bash
python example_usage.py
```

## Обработка ошибок

Менеджер автоматически обрабатывает:

✓ **Сбои сети** - автоматические повторные попытки (3 попытки)  
✓ **Ошибки API** - логирование с описанием проблемы  
✓ **Некорректные данные** - парсинг с обработкой исключений  
✓ **Отсутствие файлов** - создание новых файлов  
✓ **Дубликаты данных** - удаление при объединении  

## Популярные тикеры Мосбиржи

- **SBER** - Сбербанк
- **GAZP** - Газпром
- **LKOH** - Лукойл
- **NVTK** - Новатэк
- **TATN** - Татнефть
- **PHOR** - Фармакор
- **Si** - Силверейдо
- **PLZL** - Полюс Золото
- **POSI** - ПосИТ Индекс

## Расписание

Для автоматического обновления каждый день, используйте **cron** (Linux/Mac):

```bash
# Обновление каждый день в 11:00 по московскому времени
0 11 * * * cd /home/roman/projects/ai/trading && python -c "from stock_data_manager import StockDataManager; m = StockDataManager(); m.update_watchlist(['SBER', 'GAZP', 'LKOH'])"
```

Или создайте скрипт `daily_update.py`:

```python
from stock_data_manager import StockDataManager

manager = StockDataManager()
manager.update_watchlist(['SBER', 'GAZP', 'LKOH', 'NVTK', 'TATN'])
```

И запускайте через **Task Scheduler** (Windows) или **cron** (Linux).

## Структура файлов

```
trading/
├── stock_data_manager.py   # Основной класс
├── example_usage.py         # Примеры использования
├── requirements.txt         # Зависимости
├── stock_data_manager.log   # Логи (создается автоматически)
└── stock_data/
    ├── SBER_full.csv
    ├── GAZP_full.csv
    └── ...
```

## Ограничения

⚠️ API Мосбиржи имеет следующие ограничения:

- **Макс. 100 записей** за один запрос (решено пагинацией)
- **История** - обычно доступна за последние несколько лет
- **Время отклика** - рекомендуется добавить интервалы между запросами для большого списка тикеров

## Решение проблем

### "ConnectionError: Max retries exceeded"
Возможны проблемы с сетью. Менеджер автоматически повторит попытку.

### "KeyError: 'history'"
API вернул неожиданный формат. Проверьте:
- Правильность тикера (может быть неактивным или неправильным)
- Доступность сервиса ISS

### "Empty DataFrame"
Нет данных за указанный период. Попробуйте:
- Расширить диапазон дат
- Проверить правильность тикера

## Лицензия

MIT License - свободно используйте и модифицируйте код

## Автор

Roman - Trading Data Manager

