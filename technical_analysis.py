"""
Модуль для технического анализа акций.

Функции для расчета различных технических индикаторов и анализа трендов.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Попытаемся импортировать ta-lib если доступна
try:
    import ta
    TA_LIB_AVAILABLE = True
except ImportError:
    TA_LIB_AVAILABLE = False

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """Класс для технического анализа акций."""

    def __init__(self):
        """Инициализация анализатора."""
        logger.info(f"TA-lib доступна: {TA_LIB_AVAILABLE}")

    @staticmethod
    def calculate_ema(df: pd.DataFrame, periods: List[int] = [20, 50, 200]) -> pd.DataFrame:
        """
        Рассчитывает экспоненциальное скользящее среднее (EMA).

        Args:
            df: DataFrame с колонкой CLOSE
            periods: Список периодов для EMA

        Returns:
            DataFrame исходный + колонки с EMA_20, EMA_50, EMA_200 и т.д.
        """
        df = df.copy()

        if 'CLOSE' not in df.columns:
            logger.error("DataFrame должен содержать колонку CLOSE")
            return df

        for period in periods:
            col_name = f'EMA_{period}'
            try:
                if TA_LIB_AVAILABLE:
                    df[col_name] = ta.trend.ema_indicator(
                        close=df['CLOSE'],
                        window=period,
                        fillna=True
                    )
                else:
                    # Реализация EMA без ta-lib
                    df[col_name] = df['CLOSE'].ewm(span=period, adjust=False).mean()

                logger.info(f"EMA_{period} рассчитана")
            except Exception as e:
                logger.error(f"Ошибка при расчете EMA_{period}: {e}")

        return df

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Рассчитывает индекс относительной силы (RSI).

        Args:
            df: DataFrame с колонкой CLOSE
            period: Период для расчета (обычно 14)

        Returns:
            DataFrame с колонкой RSI
        """
        df = df.copy()

        if 'CLOSE' not in df.columns:
            logger.error("DataFrame должен содержать колонку CLOSE")
            return df

        try:
            if TA_LIB_AVAILABLE:
                df['RSI'] = ta.momentum.rsi(
                    close=df['CLOSE'],
                    window=period,
                    fillna=True
                )
            else:
                # Реализация RSI без ta-lib
                delta = df['CLOSE'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))

            logger.info(f"RSI (период {period}) рассчитана")
        except Exception as e:
            logger.error(f"Ошибка при расчете RSI: {e}")

        return df

    @staticmethod
    def find_support_resistance(
        df: pd.DataFrame,
        window: int = 20
    ) -> Dict[str, Tuple[float, float]]:
        """
        Находит уровни поддержки и сопротивления.

        Args:
            df: DataFrame с колонками HIGH, LOW, CLOSE
            window: Окно для поиска экстремумов

        Returns:
            Словарь с уровнями поддержки и сопротивления
        """
        if 'HIGH' not in df.columns or 'LOW' not in df.columns:
            logger.error("DataFrame должен содержать колонки HIGH и LOW")
            return {}

        try:
            # Находим локальные максимумы (сопротивление)
            resistance_levels = []
            for i in range(window, len(df) - window):
                if df['HIGH'].iloc[i] == df['HIGH'].iloc[i - window:i + window].max():
                    resistance_levels.append(df['HIGH'].iloc[i])

            # Находим локальные минимумы (поддержка)
            support_levels = []
            for i in range(window, len(df) - window):
                if df['LOW'].iloc[i] == df['LOW'].iloc[i - window:i + window].min():
                    support_levels.append(df['LOW'].iloc[i])

            # Берем средние значения
            resistance = np.mean(resistance_levels) if resistance_levels else None
            support = np.mean(support_levels) if support_levels else None

            result = {
                'support': support,
                'resistance': resistance,
                'support_levels_count': len(support_levels),
                'resistance_levels_count': len(resistance_levels)
            }

            logger.info(f"Уровни найдены: Поддержка={support:.2f}, Сопротивление={resistance:.2f}")
            return result

        except Exception as e:
            logger.error(f"Ошибка при поиске уровней поддержки/сопротивления: {e}")
            return {}

    @staticmethod
    def detect_trend(df: pd.DataFrame) -> Dict[str, any]:
        """
        Определяет текущий тренд (up/down/sideways).

        Args:
            df: DataFrame с колонками CLOSE, HIGH, LOW

        Returns:
            Словарь с информацией о тренде
        """
        if 'CLOSE' not in df.columns:
            logger.error("DataFrame должен содержать колонку CLOSE")
            return {}

        try:
            close = df['CLOSE']

            # Считаем средние цены
            ma_20 = close.rolling(window=20).mean()
            ma_50 = close.rolling(window=50).mean()

            # Последние значения
            last_close = close.iloc[-1]
            last_ma20 = ma_20.iloc[-1]
            last_ma50 = ma_50.iloc[-1]

            # Определяем тренд
            if last_close > last_ma20 > last_ma50:
                trend = 'up'
                strength = 'strong'
            elif last_close > last_ma20 and last_close > last_ma50:
                trend = 'up'
                strength = 'moderate'
            elif last_close < last_ma20 < last_ma50:
                trend = 'down'
                strength = 'strong'
            elif last_close < last_ma20 and last_close < last_ma50:
                trend = 'down'
                strength = 'moderate'
            else:
                trend = 'sideways'
                strength = 'weak'

            # Считаем угол наклона
            recent_closes = close.tail(10).values
            if len(recent_closes) > 1:
                angle = np.polyfit(range(len(recent_closes)), recent_closes, 1)[0]
            else:
                angle = 0

            result = {
                'trend': trend,
                'strength': strength,
                'current_price': float(last_close),
                'ma_20': float(last_ma20),
                'ma_50': float(last_ma50),
                'angle': float(angle),
                'above_ma20': last_close > last_ma20,
                'above_ma50': last_close > last_ma50
            }

            logger.info(f"Тренд определен: {trend} ({strength})")
            return result

        except Exception as e:
            logger.error(f"Ошибка при определении тренда: {e}")
            return {}

    @staticmethod
    def calculate_volume_profile(df: pd.DataFrame, bins: int = 20) -> Dict[str, any]:
        """
        Анализирует профиль объёмов.

        Args:
            df: DataFrame с колонками CLOSE, VOLUME
            bins: Количество ценовых уровней для анализа

        Returns:
            Словарь с анализом объёмов
        """
        if 'CLOSE' not in df.columns or 'VOLUME' not in df.columns:
            logger.error("DataFrame должен содержать колонки CLOSE и VOLUME")
            return {}

        try:
            close = df['CLOSE']
            volume = df['VOLUME']

            # Создаем ценовые уровни
            price_min = close.min()
            price_max = close.max()
            price_bins = np.linspace(price_min, price_max, bins)

            # Считаем объемы по уровням
            volume_by_price = []
            for i in range(len(price_bins) - 1):
                mask = (close >= price_bins[i]) & (close < price_bins[i + 1])
                vol = volume[mask].sum() if mask.any() else 0
                volume_by_price.append({
                    'price_level': (price_bins[i] + price_bins[i + 1]) / 2,
                    'volume': vol
                })

            # Находим уровень максимального объема (POC - Point of Control)
            poc = max(volume_by_price, key=lambda x: x['volume'])['price_level']

            # Общая статистика
            result = {
                'total_volume': float(volume.sum()),
                'avg_volume': float(volume.mean()),
                'max_volume': float(volume.max()),
                'min_volume': float(volume.min()),
                'point_of_control': float(poc),
                'volume_trend': 'increasing' if volume.iloc[-1] > volume.mean() else 'decreasing',
                'volume_by_price': volume_by_price
            }

            logger.info(f"Профиль объемов анализирован. POC={poc:.2f}")
            return result

        except Exception as e:
            logger.error(f"Ошибка при анализе профиля объемов: {e}")
            return {}

    @staticmethod
    def analyze_stock(ticker: str, csv_path: Optional[str] = None) -> Dict[str, any]:
        """
        Проводит полный технический анализ акции.

        Args:
            ticker: Тикер акции
            csv_path: Путь к CSV файлу данных (если None, ищет в stock_data/)

        Returns:
            Словарь с полными метриками анализа
        """
        try:
            # Определяем путь к файлу
            if csv_path is None:
                csv_path = f"stock_data/{ticker}_full.csv"

            csv_path = Path(csv_path)

            # Проверяем существование файла
            if not csv_path.exists():
                logger.error(f"Файл не найден: {csv_path}")
                return {}

            # Загружаем данные
            df = pd.read_csv(csv_path, parse_dates=['DATE'])
            logger.info(f"Загружены данные для {ticker}: {len(df)} записей")

            # Выполняем анализ
            analyzer = TechnicalAnalyzer()

            # 1. EMA
            df = analyzer.calculate_ema(df, periods=[20, 50, 200])

            # 2. RSI
            df = analyzer.calculate_rsi(df, period=14)

            # 3. Поддержка/сопротивление
            support_resistance = analyzer.find_support_resistance(df, window=20)

            # 4. Тренд
            trend_analysis = analyzer.detect_trend(df)

            # 5. Профиль объемов
            volume_profile = analyzer.calculate_volume_profile(df, bins=20)

            # Итоговый результат
            result = {
                'ticker': ticker,
                'data_points': len(df),
                'date_from': df['DATE'].min().strftime('%Y-%m-%d'),
                'date_to': df['DATE'].max().strftime('%Y-%m-%d'),
                'current_price': float(df['CLOSE'].iloc[-1]),
                'price_change': float(df['CLOSE'].iloc[-1] - df['CLOSE'].iloc[0]),
                'price_change_pct': float((df['CLOSE'].iloc[-1] / df['CLOSE'].iloc[0] - 1) * 100),
                'technical_indicators': {
                    'ema_20': float(df['EMA_20'].iloc[-1]) if 'EMA_20' in df.columns else None,
                    'ema_50': float(df['EMA_50'].iloc[-1]) if 'EMA_50' in df.columns else None,
                    'ema_200': float(df['EMA_200'].iloc[-1]) if 'EMA_200' in df.columns else None,
                    'rsi': float(df['RSI'].iloc[-1]) if 'RSI' in df.columns else None,
                    'rsi_signal': 'overbought' if df['RSI'].iloc[-1] > 70 else (
                        'oversold' if df['RSI'].iloc[-1] < 30 else 'neutral'
                    ) if 'RSI' in df.columns else None
                },
                'support_resistance': support_resistance,
                'trend': trend_analysis,
                'volume': volume_profile
            }

            logger.info(f"Полный анализ {ticker} завершен")
            return result

        except Exception as e:
            logger.error(f"Ошибка при анализе {ticker}: {e}", exc_info=True)
            return {}


