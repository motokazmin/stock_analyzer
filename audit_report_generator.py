"""
Генератор HTML отчёта аудита рекомендаций.

Создаёт красивый интерактивный отчёт с статистикой и результатами.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuditReportGenerator:
    """Генератор HTML отчётов аудита."""
    
    def __init__(self, archive_file: str = "recommendations_archive.json",
                 output_folder: str = "analysis_history"):
        self.archive_file = Path(archive_file)
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
    
    def _load_archive(self) -> Dict:
        """Загружает архив рекомендаций."""
        if self.archive_file.exists():
            with open(self.archive_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"recommendations": []}
    
    def _calculate_stats(self, recs: List[Dict]) -> Dict:
        """Вычисляет статистику."""
        completed = [r for r in recs if r.get("status") == "COMPLETED"]
        failed = [r for r in recs if r.get("status") == "FAILED"]
        active = [r for r in recs if r.get("status") == "ACTIVE"]
        
        profits = [r.get("result", 0) for r in completed + failed if r.get("result") is not None]
        
        return {
            "total": len(recs),
            "completed": len(completed),
            "failed": len(failed),
            "active": len(active),
            "success_rate": round((len(completed) / len(recs) * 100) if recs else 0, 1),
            "avg_profit": round(sum(profits) / len(profits), 2) if profits else 0,
            "max_profit": round(max(profits), 2) if profits and len(profits) > 0 else 0,
            "min_profit": round(min(profits), 2) if profits and len(profits) > 0 else 0
        }
    
    def _get_status_badge(self, status: str) -> str:
        """Возвращает HTML для статуса."""
        badges = {
            "COMPLETED": '<span class="badge badge-success">✅ ВЫПОЛНЕНА</span>',
            "FAILED": '<span class="badge badge-danger">❌ ПРОВАЛЕНА</span>',
            "ACTIVE": '<span class="badge badge-warning">🟡 АКТИВНА</span>',
            "IN_PROGRESS": '<span class="badge badge-info">⏳ В ПРОЦЕССЕ</span>',
            "TARGET1_HIT": '<span class="badge badge-info">🎯 ЦЕЛЬ 1</span>',
            "TARGET2_HIT": '<span class="badge badge-success">🎯🎯 ЦЕЛЬ 2</span>',
            "STOPPED_OUT": '<span class="badge badge-danger">🛑 СТОП</span>',
        }
        return badges.get(status, f'<span class="badge">{status}</span>')
    
    def _get_result_color(self, result_pct: float) -> str:
        """Возвращает цвет для результата."""
        if result_pct is None:
            result_pct = 0
        
        if result_pct > 0:
            return f'<span class="positive">{result_pct:+.2f}%</span>'
        elif result_pct < 0:
            return f'<span class="negative">{result_pct:.2f}%</span>'
        else:
            return '<span class="neutral">0.00%</span>'
    
    def generate_html(self) -> str:
        """Генерирует HTML отчёт."""
        archive = self._load_archive()
        recs = archive.get("recommendations", [])
        stats = self._calculate_stats(recs)
        
        # Группируем по статусам
        completed = [r for r in recs if r.get("status") == "COMPLETED"]
        failed = [r for r in recs if r.get("status") == "FAILED"]
        active = [r for r in recs if r.get("status") == "ACTIVE"]
        
        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Аудит Рекомендаций - {datetime.now().strftime('%d.%m.%Y')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #333;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }}
        
        h1 {{
            color: #1e3c72;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        
        .stat-box h3 {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 8px;
        }}
        
        .stat-box .number {{
            font-size: 2em;
            font-weight: bold;
        }}
        
        section {{
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        section h2 {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            margin: 0;
            font-size: 1.8em;
        }}
        
        .section-content {{
            padding: 30px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        
        .badge-success {{
            background: #dcfce7;
            color: #166534;
        }}
        
        .badge-danger {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .badge-warning {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .badge-info {{
            background: #dbeafe;
            color: #1e40af;
        }}
        
        .positive {{
            color: #22c55e;
            font-weight: bold;
        }}
        
        .negative {{
            color: #ef4444;
            font-weight: bold;
        }}
        
        .neutral {{
            color: #666;
            font-weight: bold;
        }}
        
        .rec-card {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
        }}
        
        .rec-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .ticker {{
            font-size: 1.3em;
            font-weight: bold;
            color: #1e3c72;
        }}
        
        .rec-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            font-size: 0.9em;
        }}
        
        .detail {{
            background: white;
            padding: 10px;
            border-radius: 3px;
            border-left: 3px solid #667eea;
        }}
        
        .detail-label {{
            color: #666;
            font-size: 0.8em;
            font-weight: 600;
        }}
        
        .detail-value {{
            color: #1e3c72;
            font-weight: bold;
            margin-top: 3px;
        }}
        
        footer {{
            background: white;
            padding: 20px;
            text-align: center;
            border-radius: 10px;
            color: #666;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 1.8em;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .rec-details {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Аудит Торговых Рекомендаций</h1>
            <p>📅 Дата отчёта: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            <p>📈 Всего рекомендаций: {stats['total']}</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-box">
                <h3>✅ Выполнено</h3>
                <div class="number">{stats['completed']}</div>
            </div>
            <div class="stat-box">
                <h3>❌ Провалено</h3>
                <div class="number">{stats['failed']}</div>
            </div>
            <div class="stat-box">
                <h3>🟡 Активно</h3>
                <div class="number">{stats['active']}</div>
            </div>
            <div class="stat-box">
                <h3>📈 Процент успеха</h3>
                <div class="number">{stats['success_rate']}%</div>
            </div>
            <div class="stat-box">
                <h3>💰 Средний результат</h3>
                <div class="number">{stats['avg_profit']:+.2f}%</div>
            </div>
            <div class="stat-box">
                <h3>🎯 Максимум</h3>
                <div class="number">{stats['max_profit']:+.2f}%</div>
            </div>
        </div>
        
        <!-- ВЫПОЛНЕННЫЕ -->
        <section>
            <h2>✅ Выполненные рекомендации ({len(completed)})</h2>
            <div class="section-content">
                {self._render_recs_html(completed) if completed else '<p>Нет выполненных рекомендаций</p>'}
            </div>
        </section>
        
        <!-- АКТИВНЫЕ -->
        <section>
            <h2>🟡 Активные рекомендации ({len(active)})</h2>
            <div class="section-content">
                {self._render_recs_html(active) if active else '<p>Нет активных рекомендаций</p>'}
            </div>
        </section>
        
        <!-- ПРОВАЛЕНЫ -->
        <section>
            <h2>❌ Провалены рекомендации ({len(failed)})</h2>
            <div class="section-content">
                {self._render_recs_html(failed) if failed else '<p>Нет провалены рекомендаций</p>'}
            </div>
        </section>
        
        <footer>
            <p>🔍 Аудит создан автоматически системой анализа акций</p>
            <p>📌 Следующий аудит: {(datetime.now()).strftime('%d.%m.%Y')}</p>
        </footer>
    </div>
</body>
</html>"""
        return html
    
    def _render_recs_html(self, recs: List[Dict]) -> str:
        """Рендерит HTML для рекомендаций."""
        html = ""
        for rec in recs:
            result_pct = rec.get("result", 0)
            status = rec.get("status", "UNKNOWN")
            
            html += f"""
            <div class="rec-card">
                <div class="rec-header">
                    <span class="ticker">{rec.get('ticker', 'N/A')}</span>
                    {self._get_status_badge(status)}
                    {self._get_result_color(result_pct)}
                </div>
                <div class="rec-details">
                    <div class="detail">
                        <div class="detail-label">Дата</div>
                        <div class="detail-value">{rec.get('date', 'N/A')[:10]}</div>
                    </div>
                    <div class="detail">
                        <div class="detail-label">Сигнал</div>
                        <div class="detail-value">{rec.get('signal', 'N/A')}</div>
                    </div>
                    <div class="detail">
                        <div class="detail-label">Цена входа</div>
                        <div class="detail-value">{rec.get('entry_price', 0):.2f} ₽</div>
                    </div>
                    <div class="detail">
                        <div class="detail-label">Цель 1 / 2</div>
                        <div class="detail-value">{rec.get('target1', 0):.2f} / {rec.get('target2', 0):.2f} ₽</div>
                    </div>
                    <div class="detail">
                        <div class="detail-label">Стоп-лосс</div>
                        <div class="detail-value">{rec.get('stop_loss', 0):.2f} ₽</div>
                    </div>
                    <div class="detail">
                        <div class="detail-label">RSI / Тренд</div>
                        <div class="detail-value">{rec.get('rsi', 0):.2f} / {rec.get('trend', 'N/A')}</div>
                    </div>
                </div>
                {f'<p style="margin-top: 10px; color: #666; font-size: 0.9em;"><strong>💬</strong> {rec.get("comment", "")}</p>' if rec.get("comment") else ""}
            </div>
            """
        
        return html
    
    def save_report(self):
        """Сохраняет отчёт в HTML файл."""
        html = self.generate_html()
        
        filename = f"AUDIT_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = self.output_folder / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"✅ Отчёт сохранён: {filepath}")
        return str(filepath)


if __name__ == "__main__":
    generator = AuditReportGenerator()
    generator.save_report()
    print("✅ Отчёт аудита создан!")

