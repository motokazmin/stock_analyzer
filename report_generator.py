"""
Генератор markdown-отчётов для технического анализа акций.

Создаёт красивые еженедельные отчёты с рейтингом, сигналами и подробным анализом.
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

from technical_analysis import TechnicalAnalyzer
from audit_manager import AuditManager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Генератор отчётов для технического анализа."""

    def __init__(self, reports_dir: str = "reports"):
        """
        Инициализация генератора.

        Args:
            reports_dir: Директория для сохранения отчётов
        """
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        self.analyzer = TechnicalAnalyzer()
        self.audit = AuditManager()  # ← добавляем аудит менеджер
        logger.info(f"Директория отчётов: {self.reports_dir}")

    @staticmethod
    def find_signals(analysis_result: Dict) -> Dict[str, str]:
        """
        Находит торговые сигналы на основе анализа.

        Args:
            analysis_result: Результат анализа от TechnicalAnalyzer

        Returns:
            Dict с сигналами и их описаниями
        """
        signals = {
            'primary': None,
            'strength': None,
            'indicators': [],
            'conditions': []
        }

        if not analysis_result or not analysis_result.get('technical_indicators'):
            return signals

        rsi = analysis_result['technical_indicators'].get('rsi')
        trend = analysis_result['trend']
        price_change = analysis_result.get('price_change_pct', 0)

        # Проверяем условия
        if trend and trend.get('above_ma20') and trend.get('above_ma50'):
            signals['conditions'].append('Цена выше обоих МА')

        if rsi and rsi < 30:
            signals['indicators'].append('🟢 RSI < 30 (перепродано)')
        elif rsi and rsi > 70:
            signals['indicators'].append('🔴 RSI > 70 (перекуплено)')
        elif rsi and 40 < rsi < 60:
            signals['indicators'].append('⚪ RSI нейтральный')

        if trend:
            if trend.get('trend') == 'up' and trend.get('strength') == 'strong':
                signals['conditions'].append('Сильный восходящий тренд')
            elif trend.get('trend') == 'down' and trend.get('strength') == 'strong':
                signals['conditions'].append('Сильный нисходящий тренд')

        # Определяем основной сигнал
        if rsi and rsi < 30 and trend and trend.get('trend') == 'up':
            signals['primary'] = '🟢 ПОКУПКА'
            signals['strength'] = 'strong'
        elif rsi and rsi > 70 and trend and trend.get('trend') == 'up':
            signals['primary'] = '🟡 ОСТОРОЖНОСТЬ'
            signals['strength'] = 'moderate'
        elif rsi and rsi > 70 and trend and trend.get('trend') == 'down':
            signals['primary'] = '🔴 ПРОДАЖА'
            signals['strength'] = 'strong'
        elif rsi and rsi < 30 and trend and trend.get('trend') == 'down':
            signals['primary'] = '🟡 ОСТОРОЖНОСТЬ'
            signals['strength'] = 'moderate'
        else:
            signals['primary'] = '⚪ НЕЙТРАЛЬНО'
            signals['strength'] = 'weak'

        return signals

    @staticmethod
    def rank_stocks(analysis_results: List[Dict]) -> List[Dict]:
        """
        Ранжирует акции по качеству сигнала.

        Args:
            analysis_results: Список результатов анализа

        Returns:
            Отсортированный список с рейтингом
        """
        ranked = []

        for result in analysis_results:
            if not result:
                continue

            score = 0
            factors = []

            # Тренд (макс 40 баллов)
            trend = result.get('trend', {})
            if trend.get('trend') == 'up':
                if trend.get('strength') == 'strong':
                    score += 40
                    factors.append('Сильный восход. тренд (+40)')
                else:
                    score += 25
                    factors.append('Умеренный восход. тренд (+25)')
            elif trend.get('trend') == 'down':
                if trend.get('strength') == 'strong':
                    score -= 20
                    factors.append('Сильный нисход. тренд (-20)')

            # RSI (макс 30 баллов)
            rsi = result.get('technical_indicators', {}).get('rsi')
            if rsi:
                if 30 < rsi < 70:
                    score += 20
                    factors.append('RSI нейтральный (+20)')
                elif rsi < 30:
                    score += 30
                    factors.append('RSI низкий - сигнал покупки (+30)')
                elif rsi > 70:
                    score -= 15
                    factors.append('RSI высокий - риск (+15)')

            # Цена выше МА (макс 20 баллов)
            if trend.get('above_ma20') and trend.get('above_ma50'):
                score += 20
                factors.append('Цена выше MA20 и MA50 (+20)')

            # Объёмы (макс 10 баллов)
            volume = result.get('volume', {})
            if volume.get('volume_trend') == 'increasing':
                score += 10
                factors.append('Растущие объёмы (+10)')

            ranked.append({
                'ticker': result.get('ticker'),
                'score': score,
                'price': result.get('current_price'),
                'price_change': result.get('price_change_pct'),
                'rsi': rsi,
                'trend': trend.get('trend'),
                'factors': factors,
                'full_result': result,
                'is_excluded': result.get('is_excluded', False),  # ← ДОБАВЛЯЕМ!
                'excluded_reason': result.get('excluded_reason', None)  # ← ДОБАВЛЯЕМ!
            })

        # Сортируем по скору (по убыванию)
        ranked.sort(key=lambda x: x['score'], reverse=True)

        # Присваиваем рейтинг
        for idx, item in enumerate(ranked, 1):
            item['rank'] = idx

        return ranked

    def _format_entry_points(self, analysis_result: Dict) -> str:
        """Форматирует точки входа."""
        sr = analysis_result.get('support_resistance', {})
        trend = analysis_result.get('trend', {})
        current = analysis_result.get('current_price', 0)
        rsi = analysis_result.get('technical_indicators', {}).get('rsi')

        text = "### Точки входа\n\n"

        if trend and trend.get('trend') == 'up':
            support = sr.get('support')
            if support:
                text += f"**На откате к поддержке:** {support:.2f}\n"
                text += f"  - На {(current - support) / current * 100:.1f}% ниже текущей цены\n\n"

        if rsi and rsi > 70:
            text += "**На коррекции:** дождаться RSI < 50\n\n"

        return text

    def _format_take_profit(self, analysis_result: Dict) -> str:
        """Форматирует цели прибыли."""
        sr = analysis_result.get('support_resistance', {})
        current = analysis_result.get('current_price', 0)

        text = "### Цели прибыли\n\n"

        resistance = sr.get('resistance')
        if resistance:
            gain = (resistance - current) / current * 100
            text += f"**Первая цель (Сопротивление):** {resistance:.2f} (+{gain:.1f}%)\n\n"

        # Вторая цель - на 50% выше сопротивления
        if resistance:
            second_target = resistance + (resistance - sr.get('support', resistance)) * 0.5
            gain = (second_target - current) / current * 100
            text += f"**Вторая цель:** {second_target:.2f} (+{gain:.1f}%)\n\n"

        return text

    def _format_stop_loss(self, analysis_result: Dict) -> str:
        """Форматирует стоп-лоссы."""
        sr = analysis_result.get('support_resistance', {})
        current = analysis_result.get('current_price', 0)

        text = "### Стоп-лосс\n\n"

        support = sr.get('support')
        if support:
            loss = (current - support) / current * 100
            text += f"**На уровне поддержки:** {support:.2f} (-{loss:.1f}%)\n\n"

        # Альтернативный стоп - на 2% ниже
        alt_stop = current * 0.98
        text += f"**Агрессивный стоп:** {alt_stop:.2f} (-2%)\n\n"

        return text

    def generate_detailed_analysis(self, analysis_result: Dict) -> str:
        """
        Генерирует детальный анализ для одной акции.

        Args:
            analysis_result: Результат анализа

        Returns:
            Markdown текст анализа
        """
        ticker = analysis_result.get('ticker', 'N/A')
        text = f"## {ticker} - Детальный анализ\n\n"

        # Базовая информация
        text += "### Базовая информация\n\n"
        text += f"- **Текущая цена:** {analysis_result.get('current_price', 0):.2f} ₽\n"
        text += f"- **Изменение:** {analysis_result.get('price_change', 0):+.2f} ({analysis_result.get('price_change_pct', 0):+.2f}%)\n"
        text += f"- **Период:** {analysis_result.get('date_from')} - {analysis_result.get('date_to')}\n"
        text += f"- **Данных:** {analysis_result.get('data_points')} дней\n\n"

        # Сигнал
        signals = self.find_signals(analysis_result)
        text += f"### Сигнал\n\n"
        text += f"**{signals['primary']}** ({signals['strength']})\n\n"
        if signals['indicators']:
            for indicator in signals['indicators']:
                text += f"- {indicator}\n"
        text += "\n"

        # Технические индикаторы
        text += "### Технические индикаторы\n\n"
        ind = analysis_result.get('technical_indicators', {})
        text += f"- **EMA 20:** {ind.get('ema_20', 'N/A'):.2f}\n" if ind.get('ema_20') else ""
        text += f"- **EMA 50:** {ind.get('ema_50', 'N/A'):.2f}\n" if ind.get('ema_50') else ""
        text += f"- **EMA 200:** {ind.get('ema_200', 'N/A'):.2f}\n" if ind.get('ema_200') else ""
        text += f"- **RSI (14):** {ind.get('rsi', 'N/A'):.2f} ({ind.get('rsi_signal', 'N/A')})\n" if ind.get('rsi') else ""
        text += "\n"

        # Тренд анализ
        text += "### Анализ тренда\n\n"
        trend = analysis_result.get('trend', {})
        if trend:
            symbol = "📈" if trend.get('trend') == 'up' else "📉" if trend.get('trend') == 'down' else "➡️"
            text += f"- **Тренд:** {symbol} {trend.get('trend', 'N/A').upper()}\n"
            text += f"- **Сила:** {trend.get('strength', 'N/A').upper()}\n"
            text += f"- **Выше MA20:** {'✅ Да' if trend.get('above_ma20') else '❌ Нет'}\n"
            text += f"- **Выше MA50:** {'✅ Да' if trend.get('above_ma50') else '❌ Нет'}\n"
            text += f"- **MA20:** {trend.get('ma_20', 'N/A'):.2f}\n"
            text += f"- **MA50:** {trend.get('ma_50', 'N/A'):.2f}\n"
            text += "\n"

        # Поддержка/сопротивление
        text += "### Уровни поддержки и сопротивления\n\n"
        sr = analysis_result.get('support_resistance', {})
        if sr:
            text += f"- **Поддержка:** {sr.get('support', 'N/A'):.2f}\n"
            text += f"- **Сопротивление:** {sr.get('resistance', 'N/A'):.2f}\n"
            text += f"- **Расстояние:** {sr.get('resistance', 0) - sr.get('support', 0):.2f}\n"
            text += "\n"

        # Анализ объёмов
        text += "### Анализ объёмов\n\n"
        vol = analysis_result.get('volume', {})
        if vol:
            text += f"- **Средний объём:** {vol.get('avg_volume', 0):,.0f}\n"
            text += f"- **Point of Control:** {vol.get('point_of_control', 'N/A'):.2f}\n"
            text += f"- **Тренд объёма:** {vol.get('volume_trend', 'N/A')}\n"
            text += "\n"

        # Точки входа
        text += self._format_entry_points(analysis_result)

        # Цели прибыли
        text += self._format_take_profit(analysis_result)

        # Стоп-лосс
        text += self._format_stop_loss(analysis_result)

        # Выводы
        text += "### Вывод\n\n"
        if signals['primary'] == '🟢 ПОКУПКА':
            text += "✅ **Рекомендация:** Подходит для долгосрочного входа.\n"
        elif signals['primary'] == '🔴 ПРОДАЖА':
            text += "⛔ **Рекомендация:** Высокий риск. Избегать покупки.\n"
        else:
            text += "⚠️ **Рекомендация:** Ожидать более четких сигналов.\n"

        text += "\n---\n\n"

        return text

    def generate_weekly_report(self, tickers: List[str]) -> str:
        """
        Генерирует еженедельный отчёт по акциям.

        Args:
            tickers: Список тикеров для анализа

        Returns:
            Markdown текст отчёта
        """
        logger.info(f"Генерируем отчёт для {len(tickers)} акций")

        # Анализируем все акции
        analysis_results = []
        for ticker in tickers:
            try:
                result = self.analyzer.analyze_stock(ticker)
                if result:
                    analysis_results.append(result)
            except Exception as e:
                logger.error(f"Ошибка при анализе {ticker}: {e}")

        if not analysis_results:
            logger.error("Не удалось проанализировать акции")
            return ""

        # 🚨 ФИЛЬТРУЕМ ложные восстановления (отскоки от дна)
        # Используем профессиональный анализ с ta-library (ADX, MACD, OBV, RSI, BBANDS)
        filtered_results = []
        for item in analysis_results:
            ticker = item.get('ticker', 'N/A')
            item['is_excluded'] = False
            item['excluded_reason'] = None
            
            # Загружаем данные для проверки на ложный отскок
            try:
                from pathlib import Path
                data_file = Path("stock_data") / f"{ticker}_full.csv"
                
                if data_file.exists():
                    df = pd.read_csv(data_file)
                    df['DATE'] = pd.to_datetime(df['DATE'])
                    
                    if df is not None and len(df) > 0:
                        # Проверяем на ложный отскок
                        is_false, reasons = self.analyzer.is_false_recovery(df)
                        
                        if is_false:
                            logger.warning(f"⚠️  {ticker}: исключена из BUY - ложный отскок")
                            item['is_excluded'] = True
                            item['excluded_reason'] = "; ".join(reasons)
                            logger.info(f"    Причины: {item['excluded_reason']}")
                    
            except Exception as e:
                logger.debug(f"Не удалось проверить {ticker} на ложный отскок: {e}")
            
            filtered_results.append(item)

        # Ранжируем акции
        ranked = self.rank_stocks(filtered_results)

        # Начинаем отчёт
        now = datetime.now()
        date_str = now.strftime('%d.%m.%Y')
        week_start = (now - timedelta(days=now.weekday())).strftime('%d.%m.%Y')
        week_end = now.strftime('%d.%m.%Y')

        report = f"# Еженедельный анализ акций\n\n"
        report += f"**Дата:** {date_str}  \n"
        report += f"**Неделя:** {week_start} - {week_end}  \n"
        report += f"**Проанализировано акций:** {len(analysis_results)}\n\n"

        # Таблица рейтинга
        report += "## 🏆 Рейтинг акций\n\n"
        report += "| # | Тикер | Цена | Изм% | RSI | Тренд | Сигнал | Скор | Комментарий |\n"
        report += "|---|-------|------|------|-----|-------|--------|------|-------------|\n"

        for item in ranked:
            # 🚨 ПРОПУСКАЕМ исключённые акции
            if item.get('is_excluded', False):
                continue
            
            rank = item['rank']
            ticker = item['ticker']
            price = f"{item['price']:.2f}"
            change = f"{item['price_change']:+.1f}%"
            rsi = f"{item['rsi']:.0f}" if item['rsi'] else "N/A"
            trend = item['trend'].upper() if item['trend'] else "N/A"
            score = item['score']

            # Определяем сигнал по скору
            if score >= 60:
                signal = "🟢 BUY"
            elif score <= -10:
                signal = "🔴 SELL"
            else:
                signal = "🟡 HOLD"

            # Главный фактор
            main_factor = item['factors'][0] if item['factors'] else "Нейтрально"

            report += f"| {rank} | **{ticker}** | {price} | {change} | {rsi} | {trend} | {signal} | {score} | {main_factor} |\n"

        report += "\n"

        # Топ сигналы
        report += "## 📊 Главные сигналы\n\n"

        buy_signals = [item for item in ranked if item['score'] >= 60]
        sell_signals = [item for item in ranked if item['score'] <= -10]
        hold_signals = [item for item in ranked if -10 < item['score'] < 60]

        if buy_signals:
            report += "### 🟢 Сигналы на ПОКУПКУ\n"
            for item in buy_signals:  # ← ВСЕ BUY сигналы, не только топ-3!
                # 🚨 Проверяем не исключена ли акция
                if item.get('is_excluded', False):
                    reason = item.get('excluded_reason', 'неизвестно')
                    report += f"- **{item['ticker']}** (⚠️ исключена: {reason})\n"
                    continue
                
                report += f"- **{item['ticker']}** (скор: {item['score']}) - {item['factors'][0]}\n"
                
                # 🔥 ДОБАВЛЯЕМ В АРХИВ РЕКОМЕНДАЦИЙ
                try:
                    full_result = item['full_result']
                    ticker = item['ticker']
                    entry_price = full_result.get('current_price', 0)
                    
                    # Используем уровни поддержки/сопротивления как цели
                    support = full_result.get('support_resistance', {}).get('support', entry_price * 0.98)
                    resistance = full_result.get('support_resistance', {}).get('resistance', entry_price * 1.05)
                    
                    # Рассчитываем цели на основе ATR или уровней
                    range_size = resistance - support
                    target1 = entry_price + (range_size * 0.5)
                    target2 = entry_price + (range_size * 1.0)
                    stop_loss = support * 0.98  # Чуть ниже поддержки
                    
                    rsi = full_result.get('technical_indicators', {}).get('rsi', 50)
                    trend = full_result.get('trend', {}).get('trend', 'sideways').upper()
                    
                    self.audit.add_recommendation(
                        ticker=ticker,
                        signal="BUY",
                        entry_price=entry_price,
                        target1=target1,
                        target2=target2,
                        stop_loss=stop_loss,
                        rsi=rsi,
                        trend=trend,
                        comment=f"{item['factors'][0]}"
                    )
                    logger.info(f"✅ Добавлена рекомендация BUY для {ticker}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при добавлении рекомендации {item['ticker']}: {e}")
            
            report += "\n"

        if sell_signals:
            report += "### 🔴 Сигналы на ПРОДАЖУ\n"
            for item in sell_signals[:3]:
                report += f"- **{item['ticker']}** (скор: {item['score']}) - {item['factors'][0]}\n"
            report += "\n"

        if hold_signals:
            report += "### 🟡 HOLD (Ожидание)\n"
            report += f"- Остальные {len(hold_signals)} акции\n\n"

        # Детальный анализ
        report += "## 📈 Детальный анализ\n\n"

        for item in ranked:
            report += self.generate_detailed_analysis(item['full_result'])

        logger.info("Отчёт сгенерирован успешно")
        return report

    def save_report(self, report_text: str, filename: Optional[str] = None) -> Path:
        """
        Сохраняет отчёт в файл.

        Args:
            report_text: Текст отчёта
            filename: Имя файла (если None, использует дату)

        Returns:
            Путь к сохранённому файлу
        """
        if filename is None:
            now = datetime.now()
            filename = f"report_{now.strftime('%Y%m%d_%H%M%S')}.md"

        filepath = self.reports_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_text)

            logger.info(f"Отчёт сохранён: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Ошибка при сохранении отчёта: {e}")
            return None

    def generate_and_save(self, tickers: List[str], filename: Optional[str] = None) -> Optional[Path]:
        """
        Генерирует отчёт и сохраняет его в файл.

        Args:
            tickers: Список тикеров
            filename: Имя файла (если None, использует дату)

        Returns:
            Путь к файлу или None
        """
        report = self.generate_weekly_report(tickers)
        if report:
            return self.save_report(report, filename)
        return None


def main():
    """Пример использования генератора отчётов."""
    print("\n" + "="*60)
    print("ГЕНЕРАТОР ОТЧЁТОВ")
    print("="*60)

    generator = ReportGenerator()

    # Список акций
    tickers = ['SBER', 'GAZP', 'LKOH', 'NVTK', 'TATN']

    # Генерируем и сохраняем отчёт
    filepath = generator.generate_and_save(tickers)

    if filepath:
        print(f"\n✅ Отчёт сохранён: {filepath}")

        # Выводим первую часть отчёта
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"\nПервые 2000 символов отчёта:")
            print("─" * 60)
            print(content[:2000])
            print("─" * 60)
            print(f"...\n(Полный отчёт в {filepath})")
    else:
        print("❌ Ошибка при генерировании отчёта")


if __name__ == "__main__":
    main()

