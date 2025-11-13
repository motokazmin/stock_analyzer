"""
Примеры использования StockDataManager
"""

from stock_data_manager import StockDataManager
import logging

logger = logging.getLogger(__name__)


def example_1_simple_download():
    """Пример 1: Загрузка данных для одной акции."""
    print("\n" + "="*60)
    print("ПРИМЕР 1: Простая загрузка данных")
    print("="*60)
    
    manager = StockDataManager()
    
    # Загружаем данные за период
    data = manager.download_stock_data(
        ticker='SBER',
        from_date='2024-01-01',
        to_date='2024-12-31'
    )
    
    print(f"\nЗагружено {len(data)} записей для SBER")
    print(f"Первая дата: {data['DATE'].min()}")
    print(f"Последняя дата: {data['DATE'].max()}")
    print("\nПервые 5 записей:")
    print(data.head())
    
    # Сохраняем в файл
    manager.save_to_csv('SBER', data)


def example_2_update_watchlist():
    """Пример 2: Обновление списка избранных акций."""
    print("\n" + "="*60)
    print("ПРИМЕР 2: Обновление списка акций")
    print("="*60)
    
    manager = StockDataManager()
    
    # Популярные акции Мосбиржи
    watchlist = ['SBER', 'GAZP', 'LKOH', 'PLZL', 'Si']
    
    # Обновляем данные для всех
    results = manager.update_watchlist(watchlist)
    
    # Выводим результаты
    print("\nРезультаты обновления:")
    for ticker, success in results.items():
        status = "✓ ОК" if success else "✗ Ошибка"
        print(f"  {ticker}: {status}")


def example_3_get_statistics():
    """Пример 3: Получение статистики по акции."""
    print("\n" + "="*60)
    print("ПРИМЕР 3: Статистика по акции")
    print("="*60)
    
    manager = StockDataManager()
    
    # Предварительно должны быть загружены данные
    tickers = ['SBER', 'GAZP', 'LKOH']
    
    for ticker in tickers:
        stats = manager.get_statistics(ticker)
        
        if stats:
            print(f"\n{ticker}:")
            print(f"  Всего записей: {stats['total_records']}")
            print(f"  Период: {stats['date_from']} → {stats['date_to']}")
            print(f"  Средняя цена: {stats['avg_price']:.2f} ₽")
            print(f"  Диапазон: {stats['min_price']:.2f} - {stats['max_price']:.2f} ₽")
            print(f"  Объем торгов: {stats['total_volume']:,.0f}")
        else:
            print(f"\n{ticker}: данные не найдены")


def example_4_get_latest_data():
    """Пример 4: Получение последних данных по акции."""
    print("\n" + "="*60)
    print("ПРИМЕР 4: Последние данные по акции")
    print("="*60)
    
    manager = StockDataManager()
    
    df = manager.get_data('SBER')
    
    if df is not None:
        print(f"\nПоследние 10 дней SBER:")
        print(df[['DATE', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']].tail(10))


def example_5_incremental_update():
    """Пример 5: Инкрементальное обновление (только новые данные)."""
    print("\n" + "="*60)
    print("ПРИМЕР 5: Инкрементальное обновление")
    print("="*60)
    
    manager = StockDataManager()
    
    ticker = 'GAZP'
    
    # Первая загрузка
    print(f"\n1. Первичная загрузка {ticker}...")
    manager.update_watchlist([ticker])
    
    stats1 = manager.get_statistics(ticker)
    print(f"   Загружено записей: {stats1.get('total_records', 0)}")
    
    # Вторая загрузка (только новые данные)
    print(f"\n2. Инкрементальное обновление {ticker}...")
    manager.update_watchlist([ticker])
    
    stats2 = manager.get_statistics(ticker)
    new_records = stats2.get('total_records', 0) - stats1.get('total_records', 0)
    print(f"   Добавлено новых записей: {new_records}")
    print(f"   Всего записей: {stats2.get('total_records', 0)}")


if __name__ == "__main__":
    # Раскомментируйте нужный пример для запуска
    
    # example_1_simple_download()
    example_2_update_watchlist()
    # example_3_get_statistics()
    # example_4_get_latest_data()
    # example_5_incremental_update()

