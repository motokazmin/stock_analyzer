#!/usr/bin/env python3
"""
Демонстрация приоритета конфига при определении уровней S/R.
"""

import json
from technical_analysis import TechnicalAnalyzer
from config_manager import ConfigManager

print("\n" + "="*70)
print("📊 ДЕМОНСТРАЦИЯ ПРИОРИТЕТА КОНФИГА")
print("="*70 + "\n")

# Загружаем конфиг
config = ConfigManager.load_config()

print("📋 Структура конфига:\n")

tickers = ['SBER', 'GAZP', 'LKOH', 'OZON']

for ticker in tickers:
    levels = config['key_levels'].get(ticker, {})
    support = levels.get('support', [])
    resistance = levels.get('resistance', [])
    notes = levels.get('notes', '')
    
    print(f"{ticker}:")
    print(f"  Support:     {support if support else '[] (пусто - будет автоматический расчёт)'}")
    print(f"  Resistance:  {resistance if resistance else '[] (пусто - будет автоматический расчёт)'}")
    print(f"  Notes:       {notes}")
    print()

print("\n" + "-"*70)
print("🔧 КАК ЭТО РАБОТАЕТ:")
print("-"*70 + "\n")

print("""
1. SBER и GAZP:
   ✅ Имеют значения в конфиге
   ➜ Будут использованы РУЧНЫЕ уровни из конфига
   
2. LKOH и остальные:
   ❌ Массивы пусты []
   ➜ Будут использованы АВТОМАТИЧЕСКИ РАССЧИТАННЫЕ уровни

АЛГОРИТМ:
┌─────────────────────────────┐
│ Загрузить данные            │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│ Рассчитать автоматические  │ (всегда)
│ уровни S/R                  │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│ Проверить конфиг            │
└────────────┬────────────────┘
             │
      ┌──────┴──────┐
      ▼             ▼
   ┌─────┐      ┌─────┐
   │ЕСТЬ │      │НЕТ  │
   └──┬──┘      └──┬──┘
      │            │
      ▼            ▼
 ПЕРЕПИСАТЬ    ОСТАВИТЬ
 АВТОМАТИЧ    АВТОМАТИЧ
""")

print("\n" + "-"*70)
print("💡 ДЛЯ ИСПОЛЬЗОВАНИЯ:")
print("-"*70 + "\n")

print("""
Установить ручные уровни для TATN:

from config_manager import ConfigManager

ConfigManager.set_key_levels('TATN', {
    'support': [280, 300],
    'resistance': [350, 380],
    'notes': 'Проверенные уровни'
})

Теперь при анализе TATN будут использованы ваши уровни!
Если хотите вернуться к автоматическому расчёту - просто очистите массивы:

ConfigManager.set_key_levels('TATN', {
    'support': [],
    'resistance': [],
    'notes': 'Рассчитывается автоматически'
})
""")

print("\n" + "="*70)

