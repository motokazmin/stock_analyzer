"""
Тестирование StockDataManager
"""

import sys
from stock_data_manager import StockDataManager
import logging

# Настройка логирования для тестов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_initialization():
    """Тест инициализации менеджера."""
    print("\n" + "="*60)
    print("ТЕСТ 1: Инициализация менеджера")
    print("="*60)
    
    try:
        manager = StockDataManager()
        print("✓ Менеджер успешно инициализирован")
        return True
    except Exception as e:
        print(f"✗ Ошибка при инициализации: {e}")
        return False


def test_single_download():
    """Тест загрузки данных для одной акции."""
    print("\n" + "="*60)
    print("ТЕСТ 2: Загрузка данных одной акции (SBER)")
    print("="*60)
    
    try:
        manager = StockDataManager()
        
        print("Загружаем данные за последний месяц...")
        from datetime import datetime, timedelta
        
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        data = manager.download_stock_data('SBER', from_date, to_date)
        
        if data.empty:
            print("⚠ Данные не загружены (возможна проблема с API)")
            return False
        
        print(f"✓ Загружено {len(data)} записей")
        print(f"  Диапазон: {data['DATE'].min()} - {data['DATE'].max()}")
        print(f"  Колонки: {', '.join(data.columns.tolist())}")
        print(f"\nПервые 3 записи:")
        print(data.head(3).to_string(index=False))
        
        return True
    
    except Exception as e:
        print(f"✗ Ошибка при загрузке: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_save_and_load():
    """Тест сохранения и загрузки данных."""
    print("\n" + "="*60)
    print("ТЕСТ 3: Сохранение и загрузка CSV")
    print("="*60)
    
    try:
        manager = StockDataManager()
        
        # Загружаем данные
        from datetime import datetime, timedelta
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
        
        print("Загружаем данные...")
        data = manager.download_stock_data('GAZP', from_date, to_date)
        
        if data.empty:
            print("⚠ Данные не загружены")
            return False
        
        # Сохраняем
        print("Сохраняем в CSV...")
        success = manager.save_to_csv('GAZP', data)
        
        if not success:
            print("✗ Ошибка при сохранении")
            return False
        
        # Загружаем обратно
        print("Загружаем из CSV...")
        loaded_data = manager.get_data('GAZP')
        
        if loaded_data is None or loaded_data.empty:
            print("✗ Ошибка при загрузке из CSV")
            return False
        
        print(f"✓ Успешно сохранено и загружено {len(loaded_data)} записей")
        print(f"  Файл: stock_data/GAZP_full.csv")
        
        return True
    
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_statistics():
    """Тест получения статистики."""
    print("\n" + "="*60)
    print("ТЕСТ 4: Получение статистики")
    print("="*60)
    
    try:
        manager = StockDataManager()
        
        # Сначала загружаем данные
        print("Загружаем данные для LKOH...")
        from datetime import datetime, timedelta
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        data = manager.download_stock_data('LKOH', from_date, to_date)
        
        if data.empty:
            print("⚠ Данные не загружены")
            return False
        
        manager.save_to_csv('LKOH', data)
        
        # Получаем статистику
        print("Получаем статистику...")
        stats = manager.get_statistics('LKOH')
        
        if not stats:
            print("✗ Не удалось получить статистику")
            return False
        
        print("✓ Статистика получена:")
        print(f"  Тикер: {stats['ticker']}")
        print(f"  Записей: {stats['total_records']}")
        print(f"  Период: {stats['date_from']} - {stats['date_to']}")
        print(f"  Ср. цена: {stats['avg_price']:.2f} ₽")
        print(f"  Диапазон: {stats['min_price']:.2f} - {stats['max_price']:.2f} ₽")
        print(f"  Объем: {stats['total_volume']:,.0f}")
        
        return True
    
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_update_watchlist():
    """Тест обновления списка акций."""
    print("\n" + "="*60)
    print("ТЕСТ 5: Обновление списка акций")
    print("="*60)
    
    try:
        manager = StockDataManager()
        
        tickers = ['NVTK', 'TATN']
        print(f"Обновляем данные для: {', '.join(tickers)}")
        print("(Это может занять время...)\n")
        
        results = manager.update_watchlist(tickers)
        
        print("\nРезультаты:")
        all_success = True
        for ticker, success in results.items():
            status = "✓ ОК" if success else "✗ Ошибка"
            print(f"  {ticker}: {status}")
            all_success = all_success and success
        
        if all_success:
            print("\n✓ Все акции успешно обновлены")
        
        return all_success
    
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Запуск всех тестов."""
    print("\n" + "#"*60)
    print("# ТЕСТИРОВАНИЕ StockDataManager")
    print("#"*60)
    
    tests = [
        ("Инициализация", test_initialization),
        ("Загрузка данных", test_single_download),
        ("Сохранение/Загрузка CSV", test_save_and_load),
        ("Статистика", test_statistics),
        ("Обновление списка", test_update_watchlist),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n✗ Критическая ошибка в тесте '{name}': {e}")
            results[name] = False
    
    # Итоговый отчет
    print("\n" + "="*60)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("="*60)
    
    for name, success in results.items():
        status = "✓ ПРОЙДЕН" if success else "✗ ПРОВАЛЕН"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\nВсего: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("\n✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return 0
    else:
        print(f"\n✗ ПРОВАЛЕНО {total - passed} ТЕСТОВ")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

