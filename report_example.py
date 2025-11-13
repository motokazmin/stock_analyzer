"""
Примеры использования модуля report_generator.py
"""

from report_generator import ReportGenerator
from datetime import datetime


def example_1_simple_report():
    """Пример 1: Простой отчёт по акциям."""
    print("\n" + "="*60)
    print("ПРИМЕР 1: Простой еженедельный отчёт")
    print("="*60)

    generator = ReportGenerator()
    
    # Список акций для анализа
    tickers = ['SBER', 'GAZP', 'LKOH']
    
    # Генерируем отчёт
    report = generator.generate_weekly_report(tickers)
    
    # Выводим первую часть
    lines = report.split('\n')
    print('\n'.join(lines[:50]))  # Первые 50 строк
    print("\n... (смотрите полный отчёт в файле)")


def example_2_save_report():
    """Пример 2: Генерация и сохранение отчёта."""
    print("\n" + "="*60)
    print("ПРИМЕР 2: Генерация и сохранение отчёта")
    print("="*60)

    generator = ReportGenerator()
    
    tickers = ['SBER', 'GAZP', 'LKOH', 'NVTK', 'TATN']
    
    # Генерируем и сохраняем
    filepath = generator.generate_and_save(tickers)
    
    if filepath:
        print(f"\n✅ Отчёт сохранён: {filepath}")
        
        # Получаем размер файла
        size = filepath.stat().st_size / 1024  # в KB
        print(f"   Размер: {size:.1f} KB")
        
        # Выводим статистику
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            line_count = content.count('\n')
            print(f"   Строк: {line_count}")


def example_3_custom_analysis():
    """Пример 3: Кастомное имя отчёта."""
    print("\n" + "="*60)
    print("ПРИМЕР 3: Отчёт с кастомным названием")
    print("="*60)

    generator = ReportGenerator()
    
    tickers = ['SBER', 'GAZP']
    
    # Генерируем с кастомным именем
    now = datetime.now()
    custom_name = f"report_top2_{now.strftime('%Y%m%d')}.md"
    
    filepath = generator.generate_and_save(tickers, filename=custom_name)
    
    if filepath:
        print(f"✅ Отчёт сохранён: {filepath}")


def example_4_ranking():
    """Пример 4: Ранжирование акций."""
    print("\n" + "="*60)
    print("ПРИМЕР 4: Ранжирование и скоринг акций")
    print("="*60)

    from technical_analysis import TechnicalAnalyzer
    
    generator = ReportGenerator()
    analyzer = TechnicalAnalyzer()
    
    # Анализируем акции
    tickers = ['SBER', 'GAZP', 'LKOH']
    results = []
    
    for ticker in tickers:
        result = analyzer.analyze_stock(ticker)
        if result:
            results.append(result)
    
    # Ранжируем
    ranked = generator.rank_stocks(results)
    
    print("\nРейтинг акций по скору:")
    print("─" * 60)
    
    for item in ranked:
        ticker = item['ticker']
        rank = item['rank']
        score = item['score']
        price = item['price']
        change = item['price_change']
        
        print(f"{rank}. {ticker:<8} Скор: {score:>3} | Цена: {price:>7.2f} ₽ | {change:>+6.2f}%")
        
        for factor in item['factors'][:2]:  # Первые 2 фактора
            print(f"   └─ {factor}")


def example_5_signals():
    """Пример 5: Анализ сигналов."""
    print("\n" + "="*60)
    print("ПРИМЕР 5: Торговые сигналы")
    print("="*60)

    from technical_analysis import TechnicalAnalyzer
    
    generator = ReportGenerator()
    analyzer = TechnicalAnalyzer()
    
    tickers = ['SBER', 'GAZP', 'LKOH']
    
    print("\nТорговые сигналы:")
    print("─" * 60)
    
    for ticker in tickers:
        result = analyzer.analyze_stock(ticker)
        
        if result:
            signals = generator.find_signals(result)
            
            print(f"\n{ticker}:")
            print(f"  Основной сигнал: {signals['primary']}")
            print(f"  Сила сигнала: {signals['strength']}")
            
            if signals['indicators']:
                print(f"  Индикаторы:")
                for ind in signals['indicators']:
                    print(f"    • {ind}")


def example_6_compare_reports():
    """Пример 6: Сравнение отчётов за разные дни."""
    print("\n" + "="*60)
    print("ПРИМЕР 6: Создание нескольких отчётов")
    print("="*60)

    generator = ReportGenerator()
    tickers = ['SBER', 'GAZP', 'LKOH']
    
    # Генерируем несколько отчётов с разными названиями
    filenames = [
        'report_portfolio_top3.md',
        'report_analysis_detailed.md'
    ]
    
    for filename in filenames:
        filepath = generator.generate_and_save(tickers, filename=filename)
        if filepath:
            print(f"✅ {filename} создан")


def example_7_entry_exit_points():
    """Пример 7: Точки входа/выхода."""
    print("\n" + "="*60)
    print("ПРИМЕР 7: Точки входа и выхода")
    print("="*60)

    from technical_analysis import TechnicalAnalyzer
    
    generator = ReportGenerator()
    analyzer = TechnicalAnalyzer()
    
    ticker = 'SBER'
    result = analyzer.analyze_stock(ticker)
    
    if result:
        print(f"\n{ticker} - Торговый план:")
        print("─" * 60)
        
        current = result['current_price']
        sr = result['support_resistance']
        trend = result['trend']
        
        support = sr.get('support', 0)
        resistance = sr.get('resistance', 0)
        
        print(f"\nТекущая цена: {current:.2f} ₽\n")
        
        # Если восходящий тренд
        if trend.get('trend') == 'up':
            print(f"📈 Восходящий тренд - ДОЛГАЯ позиция\n")
            print(f"Вход:")
            print(f"  • На откате к поддержке: {support:.2f} ₽")
            print(f"    На {(current - support) / current * 100:.1f}% ниже текущей\n")
            
            print(f"Цели прибыли:")
            print(f"  • Сопротивление (1): {resistance:.2f} ₽")
            print(f"    Прибыль: +{(resistance - current) / current * 100:.1f}%\n")
            
            print(f"  • Расширение (2): {resistance + (resistance - support) * 0.5:.2f} ₽")
            print(f"    Прибыль: +{((resistance + (resistance - support) * 0.5) - current) / current * 100:.1f}%\n")
            
            print(f"Стоп-лосс:")
            print(f"  • Жёсткий: {support:.2f} ₽")
            print(f"    Риск: -{(current - support) / current * 100:.1f}%\n")
            
            print(f"  • Мягкий (2%): {current * 0.98:.2f} ₽")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ПРИМЕРЫ РАБОТЫ ГЕНЕРАТОРА ОТЧЁТОВ")
    print("="*60)

    # Раскомментируйте нужные примеры
    example_1_simple_report()
    # example_2_save_report()
    # example_3_custom_analysis()
    # example_4_ranking()
    # example_5_signals()
    # example_6_compare_reports()
    # example_7_entry_exit_points()

