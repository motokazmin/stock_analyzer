#!/usr/bin/env python3
"""
Обновление данных с подробным отчётом о том что происходит.
Показывает откуда берутся последние даты для каждой акции.
"""

import sys
from datetime import datetime
from pathlib import Path
from config_manager import ConfigManager
from stock_data_manager import StockDataManager
import pandas as pd

print("\n" + "="*80)
print("📊 ОБНОВЛЕНИЕ ДАННЫХ - ПОДРОБНЫЙ ОТЧЁТ")
print("="*80 + "\n")

manager = StockDataManager()
config_manager = ConfigManager()
tickers = config_manager.get_watchlist()

print(f"📋 Список акций ({len(tickers)} шт):\n")

# Фаза 1: Анализ текущего состояния
print("-"*80)
print("ФАЗА 1: Проверка существующих файлов")
print("-"*80 + "\n")

file_status = {}

for ticker in tickers:
    csv_path = Path(f"stock_data/{ticker}_full.csv")
    
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path, parse_dates=['DATE'])
            if not df.empty:
                last_date = df['DATE'].max()
                first_date = df['DATE'].min()
                row_count = len(df)
                
                file_status[ticker] = {
                    'exists': True,
                    'first_date': first_date,
                    'last_date': last_date,
                    'rows': row_count
                }
                
                print(f"✅ {ticker:8} | Данные: {first_date.date()} → {last_date.date()} ({row_count} дней)")
            else:
                file_status[ticker] = {'exists': True, 'empty': True}
                print(f"⚠️  {ticker:8} | Файл пуст")
        except Exception as e:
            file_status[ticker] = {'exists': True, 'error': str(e)}
            print(f"❌ {ticker:8} | Ошибка: {e}")
    else:
        file_status[ticker] = {'exists': False}
        print(f"🆕 {ticker:8} | Файл не существует (будет загружен полный период)")

print("\n" + "-"*80)
print("ФАЗА 2: Обновление данных")
print("-"*80 + "\n")

results = manager.update_watchlist(tickers)

print("\n" + "-"*80)
print("ФАЗА 3: Результаты обновления")
print("-"*80 + "\n")

successful = 0
failed = 0

for ticker in tickers:
    csv_path = Path(f"stock_data/{ticker}_full.csv")
    
    if results.get(ticker):
        successful += 1
        if csv_path.exists():
            df = pd.read_csv(csv_path, parse_dates=['DATE'])
            if not df.empty:
                last_date = df['DATE'].max()
                rows = len(df)
                
                # Сравним с предыдущим
                old_status = file_status.get(ticker, {})
                if old_status.get('rows'):
                    new_rows = rows - old_status['rows']
                    print(f"✅ {ticker:8} | ➕ {new_rows:3} новых строк | Всего: {rows:4} | До {last_date.date()}")
                else:
                    print(f"✅ {ticker:8} | 📥 Загружено {rows:4} строк | Период: до {last_date.date()}")
    else:
        failed += 1
        print(f"❌ {ticker:8} | Ошибка обновления")

print("\n" + "="*80)
print(f"📈 ИТОГО: ✅ {successful}/{len(tickers)} успешно | ❌ {failed} ошибок")
print("="*80 + "\n")

print("💡 КАК ЭТО РАБОТАЕТ:\n")
print("""
1. ПРОЧИТАТЬ ПОСЛЕДНЮЮ ДАТУ:
   ├─ Смотрим файл stock_data/{TICKER}_full.csv
   ├─ Если файл есть → читаем последнюю дату из него
   └─ Если нет → начинаем с 1 года назад

2. ЗАГРУЗИТЬ НОВЫЕ ДАННЫЕ:
   ├─ С Мосбиржи API скачиваем с (последняя_дата + 1 день)
   ├─ Если ошибка → пробуем заново
   └─ Результат сохраняем в CSV

3. ОБЪЕДИНИТЬ:
   ├─ Если были старые данные
   ├─ Удаляем дубликаты (последний день старых может повторяться)
   └─ Сохраняем объединённый файл

4. РЕЗУЛЬТАТ:
   └─ Файл всегда синхронизирован с реальными данными на диске
   
⚠️  ВАЖНО: config.json используется ТОЛЬКО для логирования
    Реальная логика берет даты ИЗ ФАЙЛОВ данных!
""")

print("\n" + "="*80)

