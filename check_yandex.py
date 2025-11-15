#!/usr/bin/env python3
"""Проверяем доступность Яндекса на API"""

import requests
import sys

tickers_to_test = ['RUS-YDEX', 'YDEX', 'YNDX', 'YANDEX']

print("\n" + "="*60)
print("🔍 ПРОВЕРКА ЯНДЕКСА НА МОСБИРЖЕ API")
print("="*60 + "\n")

found = False

for ticker in tickers_to_test:
    url = f"https://iss.moex.com/iss/history/engines/stock/markets/shares/securities/{ticker}.json"
    
    try:
        print(f"Проверяю {ticker}...", end=" ")
        r = requests.get(url, timeout=5, params={'limit': 1})
        
        if r.status_code == 200:
            data = r.json()
            
            if 'history' in data:
                records = data['history'].get('data', [])
                if records:
                    print(f"✅ НАЙДЕН! ({len(records)} записей)")
                    found = True
                    print(f"\nРезультат: используйте тикер '{ticker}'")
                    break
                else:
                    print("⚠️ Есть, но нет данных")
            else:
                print("⚠️ Неправильный ответ")
        else:
            print(f"❌ Ошибка {r.status_code}")
            
    except Exception as e:
        print(f"❌ {type(e).__name__}")

if not found:
    print("\n❌ Яндекс не найден ни под одним из тикеров!")
    print("\nВозможные причины:")
    print("1. Акция не торгуется на Мосбирже (может быть на бирже SPYF или другой)")
    print("2. Неправильный тикер")
    print("3. API Мосбиржи в данный момент недоступен")

print("\n" + "="*60 + "\n")

