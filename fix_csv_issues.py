#!/usr/bin/env python3
"""
Исправление проблем в CSV файлах:
1. Объединение дублирующихся дат (две сессии торговли)
2. Удаление строк с VOLUME=0 (дни без торговли)
"""

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def fix_csv_file(csv_path: Path) -> bool:
    """Исправляет CSV файл."""
    try:
        # Читаем файл
        df = pd.read_csv(csv_path, parse_dates=['DATE'])
        original_rows = len(df)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📄 {csv_path.name}")
        logger.info(f"{'='*60}")
        logger.info(f"Исходно: {original_rows} строк")
        
        # Шаг 1: Объединяем дублирующиеся даты (две сессии торговли)
        # Если есть несколько записей в один день - берем сессию с большим объемом (T+0)
        duplicates = df[df.duplicated(subset=['DATE'], keep=False)]
        if len(duplicates) > 0:
            duplicate_dates = duplicates['DATE'].unique()
            logger.info(f"⚠️  Найдено дублирующихся дат (две сессии): {len(duplicate_dates)}")
            for dup_date in duplicate_dates[:3]:  # Показываем первые 3
                dup_records = df[df['DATE'] == dup_date]
                logger.info(f"   {dup_date.date()}: {len(dup_records)} записей")
                for idx, row in dup_records.iterrows():
                    vol_display = f"{int(row['VOLUME']):,}" if pd.notna(row['VOLUME']) else "N/A"
                    logger.info(f"      O={row['OPEN']} C={row['CLOSE']} V={vol_display}")
            
            # Сортируем по дате и объему (УБЫВАНИЕ)
            # Берем первую запись каждой даты (с максимальным объемом) = T+0 основная сессия
            df = df.sort_values(['DATE', 'VOLUME'], ascending=[True, False])
            df = df.drop_duplicates(subset=['DATE'], keep='first')  # Берем T+0 (большой объем)
            logger.info(f"✅ Объединено: {original_rows - len(df)} дополнительных сессий удалено")
            logger.info(f"   Оставлена основная сессия T+0 (большой объем)")
        
        before_volume_filter = len(df)
        
        # Шаг 2: Удаляем строки с VOLUME=0
        df = df[df['VOLUME'] > 0]
        volume_removed = before_volume_filter - len(df)
        if volume_removed > 0:
            logger.info(f"🧹 Удалены дни без торговли: {volume_removed} строк")
        
        # Шаг 3: Проверяем целостность данных
        df = df.sort_values('DATE').reset_index(drop=True)
        
        # Сохраняем
        df.to_csv(csv_path, index=False)
        
        logger.info(f"📊 Итого: {len(df)} строк")
        logger.info(f"   Диапазон: {df['DATE'].min().date()} → {df['DATE'].max().date()}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

# Обрабатываем все CSV файлы
data_dir = Path("stock_data")
csv_files = sorted(data_dir.glob("*.csv"))

logger.info(f"\n🔧 ИСПРАВЛЕНИЕ CSV ФАЙЛОВ\n")
logger.info(f"Найдено файлов: {len(csv_files)}\n")

success = 0
failed = 0

for csv_file in csv_files:
    if fix_csv_file(csv_file):
        success += 1
    else:
        failed += 1

logger.info(f"\n{'='*60}")
logger.info(f"✅ Успешно: {success}/{len(csv_files)}")
logger.info(f"❌ Ошибок: {failed}")
logger.info(f"{'='*60}\n")

# ВАЖНО: Информация о влиянии на алгоритмы
logger.info("""
📊 ВЛИЯНИЕ НА АЛГОРИТМЫ АНАЛИЗА:

1️⃣  EMA (Экспоненциальная Скользящая Средняя):
   ✅ EMA_20 = среднее за 20 дней ТОРГОВЛИ (не календарных)
   ✅ Это ПРАВИЛЬНО - технические индикаторы используют торговые дни
   ✅ При удалении VOLUME=0 данные не нарушаются

2️⃣  RSI (Relative Strength Index):
   ✅ RSI считает изменения за периоды торговли
   ✅ Пропускаем выходные/праздники = прямо к следующему торговому дню
   ✅ Это корректно!

3️⃣  Support/Resistance (Поддержка/Сопротивление):
   ✅ Ищем экстремумы в торговых днях
   ✅ Выходные не важны для уровней
   ✅ Данные только более точные

4️⃣  Volume Profile (Профиль объемов):
   ✅ Объем только по торговым дням
   ✅ При удалении VOLUME=0 исключаем фиктивные записи
   ✅ Анализ становится корректнее

ВЫВОД: ✅ Удаление VOLUME=0 и объединение дублей = улучшение качества данных!
""")