def main():
    """Пример использования модуля."""
    analyzer = TechnicalAnalyzer()

    # Пример анализа
    tickers = ['SBER', 'GAZP', 'LKOH']

    for ticker in tickers:
        print(f"\n{'='*60}")
        print(f"АНАЛИЗ {ticker}")
        print(f"{'='*60}")

        result = analyzer.analyze_stock(ticker)

        if result:
            print(f"\nБазовая информация:")
            print(f"  Цена: {result['current_price']:.2f} ₽")
            print(f"  Изменение: {result['price_change']:.2f} ({result['price_change_pct']:.2f}%)")
            print(f"  Период: {result['date_from']} - {result['date_to']}")

            print(f"\nТехнические индикаторы:")
            indicators = result['technical_indicators']
            print(f"  EMA 20: {indicators['ema_20']:.2f}" if indicators['ema_20'] else "  EMA 20: N/A")
            print(f"  EMA 50: {indicators['ema_50']:.2f}" if indicators['ema_50'] else "  EMA 50: N/A")
            print(f"  EMA 200: {indicators['ema_200']:.2f}" if indicators['ema_200'] else "  EMA 200: N/A")
            print(f"  RSI: {indicators['rsi']:.2f} ({indicators['rsi_signal']})" if indicators['rsi'] else "  RSI: N/A")

            print(f"\nПоддержка/сопротивление:")
            sr = result['support_resistance']
            if sr:
                print(f"  Поддержка: {sr.get('support', 'N/A'):.2f}" if sr.get('support') else "  Поддержка: N/A")
                print(f"  Сопротивление: {sr.get('resistance', 'N/A'):.2f}" if sr.get('resistance') else "  Сопротивление: N/A")

            print(f"\nТренд:")
            trend = result['trend']
            if trend:
                print(f"  Направление: {trend.get('trend', 'N/A').upper()}")
                print(f"  Сила: {trend.get('strength', 'N/A')}")
                print(f"  Выше MA20: {trend.get('above_ma20', 'N/A')}")
                print(f"  Выше MA50: {trend.get('above_ma50', 'N/A')}")

            print(f"\nОбъемы:")
            vol = result['volume']
            if vol:
                print(f"  Средний объем: {vol.get('avg_volume', 0):,.0f}")
                print(f"  Тренд объема: {vol.get('volume_trend', 'N/A')}")
                print(f"  Point of Control: {vol.get('point_of_control', 'N/A'):.2f}")
        else:
            print(f"Не удалось проанализировать {ticker}")


if __name__ == "__main__":
    main()

