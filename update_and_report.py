#!/usr/bin/env python3
"""
Скрипт для обновления данных и создания актуального отчёта.
Использует свежие данные с актуальными уровнями поддержки/сопротивления.
"""

import sys
import logging
from datetime import datetime
from config_manager import ConfigManager
from stock_data_manager import StockDataManager
from technical_analysis import TechnicalAnalyzer
from report_generator import ReportGenerator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Основная функция."""
    print("\n" + "="*70)
    print("📊 ОБНОВЛЕНИЕ ДАННЫХ И СОЗДАНИЕ АКТУАЛЬНОГО ОТЧЁТА")
    print("="*70 + "\n")
    
    try:
        # 1. Получаем список акций
        print("1️⃣ Получаем список акций...")
        manager = StockDataManager()
        config_manager = ConfigManager()
        
        tickers = config_manager.get_watchlist()
        print(f"   ✓ Список: {', '.join(tickers)}\n")
        
        # 2. Обновляем данные
        print("2️⃣ Обновляем данные с API Мосбиржи...")
        print(f"   Время начала: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        
        results = manager.update_watchlist(tickers)
        
        successful = sum(1 for v in results.values() if v)
        print(f"   ✓ Обновлено успешно: {successful}/{len(tickers)}\n")
        
        for ticker, success in results.items():
            status = "✓" if success else "✗"
            print(f"   [{status}] {ticker}")
        
        # 3. Проверяем данные
        print(f"\n3️⃣ Проверяем актуальность данных...")
        
        analyzer = TechnicalAnalyzer()
        for ticker in tickers:
            df = manager.get_data(ticker)
            if df is not None:
                last_date = df['DATE'].max()
                last_close = df['CLOSE'].iloc[-1]
                print(f"   {ticker}: {last_date.strftime('%Y-%m-%d')} | Цена: {last_close:.2f} ₽")
        
        # 4. Создаём новый отчёт
        print(f"\n4️⃣ Создаём новый отчёт с актуальными уровнями...")
        print(f"   Время создания: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        
        reporter = ReportGenerator()
        report_path = reporter.generate_and_save(tickers)
        
        if report_path:
            print(f"   ✓ Отчёт создан: {report_path}\n")
        else:
            print(f"   ✗ Ошибка при создании отчёта\n")
            return 1
        
        # 5. Выводим краткую информацию по акциям
        print("5️⃣ Информация по акциям:")
        print("-" * 70)
        
        for ticker in tickers:
            stats = manager.get_statistics(ticker)
            if stats:
                sr = analyzer.find_support_resistance(manager.get_data(ticker))
                
                print(f"\n{ticker}:")
                print(f"  Цена: {stats['avg_price']:.2f} ₽")
                print(f"  Диапазон: {stats['min_price']:.2f} - {stats['max_price']:.2f} ₽")
                
                if sr and sr.get('support') and sr.get('resistance'):
                    print(f"  Поддержка: {sr['support']:.2f} ₽")
                    print(f"  Сопротивление: {sr['resistance']:.2f} ₽")
                    print(f"  Текущая цена: {sr.get('current_price', 'N/A'):.2f} ₽")
        
        print("\n" + "="*70)
        print("✅ ОБНОВЛЕНИЕ И АНАЛИЗ ЗАВЕРШЕНЫ!")
        print("="*70 + "\n")
        
        return 0
    
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        print(f"\n❌ Ошибка: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

