"""
Примеры использования модуля technical_analysis.py
"""

import pandas as pd
from technical_analysis import TechnicalAnalyzer
import json


def example_1_load_and_analyze():
    """Пример 1: Загрузка и полный анализ одной акции."""
    print("\n" + "="*60)
    print("ПРИМЕР 1: Полный анализ одной акции")
    print("="*60)

    analyzer = TechnicalAnalyzer()

    # Анализ SBER
    result = analyzer.analyze_stock('SBER')

    if result:
        print(f"\n{result['ticker']} - Полный анализ")
        print(f"{'─'*60}")
        print(f"Цена: {result['current_price']:.2f} ₽")
        print(f"Изменение: {result['price_change']:+.2f} ({result['price_change_pct']:+.2f}%)")
        print(f"Данных: {result['data_points']} записей ({result['date_from']} - {result['date_to']})")

        print(f"\nТехнические индикаторы:")
        ind = result['technical_indicators']
        print(f"  EMA 20:  {ind['ema_20']:.2f}" if ind['ema_20'] else "  EMA 20:  N/A")
        print(f"  EMA 50:  {ind['ema_50']:.2f}" if ind['ema_50'] else "  EMA 50:  N/A")
        print(f"  EMA 200: {ind['ema_200']:.2f}" if ind['ema_200'] else "  EMA 200: N/A")
        print(f"  RSI:     {ind['rsi']:.2f} ({ind['rsi_signal']})" if ind['rsi'] else "  RSI:     N/A")

        print(f"\nТренд анализ:")
        trend = result['trend']
        if trend:
            print(f"  Направление: {trend['trend'].upper()}")
            print(f"  Сила: {trend['strength']}")
            print(f"  Выше MA20: {'Да' if trend['above_ma20'] else 'Нет'}")
            print(f"  Выше MA50: {'Да' if trend['above_ma50'] else 'Нет'}")

        print(f"\nУровни поддержки/сопротивления:")
        sr = result['support_resistance']
        if sr and sr.get('support'):
            print(f"  Поддержка: {sr['support']:.2f}")
            print(f"  Сопротивление: {sr['resistance']:.2f}")
            print(f"  Диапазон: {sr['resistance'] - sr['support']:.2f}")


def example_2_ema_calculation():
    """Пример 2: Расчет различных EMA."""
    print("\n" + "="*60)
    print("ПРИМЕР 2: Расчет EMA (20, 50, 200)")
    print("="*60)

    try:
        df = pd.read_csv('stock_data/GAZP_full.csv', parse_dates=['DATE'])

        analyzer = TechnicalAnalyzer()
        df = analyzer.calculate_ema(df, periods=[20, 50, 200])

        print(f"\nПоследние 5 дней GAZP:")
        print(df[['DATE', 'CLOSE', 'EMA_20', 'EMA_50', 'EMA_200']].tail(5).to_string(index=False))

        # Анализ позиции цены
        close = df['CLOSE'].iloc[-1]
        ema20 = df['EMA_20'].iloc[-1]
        ema50 = df['EMA_50'].iloc[-1]
        ema200 = df['EMA_200'].iloc[-1]

        print(f"\nПозиция цены относительно EMA:")
        print(f"  Цена: {close:.2f}")
        print(f"  EMA 20: {ema20:.2f} ({'+' if close > ema20 else '-'} {abs(close - ema20):.2f})")
        print(f"  EMA 50: {ema50:.2f} ({'+' if close > ema50 else '-'} {abs(close - ema50):.2f})")
        print(f"  EMA 200: {ema200:.2f} ({'+' if close > ema200 else '-'} {abs(close - ema200):.2f})")

    except Exception as e:
        print(f"Ошибка: {e}")


def example_3_rsi_analysis():
    """Пример 3: Анализ RSI."""
    print("\n" + "="*60)
    print("ПРИМЕР 3: Анализ RSI (индекс относительной силы)")
    print("="*60)

    try:
        df = pd.read_csv('stock_data/LKOH_full.csv', parse_dates=['DATE'])

        analyzer = TechnicalAnalyzer()
        df = analyzer.calculate_rsi(df, period=14)

        print(f"\nПоследние 10 дней LKOH:")
        print(df[['DATE', 'CLOSE', 'RSI']].tail(10).to_string(index=False))

        # RSI интерпретация
        rsi = df['RSI'].iloc[-1]
        print(f"\nПоследнее значение RSI: {rsi:.2f}")

        if rsi > 70:
            signal = "🔴 ПЕРЕКУПЛЕНО (overbought)"
        elif rsi < 30:
            signal = "🟢 ПЕРЕПРОДАНО (oversold)"
        elif rsi > 60:
            signal = "🟡 Сильный восходящий тренд"
        elif rsi < 40:
            signal = "🟡 Сильный нисходящий тренд"
        else:
            signal = "⚪ Нейтральная зона"

        print(f"Сигнал: {signal}")

        # История
        print(f"\nЭкстремумы за период:")
        print(f"  Макс RSI: {df['RSI'].max():.2f}")
        print(f"  Мин RSI: {df['RSI'].min():.2f}")
        print(f"  Средн RSI: {df['RSI'].mean():.2f}")

    except Exception as e:
        print(f"Ошибка: {e}")


