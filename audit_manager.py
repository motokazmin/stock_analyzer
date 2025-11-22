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
        
        Проверяет, что рекомендация для этого ticker еще не была добавлена сегодня,
        чтобы избежать дублей.
        
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
        # Проверяем, нет ли уже рекомендации для этого тикера сегодня
        today = datetime.now().date()
        for rec in self.archive["recommendations"]:
            rec_date = pd.to_datetime(rec["date"]).date()
            if rec["ticker"] == ticker and rec_date == today and rec["signal"] == signal:
                logger.info(f"⚠️  Рекомендация {ticker} {signal} уже добавлена сегодня")
                return
        
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
        Проверяет рекомендацию, сравнивая цену в день рекомендации с текущей ценой.
        
        Логика:
        1. Берет цену на дату рекомендации (entry_price)
        2. Берет последнюю доступную цену (текущая)
        3. Проверяет: была ли достигнута цель? сработал ли стоп?
        4. Считает результат в %
        
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
        rec_date_obj = pd.to_datetime(rec["date"]).date()
        
        # Получаем цену входа (на дату рекомендации или максимально близко к ней)
        # Фильтруем по году, чтобы не взять старые данные из прошлого года
        rec_year = rec_date_obj.year
        df_current_year = df[df['DATE'].dt.year == rec_year]
        
        rec_day_data = df_current_year[df_current_year['DATE'].dt.date == rec_date_obj]
        if len(rec_day_data) == 0:
            # Если данных в точный день нет, берём самый близкий день после рекомендации
            rec_day_data = df_current_year[df_current_year['DATE'].dt.date >= rec_date_obj].head(1)
            if len(rec_day_data) == 0:
                return {"status": "NO_DATA", "message": f"Нет данных для {ticker} на {rec_date_obj}"}
        
        entry_price_actual = rec_day_data.iloc[-1]['CLOSE']
        rec_day_actual = rec_day_data.iloc[-1]['DATE'].date()
        
        entry_price = rec.get("entry_price")
        target1 = rec.get("target1")
        target2 = rec.get("target2")
        stop_loss = rec.get("stop_loss")
        
        # Проверяем что все значения заданы
        if not all([entry_price, target1, target2, stop_loss]):
            return {"status": "ERROR", "message": f"Неполные данные рекомендации"}
        
        # Берём ПОСЛЕДНЮЮ доступную цену (сегодня или последний день торговли)
        final_price = df_current_year.iloc[-1]['CLOSE']
        final_date = df_current_year.iloc[-1]['DATE'].date()
        
        # Анализируем все данные от даты рекомендации до сегодня (только текущий год)
        df_period = df_current_year[df_current_year['DATE'].dt.date >= rec_date_obj]
        
        hit_target1 = False
        hit_target2 = False
        hit_stop_loss = False
        max_price = entry_price_actual
        min_price = entry_price_actual
        
        for idx, row in df_period.iterrows():
            high = row['HIGH']
            low = row['LOW']
            
            max_price = max(max_price, high)
            min_price = min(min_price, low)
            
            # Проверяем цели (когда цена впервые достигла уровня)
            if target1 is not None and high >= target1 and not hit_target1:
                hit_target1 = True
            
            if target2 is not None and high >= target2 and not hit_target2:
                hit_target2 = True
            
            # Проверяем стоп (когда цена впервые упала ниже стопа)
            if stop_loss is not None and low <= stop_loss and not hit_stop_loss:
                hit_stop_loss = True
        
        # Считаем результат
        if rec["signal"] == "BUY":
            if hit_stop_loss:
                # Если сработал стоп, результат = убыток до стоп-лосса
                result_pct = ((stop_loss - entry_price) / entry_price) * 100
                status = "STOPPED_OUT"
            elif hit_target2:
                # Если достигнута вторая цель, результат = до второй цели
                result_pct = ((target2 - entry_price) / entry_price) * 100
                status = "TARGET2_HIT"
            elif hit_target1:
                # Если достигнута первая цель, результат = до первой цели
                result_pct = ((target1 - entry_price) / entry_price) * 100
                status = "TARGET1_HIT"
            else:
                # Иначе результат = текущая цена минус цена входа
                result_pct = ((final_price - entry_price) / entry_price) * 100
                status = "IN_PROGRESS"
        else:
            result_pct = 0
            status = "N/A"
        
        days_passed = (final_date - rec_day_actual).days
        
        result = {
            "status": status,
            "ticker": ticker,
            "signal": rec["signal"],
            "rec_date": str(rec_day_actual),
            "entry_price": round(entry_price, 2),
            "entry_price_actual": round(entry_price_actual, 2),
            "current_price": round(final_price, 2),
            "current_date": str(final_date),
            "target1": target1,
            "target2": target2,
            "stop_loss": stop_loss,
            "hit_target1": hit_target1,
            "hit_target2": hit_target2,
            "hit_stop_loss": hit_stop_loss,
            "result_pct": round(result_pct, 2),
            "max_price": round(max_price, 2),
            "min_price": round(min_price, 2),
            "days_passed": days_passed
        }
        
        return result
    
    def audit_all(self) -> List[Dict]:
        """Проверяет все активные рекомендации."""
        active_recs = [r for r in self.archive["recommendations"] 
                      if r["status"] == "ACTIVE"]
        
        results = []
        for rec in active_recs:
            result = self.audit_recommendation(rec["ticker"], rec["date"])
            # Пропускаем ошибки и NO_DATA - это означает, что данных еще нет
            if result.get("status") not in ["ERROR", "NO_DATA"]:
                results.append(result)
                
                # Обновляем статус в архиве (только для проверенных рекомендаций)
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

