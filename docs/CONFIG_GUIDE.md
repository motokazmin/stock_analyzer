# ⚙️ CONFIG_GUIDE - Руководство по конфигурации

Полное руководство по управлению конфигурацией приложения Stock Analyzer.

## 📋 Структура config.json

```json
{
  "app": {
    "name": "Stock Analyzer",
    "version": "1.0.0",
    "language": "ru"
  },
  "watchlist": ["SBER", "GAZP", "LKOH"],
  "folders": {
    "data_folder": "stock_data",
    "reports_folder": "reports",
    "logs_folder": "logs"
  },
  "analysis": {
    "period_months": 6,
    "ema_periods": [20, 50, 200],
    "rsi_period": 14
  },
  "key_levels": {
    "SBER": {
      "support": [275, 265],
      "resistance": [290, 305]
    }
  },
  "trading": {
    "min_rsi_for_buy": 30,
    "max_rsi_for_sell": 70
  },
  "last_updated": null,
  "last_report": null
}
```

## 📚 Поля конфигурации

### app
Информация о приложении.

```json
"app": {
  "name": "Stock Analyzer",       // Имя приложения
  "version": "1.0.0",             // Версия
  "language": "ru"                // Язык интерфейса
}
```

### watchlist
Список акций для мониторинга.

```json
"watchlist": [
  "SBER",    // Сбербанк
  "GAZP",    // Газпром
  "LKOH"     // Лукойл
]
```

### folders
Пути к рабочим директориям.

```json
"folders": {
  "data_folder": "stock_data",     // Папка с CSV данными
  "reports_folder": "reports",     // Папка с отчётами
  "logs_folder": "logs"            // Папка с логами
}
```

### analysis
Параметры технического анализа.

```json
"analysis": {
  "period_months": 6,              // Период анализа (месяцы)
  "min_data_points": 60,           // Минимум данных для анализа
  "ema_periods": [20, 50, 200],    // Периоды EMA
  "rsi_period": 14,                // Период RSI
  "volume_bins": 20,               // Бины для профиля объёмов
  "support_resistance_window": 20  // Окно для S/R
}
```

### key_levels
Ключевые уровни поддержки и сопротивления для каждой акции.

```json
"key_levels": {
  "SBER": {
    "support": [275, 265],         // Уровни поддержки
    "resistance": [290, 305],      // Уровни сопротивления
    "notes": "Важные уровни"       // Заметки
  },
  "GAZP": {
    "support": [140, 150],
    "resistance": [170, 180]
  }
}
```

### trading
Торговые параметры.

```json
"trading": {
  "min_rsi_for_buy": 30,           // Минимум RSI для сигнала покупки
  "max_rsi_for_sell": 70,          // Максимум RSI для сигнала продажи
  "min_volume_multiplier": 1.2,    // Минимум объёма к среднему
  "risk_reward_ratio": 1.5         // Соотношение риск/награда
}
```

### reporting
Настройки отчётирования.

```json
"reporting": {
  "format": "markdown",                 // Формат отчёта
  "include_detailed_analysis": true,    // Включать детальный анализ
  "include_entry_exit_points": true,    // Включать точки входа/выхода
  "theme": "default"                    // Тема оформления
}
```

### Временные метки

```json
"last_updated": "2024-11-13T10:15:30",  // Последнее обновление
"last_report": "2024-11-13T10:16:45"    // Последний отчёт
```

---

## 🔧 ConfigManager - Управление конфигурацией

### Основные методы

#### 1. `load_config()` - Загрузить конфигурацию

```python
from config_manager import ConfigManager

config = ConfigManager.load_config()
print(config['watchlist'])
```

#### 2. `save_config(config)` - Сохранить конфигурацию

```python
ConfigManager.save_config(config)
```

#### 3. `get_watchlist()` - Получить список акций

```python
tickers = ConfigManager.get_watchlist()
# ['SBER', 'GAZP', 'LKOH']
```

#### 4. `set_watchlist(tickers)` - Установить список акций

```python
ConfigManager.set_watchlist(['SBER', 'GAZP', 'PLZL'])
```

#### 5. `add_to_watchlist(ticker)` - Добавить акцию

```python
ConfigManager.add_to_watchlist('PLZL')
```

#### 6. `remove_from_watchlist(ticker)` - Удалить акцию

```python
ConfigManager.remove_from_watchlist('GAZP')
```

#### 7. `get_key_levels(ticker)` - Получить уровни акции

