"""
Модуль для аудита и проверки точности торговых рекомендаций.

Сравнивает исторические рекомендации с реальными данными:
- Достигнута ли цель?
- Был ли стоп-лосс?
- Какой результат в %?
"""

import json
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuditManager:
    """Менеджер для аудита рекомендаций."""
    
    def __init__(self, data_folder: str = "stock_data", 
                 archive_file: str = "recommendations_archive.json"):
        """
        Инициализация.
        
        Args:
            data_folder: папка с CSV данными
            archive_file: файл архива рекомендаций
        """
        self.data_folder = Path(data_folder)
        self.archive_file = Path(archive_file)
        self.archive = self._load_archive()
    
    def _load_archive(self) -> Dict:
        """Загружает архив рекомендаций."""
        if self.archive_file.exists():
            with open(self.archive_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"recommendations": []}
    
    def save_archive(self):
        """Сохраняет архив рекомендаций."""
        with open(self.archive_file, 'w', encoding='utf-8') as f:
            json.dump(self.archive, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Архив сохранён: {self.archive_file}")
    
    def add_recommendation(self, ticker: str, signal: str, 
                         entry_price: float, target1: float, target2: float,
                         stop_loss: float, rsi: float, trend: str,
                         comment: str = ""):
        """
        Добавляет новую рекомендацию в архив.
        
        Args:
            ticker: тикер акции
            signal: BUY/HOLD/SELL
            entry_price: цена входа
            target1: первая цель (50% позиции)
            target2: вторая цель (50% позиции)
            stop_loss: стоп-лосс
            rsi: текущий RSI
            trend: тренд (UP/DOWN/SIDEWAYS)
            comment: комментарий
        """
        rec = {
            "date": datetime.now().isoformat(),
            "ticker": ticker,
            "signal": signal,
            "entry_price": entry_price,
            "target1": target1,
            "target2": target2,
            "stop_loss": stop_loss,
            "rsi": rsi,
            "trend": trend,
            "comment": comment,
            "status": "ACTIVE",  # ACTIVE, COMPLETED, FAILED, PENDING
            "result": None  # результат в %
        }
        self.archive["recommendations"].append(rec)
        self.save_archive()
        logger.info(f"✅ Добавлена рекомендация: {ticker} {signal}")
    
    def audit_recommendation(self, ticker: str, rec_date: str) -> Dict:
        """
        Проверяет рекомендацию.
        
        Args:
            ticker: тикер акции
            rec_date: дата рекомендации (ISO format)
            
        Returns:
            Результат аудита
        """
        # Загружаем CSV данные
        csv_path = self.data_folder / f"{ticker}_full.csv"
        if not csv_path.exists():
            return {"status": "ERROR", "message": f"CSV не найден: {ticker}"}
        
        df = pd.read_csv(csv_path)
        df['DATE'] = pd.to_datetime(df['DATE'])
        
        # Находим рекомендацию
        rec = None
        for r in self.archive["recommendations"]:
            if r["ticker"] == ticker and r["date"].split('T')[0] == rec_date.split('T')[0]:
                rec = r
                break
        
        if not rec:
            return {"status": "ERROR", "message": f"Рекомендация не найдена"}
        
        # Парсим дату рекомендации
        rec_datetime = pd.to_datetime(rec["date"]).date()
        
        # Берём данные после даты рекомендации
        df_after = df[df['DATE'].dt.date > rec_datetime]
        
        if len(df_after) == 0:
            return {
                "status": "NO_DATA",
                "message": "Нет данных после рекомендации",
                "ticker": ticker
            }
        
        entry_price = rec["entry_price"]
        target1 = rec["target1"]
        target2 = rec["target2"]
        stop_loss = rec["stop_loss"]
        
        # Анализируем каждый день
        hit_target1 = False
        hit_target2 = False
        hit_stop_loss = False
        max_price = 0
        min_price = float('inf')
        final_price = df_after.iloc[-1]['CLOSE']
        
        for idx, row in df_after.iterrows():
            close = row['CLOSE']
            high = row['HIGH']
            low = row['LOW']
            date = row['DATE'].date()
            
            max_price = max(max_price, high)
            min_price = min(min_price, low)
            
            # Проверяем цели
            if high >= target1 and not hit_target1:
                hit_target1 = True
                target1_date = date
            
            if high >= target2 and not hit_target2:
                hit_target2 = True
                target2_date = date
            
            # Проверяем стоп
            if low <= stop_loss and not hit_stop_loss:
                hit_stop_loss = True
                stop_loss_date = date
        
        # Считаем результат
        if rec["signal"] == "BUY":
            if hit_stop_loss:
                result_pct = ((stop_loss - entry_price) / entry_price) * 100
                status = "STOPPED_OUT"
            elif hit_target1 and hit_target2:
                result_pct = ((target2 - entry_price) / entry_price) * 100
                status = "TARGET2_HIT"
            elif hit_target1:
                result_pct = ((target1 - entry_price) / entry_price) * 100
                status = "TARGET1_HIT"
            else:
                result_pct = ((final_price - entry_price) / entry_price) * 100
                status = "IN_PROGRESS"
        else:
            result_pct = 0
            status = "N/A"
        
        result = {
            "status": status,
            "ticker": ticker,
            "signal": rec["signal"],
            "entry_price": entry_price,
            "current_price": final_price,
            "target1": target1,
            "target2": target2,
            "stop_loss": stop_loss,
            "hit_target1": hit_target1,
            "hit_target2": hit_target2,
            "hit_stop_loss": hit_stop_loss,
            "result_pct": round(result_pct, 2),
            "max_price": round(max_price, 2),
            "min_price": round(min_price, 2),
            "days_passed": len(df_after)
        }
        
        return result
    
    def audit_all(self) -> List[Dict]:
        """Проверяет все активные рекомендации."""
        active_recs = [r for r in self.archive["recommendations"] 
                      if r["status"] == "ACTIVE"]
        
        results = []
        for rec in active_recs:
            result = self.audit_recommendation(rec["ticker"], rec["date"])
            if result.get("status") != "ERROR":
                results.append(result)
                
                # Обновляем статус в архиве
                if result["status"] == "TARGET2_HIT":
                    rec["status"] = "COMPLETED"
                    rec["result"] = result["result_pct"]
                elif result["status"] == "STOPPED_OUT":
                    rec["status"] = "FAILED"
                    rec["result"] = result["result_pct"]
        
        self.save_archive()
        return results
    
    def get_statistics(self) -> Dict:
        """Вычисляет статистику по всем рекомендациям."""
        all_recs = self.archive["recommendations"]
        
        total = len(all_recs)
        completed = len([r for r in all_recs if r["status"] == "COMPLETED"])
        failed = len([r for r in all_recs if r["status"] == "FAILED"])
        active = len([r for r in all_recs if r["status"] == "ACTIVE"])
        
        profits = [r["result"] for r in all_recs if r["result"] is not None]
        
        stats = {
            "total_recommendations": total,
            "completed": completed,
            "failed": failed,
            "active": active,
            "success_rate": round((completed / total * 100) if total > 0 else 0, 2),
            "avg_profit": round(sum(profits) / len(profits), 2) if profits else 0,
            "max_profit": round(max(profits), 2) if profits else 0,
            "min_profit": round(min(profits), 2) if profits else 0
        }
        
        return stats


if __name__ == "__main__":
    # Тестирование
    audit = AuditManager()
    
    # Пример: добавляем рекомендацию
    # audit.add_recommendation(
    #     ticker="SBER",
    #     signal="BUY",
    #     entry_price=297.44,
    #     target1=324.97,
    #     target2=349.02,
    #     stop_loss=276.88,
    #     rsi=68.96,
    #     trend="UP",
    #     comment="Восходящий тренд"
    # )
    
    # Проверяем все рекомендации
    results = audit.audit_all()
    print(f"\n✅ Проверено рекомендаций: {len(results)}")
    
    # Выводим статистику
    stats = audit.get_statistics()
    print(f"\n📊 Статистика:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

