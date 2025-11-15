# 📊 Technical Analysis - Краткая справка

## Быстрый старт

```python
from technical_analysis import TechnicalAnalyzer

analyzer = TechnicalAnalyzer()

# Полный анализ акции
result = analyzer.analyze_stock('SBER')
print(result)
```

## 6 главных функций

### 1. EMA (Экспоненциальное скользящее среднее)

```python
df = analyzer.calculate_ema(df, periods=[20, 50, 200])
```

**Интерпретация:**
- Цена > EMA20 > EMA50 = восходящий тренд ✅
- Цена < EMA20 < EMA50 = нисходящий тренд ✅
- Пересечение EMA = разворот тренда ⚠️

---

### 2. RSI (Индекс относительной силы)

```python
df = analyzer.calculate_rsi(df, period=14)
rsi = df['RSI'].iloc[-1]
```

**Сигналы:**
- **RSI > 70** = перекуплено 🔴 (возможен спад)
- **RSI < 30** = перепродано 🟢 (возможен рост)
- **30-70** = нейтральная зона ⚪

---

### 3. Поддержка/Сопротивление

```python
sr = analyzer.find_support_resistance(df, window=20)

support = sr['support']
resistance = sr['resistance']
```

**Использование:**
- Поддержка = уровень входа в длинную позицию
- Сопротивление = уровень входа в короткую позицию

---

### 4. Тренд

```python
trend = analyzer.detect_trend(df)

# trend['trend'] = 'up' / 'down' / 'sideways'
# trend['strength'] = 'strong' / 'moderate' / 'weak'
# trend['above_ma20'] = True / False
# trend['above_ma50'] = True / False
```

---

### 5. Объемы

```python
vol = analyzer.calculate_volume_profile(df, bins=20)

poc = vol['point_of_control']  # Уровень максимальной активности
avg_volume = vol['avg_volume']
```

---

### 6. Полный анализ

```python
result = analyzer.analyze_stock('SBER')

# Результат содержит:
# - current_price
# - price_change_pct
# - technical_indicators (EMA, RSI)
# - support_resistance
# - trend
# - volume
```

## 🎯 Практические примеры

### Пример 1: Простой торговый сигнал

```python
result = analyzer.analyze_stock('SBER')

rsi = result['technical_indicators']['rsi']
trend = result['trend']['trend']
above_ma20 = result['trend']['above_ma20']

# СИГНАЛ НА ПОКУПКУ
if rsi < 30 and trend == 'up' and above_ma20:
    print("✅ Сигнал на покупку SBER!")
else:
    print("❌ Условия не соблюдены")
```

### Пример 2: Определение уровней для стопов

```python
result = analyzer.analyze_stock('GAZP')

support = result['support_resistance']['support']
resistance = result['support_resistance']['resistance']
current = result['current_price']

# Если идем long
entry = current
take_profit = resistance
stop_loss = support

print(f"Вход: {entry:.2f}")
print(f"Тейк-профит: {take_profit:.2f} (+{(take_profit/entry-1)*100:.2f}%)")
print(f"Стоп-лосс: {stop_loss:.2f} ({(entry/stop_loss-1)*100:.2f}%)")
```

### Пример 3: Сравнение акций

```python
tickers = ['SBER', 'GAZP', 'LKOH']

for ticker in tickers:
    result = analyzer.analyze_stock(ticker)
    
    rsi = result['technical_indicators']['rsi']
    trend = result['trend']['trend']
    
    # Фильтруем по критериям
    if rsi < 50 and trend == 'up':
        print(f"✅ {ticker}: хороший вход")
```

### Пример 4: Анализ объемов

```python
result = analyzer.analyze_stock('NVTK')

vol = result['volume']
recent_avg = vol['avg_volume']
poc = vol['point_of_control']

print(f"Средний объем: {recent_avg:,.0f}")
print(f"Уровень максимальной активности (POC): {poc:.2f}")

if vol['volume_trend'] == 'increasing':
    print("📈 Объемы растут = подтверждение тренда")
else:
    print("📉 Объемы падают = ослабление тренда")
```

## 📋 Матрица сигналов

| Цена | EMA20 | EMA50 | RSI | Тренд | Сигнал |
|------|-------|-------|-----|-------|--------|
| > | > | > | <30 | UP | 🟢 BUY |
| > | > | > | >70 | UP | 🔴 SELL |
| < | < | < | >70 | DOWN | 🟢 SHORT |
| < | < | < | <30 | DOWN | 🔴 COVER |

## 🔧 Установка

```bash
pip install -r requirements.txt
```

## 📖 Полная документация

Смотрите `TECHNICAL_ANALYSIS.md` для подробного описания каждой функции.

## 💡 Советы

1. **Никогда не торгуйте** только по одному индикатору
2. **Используйте несколько** индикаторов вместе
3. **Проверяйте тренд** перед входом в позицию
4. **Используйте стоп-лоссы** на уровнях поддержки
5. **Объемы подтверждают** направление тренда

---

**Готово к использованию!** 🚀