```python
levels = ConfigManager.get_key_levels('SBER')
# {'support': [275, 265], 'resistance': [290, 305]}
```

#### 8. `set_key_levels(ticker, levels)` - Установить уровни

```python
levels = {
    'support': [280, 290],
    'resistance': [310, 320],
    'notes': 'Новые уровни'
}
ConfigManager.set_key_levels('SBER', levels)
```

#### 9. `get_data_folder()` - Получить папку данных

```python
folder = ConfigManager.get_data_folder()
# PosixPath('stock_data')
```

#### 10. `get_reports_folder()` - Получить папку отчётов

```python
folder = ConfigManager.get_reports_folder()
```

#### 11. `get_analysis_settings()` - Получить параметры анализа

```python
settings = ConfigManager.get_analysis_settings()
# {'period_months': 6, 'ema_periods': [20, 50, 200], ...}
```

#### 12. `get_trading_settings()` - Получить торговые параметры

```python
settings = ConfigManager.get_trading_settings()
```

#### 13. `get_setting(key_path, default)` - Получить значение по пути

```python
version = ConfigManager.get_setting('app.version')
# '1.0.0'

ema = ConfigManager.get_setting('analysis.ema_periods')
# [20, 50, 200]

missing = ConfigManager.get_setting('app.missing', 'default')
# 'default'
```

#### 14. `set_setting(key_path, value)` - Установить значение по пути

```python
ConfigManager.set_setting('app.language', 'en')
ConfigManager.set_setting('analysis.period_months', 12)
```

#### 15. `validate_config(config)` - Проверить конфигурацию

```python
is_valid, errors = ConfigManager.validate_config(config)
if is_valid:
    print("✅ Конфигурация валидна")
else:
    print(f"❌ Ошибки: {errors}")
```

#### 16. `update_last_updated()` - Обновить timestamp обновления

```python
ConfigManager.update_last_updated()
```

#### 17. `update_last_report()` - Обновить timestamp отчёта

```python
ConfigManager.update_last_report()
```

#### 18. `print_config()` - Вывести конфигурацию

```python
ConfigManager.print_config()
```

#### 19. `export_config(filepath)` - Экспортировать конфигурацию

```python
ConfigManager.export_config('backup_config.json')
```

#### 20. `import_config(filepath)` - Импортировать конфигурацию

```python
ConfigManager.import_config('backup_config.json')
```

#### 21. `reset_to_default()` - Сбросить на значения по умолчанию

```python
ConfigManager.reset_to_default()
```

---

## 📖 Примеры использования

### Пример 1: Управление watchlist

```python
from config_manager import ConfigManager

# Получить текущий список
watchlist = ConfigManager.get_watchlist()
print(f"Акций: {watchlist}")

# Добавить новую
ConfigManager.add_to_watchlist('PLZL')

# Удалить старую
ConfigManager.remove_from_watchlist('TATN')

# Получить новый список
watchlist = ConfigManager.get_watchlist()
print(f"Новый список: {watchlist}")
```

### Пример 2: Работа с ключевыми уровнями

```python
# Добавить уровни для новой акции
levels = {
    'support': [2100, 2150],
    'resistance': [2300, 2400],
    'notes': 'Полюс Золото - важные уровни'
}
ConfigManager.set_key_levels('PLZL', levels)

# Получить уровни
levels = ConfigManager.get_key_levels('PLZL')
print(f"Поддержка: {levels['support']}")
print(f"Сопротивление: {levels['resistance']}")
```

### Пример 3: Изменение параметров анализа

```python
# Изменить период анализа на 12 месяцев
ConfigManager.set_setting('analysis.period_months', 12)

# Изменить EMA периоды
ConfigManager.set_setting('analysis.ema_periods', [10, 30, 100])

# Изменить минимум RSI для покупки
ConfigManager.set_setting('trading.min_rsi_for_buy', 25)
```

### Пример 4: Получение всех параметров

```python
# Получить все параметры анализа
analysis = ConfigManager.get_analysis_settings()
for key, value in analysis.items():
    print(f"{key}: {value}")

# Получить торговые параметры
trading = ConfigManager.get_trading_settings()
for key, value in trading.items():
    print(f"{key}: {value}")

# Получить параметры отчётирования
reporting = ConfigManager.get_reporting_settings()
for key, value in reporting.items():
    print(f"{key}: {value}")
```

### Пример 5: Работа с папками