def example_4_trend_detection():
    """Пример 4: Определение тренда."""
    print("\n" + "="*60)
    print("ПРИМЕР 4: Определение тренда")
    print("="*60)

    try:
        tickers = ['SBER', 'GAZP', 'LKOH']

        analyzer = TechnicalAnalyzer()

        for ticker in tickers:
            df = pd.read_csv(f'stock_data/{ticker}_full.csv', parse_dates=['DATE'])
            trend = analyzer.detect_trend(df)

            if trend:
                symbol = "📈" if trend['trend'] == 'up' else "📉" if trend['trend'] == 'down' else "➡️"
                print(f"\n{ticker} {symbol}")
                print(f"  Тренд: {trend['trend'].upper()}")
                print(f"  Сила: {trend['strength'].upper()}")
                print(f"  Цена: {trend['current_price']:.2f}")
                print(f"  MA20: {trend['ma_20']:.2f} ({'выше' if trend['above_ma20'] else 'ниже'})")
                print(f"  MA50: {trend['ma_50']:.2f} ({'выше' if trend['above_ma50'] else 'ниже'})")

    except Exception as e:
        print(f"Ошибка: {e}")


def example_5_support_resistance():
    """Пример 5: Поддержка и сопротивление."""
    print("\n" + "="*60)
    print("ПРИМЕР 5: Уровни поддержки и сопротивления")
    print("="*60)

    try:
        df = pd.read_csv('stock_data/SBER_full.csv', parse_dates=['DATE'])

        analyzer = TechnicalAnalyzer()
        sr = analyzer.find_support_resistance(df, window=20)

        if sr:
            print(f"\nSBER - Уровни S/R:")
            print(f"  Поддержка: {sr['support']:.2f}")
            print(f"  Сопротивление: {sr['resistance']:.2f}")
            print(f"  Расстояние: {sr['resistance'] - sr['support']:.2f}")
            print(f"  Найдено уровней поддержки: {sr['support_levels_count']}")
            print(f"  Найдено уровней сопротивления: {sr['resistance_levels_count']}")

            current_price = df['CLOSE'].iloc[-1]
            to_resistance = sr['resistance'] - current_price
            to_support = current_price - sr['support']

            print(f"\nРасстояния:")
            print(f"  До сопротивления: {to_resistance:.2f} ({to_resistance/current_price*100:.2f}%)")
            print(f"  До поддержки: {to_support:.2f} ({to_support/current_price*100:.2f}%)")

    except Exception as e:
        print(f"Ошибка: {e}")


def example_6_volume_analysis():
    """Пример 6: Анализ объемов."""
    print("\n" + "="*60)
    print("ПРИМЕР 6: Анализ объемов")
    print("="*60)

    try:
        df = pd.read_csv('stock_data/NVTK_full.csv', parse_dates=['DATE'])

        analyzer = TechnicalAnalyzer()
        vol = analyzer.calculate_volume_profile(df, bins=20)

        if vol:
            print(f"\nNVTK - Профиль объемов:")
            print(f"  Всего объема: {vol['total_volume']:,.0f}")
            print(f"  Средний объем: {vol['avg_volume']:,.0f}")
            print(f"  Макс объем: {vol['max_volume']:,.0f}")
            print(f"  Мин объем: {vol['min_volume']:,.0f}")
            print(f"  Point of Control: {vol['point_of_control']:.2f}")
            print(f"  Тренд объема: {vol['volume_trend']}")

            # Соотношение последнего объема к среднему
            recent_vol = df['VOLUME'].tail(5).mean()
            ratio = recent_vol / vol['avg_volume']
            print(f"\nПоследние объемы (5 дней):")
            print(f"  Средний: {recent_vol:,.0f}")
            print(f"  К историческому: {ratio:.2f}x")

    except Exception as e:
        print(f"Ошибка: {e}")


def example_7_compare_analysis():
    """Пример 7: Сравнение нескольких акций."""
    print("\n" + "="*60)
    print("ПРИМЕР 7: Сравнение технического анализа")
    print("="*60)

    tickers = ['SBER', 'GAZP', 'LKOH']
    analyzer = TechnicalAnalyzer()

    results = []

    for ticker in tickers:
        result = analyzer.analyze_stock(ticker)
        if result:
            results.append({
                'Тикер': ticker,
                'Цена': f"{result['current_price']:.2f}",
                'Изменение': f"{result['price_change_pct']:+.2f}%",
                'Тренд': result['trend'].get('trend', 'N/A').upper() if result['trend'] else 'N/A',
                'RSI': f"{result['technical_indicators']['rsi']:.2f}" if result['technical_indicators']['rsi'] else 'N/A',
                'EMA20 > EMA50': 'Да' if (result['technical_indicators']['ema_20'] and 
                                         result['technical_indicators']['ema_50'] and
                                         result['technical_indicators']['ema_20'] > result['technical_indicators']['ema_50']) else 'Нет'
            })

    if results:
        df_results = pd.DataFrame(results)
        print("\nТеханализ по акциям:")
        print(df_results.to_string(index=False))


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ПРИМЕРЫ ТЕХНИЧЕСКОГО АНАЛИЗА")
    print("="*60)

    # Раскомментируйте нужные примеры
    example_1_load_and_analyze()
    # example_2_ema_calculation()
    # example_3_rsi_analysis()
    # example_4_trend_detection()
    # example_5_support_resistance()
    # example_6_volume_analysis()
    # example_7_compare_analysis()