```python
from config_manager import ConfigManager
import pandas as pd

# Получить папку данных
data_folder = ConfigManager.get_data_folder()

# Прочитать CSV
df = pd.read_csv(data_folder / 'SBER_full.csv')

# Получить папку отчётов
reports_folder = ConfigManager.get_reports_folder()

# Сохранить отчёт
report_path = reports_folder / 'analysis.md'
with open(report_path, 'w') as f:
    f.write('# Анализ')
```

### Пример 6: Интеграция с main.py

```python
from config_manager import ConfigManager
from stock_data_manager import StockDataManager
from technical_analysis import TechnicalAnalyzer

# Получить watchlist из конфига
watchlist = ConfigManager.get_watchlist()

# Обновить данные
manager = StockDataManager()
manager.update_watchlist(watchlist)

# Получить параметры анализа
settings = ConfigManager.get_analysis_settings()
ema_periods = settings['ema_periods']

# Проанализировать
analyzer = TechnicalAnalyzer()
for ticker in watchlist:
    result = analyzer.analyze_stock(ticker)
    
    # Получить ключевые уровни
    levels = ConfigManager.get_key_levels(ticker)
    if levels:
        print(f"{ticker}: S={levels['support']}, R={levels['resistance']}")
    
    # Обновить timestamp
    ConfigManager.update_last_updated()
```

---

## 🎯 Типичные сценарии

### Сценарий 1: Начальная настройка

```bash
# Программа создаст config.json с параметрами по умолчанию
python main.py list

# Отредактируйте config.json если нужно
# Измените watchlist, папки, параметры анализа и т.д.
```

### Сценарий 2: Добавление нового тикера

```python
from config_manager import ConfigManager

# Добавить в watchlist
ConfigManager.add_to_watchlist('PLZL')

# Установить ключевые уровни
ConfigManager.set_key_levels('PLZL', {
    'support': [2100, 2150],
    'resistance': [2300, 2400]
})
```

### Сценарий 3: Изменение параметров

```python
# Увеличить период анализа
ConfigManager.set_setting('analysis.period_months', 12)

# Изменить торговые параметры
ConfigManager.set_setting('trading.min_rsi_for_buy', 25)
ConfigManager.set_setting('trading.max_rsi_for_sell', 75)
```

### Сценарий 4: Резервная копия

```python
# Сделать резервную копию
ConfigManager.export_config('config_backup_20240113.json')

# Восстановить из резервной копии
ConfigManager.import_config('config_backup_20240113.json')
```

---

## 📝 Редактирование вручную

Вы можете отредактировать `config.json` в любом текстовом редакторе:

```json
{
  "watchlist": ["SBER", "GAZP", "PLZL"],
  "analysis": {
    "period_months": 12,
    "ema_periods": [10, 30, 100]
  }
}
```

**Важно:** 
- Соблюдайте формат JSON
- После редактирования программа автоматически её загрузит
- При ошибке в JSON конфигурация вернётся на значения по умолчанию

---

## ✅ Валидация конфигурации

```python
from config_manager import ConfigManager

# Проверить конфигурацию
config = ConfigManager.load_config()
is_valid, errors = ConfigManager.validate_config(config)

if is_valid:
    print("✅ Конфигурация валидна")
else:
    print(f"❌ Ошибки: {errors}")
    # Сбросить на значения по умолчанию
    ConfigManager.reset_to_default()
```

---

## 🔌 Интеграция

ConfigManager используется везде в приложении:

```python
# В main.py
from config_manager import ConfigManager
watchlist = ConfigManager.get_watchlist()

# В stock_data_manager.py
from config_manager import ConfigManager
data_folder = ConfigManager.get_data_folder()

# В technical_analysis.py
from config_manager import ConfigManager
settings = ConfigManager.get_analysis_settings()

# В report_generator.py
from config_manager import ConfigManager
reports_folder = ConfigManager.get_reports_folder()
```

---

## 🎓 Лучшие практики

1. **Используйте конфиг для параметров** - не добавляйте параметры в код
2. **Валидируйте конфиг** - перед использованием важных параметров
3. **Делайте резервные копии** - перед кардинальными изменениями
4. **Логируйте изменения** - фиксируйте когда что было изменено
5. **Документируйте кастомные поля** - если добавляете свои параметры

---

**Версия:** 1.0.0  
**Дата:** 13 Ноября 2024  
**Статус:** ✅ Production Ready

