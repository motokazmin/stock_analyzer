"""
Модуль для технического анализа акций.

Функции для расчета различных технических индикаторов и анализа трендов.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Импортируем ta-library (обязательна!)
import ta

# Импортируем ConfigManager для получения уровней из конфига
try:
    from config_manager import ConfigManager
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """Класс для технического анализа акций."""

    def __init__(self):
        """Инициализация анализатора.
        
        Устанавливает стандартные параметры для технического анализа:
        - MA периоды: 20, 50, 200
        - RSI период: 14
        - ADX пороги для определения тренда
        """
        self.ma_periods = [20, 50, 200]
        self.rsi_period = 14
        self.adx_strong_threshold = 25  # ADX > 25 = сильный тренд
        self.adx_weak_threshold = 15    # ADX < 15 = нет тренда
        logger.debug("TechnicalAnalyzer инициализирован с стандартными параметрами")

    @staticmethod
    def is_false_recovery(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Обнаруживает ЛОЖНЫЕ восстановления (отскоки от дна).
        
        Использует 5 независимых индикаторов ta-library для проверки:
        1. ADX двойной (14 и 50 периоды) - сравнение краткосроч и долгосроч тренда
        2. MACD дивергенция - расхождение цены и индикатора
        3. OBV (объёмы) - подтверждение рост объёмом
        4. RSI - перекупленность после падения
        5. Bollinger Bands - цена на экстремуме
        
        Args:
            df: DataFrame с колонками CLOSE, HIGH, LOW, VOLUME
            
        Returns:
            (is_false: bool, reasons: List[str])
            - is_false: True если это ложный отскок
            - reasons: список причин исключения
        """
        if len(df) < 50:
            logger.debug(f"Недостаточно данных для анализа ложного отскока: {len(df)} < 50")
            return False, []
        
        try:
            reasons = []
            close = df['CLOSE'].values
            high = df['HIGH'].values
            low = df['LOW'].values
            volume = df['VOLUME'].values
            
            # ════════════════════════════════════════════════════════════
            # 1️⃣ ADX ДВОЙНОЙ - Сравнение краткосроч и долгосроч тренда
            # ════════════════════════════════════════════════════════════
            try:
                adx_14 = ta.trend.adx(pd.Series(high), pd.Series(low), pd.Series(close), window=14)
                adx_50 = ta.trend.adx(pd.Series(high), pd.Series(low), pd.Series(close), window=50)
                
                adx_14_val = float(adx_14.iloc[-1]) if not pd.isna(adx_14.iloc[-1]) else 0
                adx_50_val = float(adx_50.iloc[-1]) if not pd.isna(adx_50.iloc[-1]) else 0
                
                # Если долгосроч тренда нет, а краткосроч сильный - подозрительно!
                # ADX > 25 = сильный тренд, ADX < 15 = нет тренда
                if adx_50_val < 15 and adx_14_val > 25:
                    reasons.append(f"ADX: долгосроч тренда нет (ADX-50={adx_50_val:.1f}), но краткосроч сильный (ADX-14={adx_14_val:.1f})")
                    logger.warning(f"  ⚠️ ADX расхождение: ADX-50={adx_50_val:.1f} vs ADX-14={adx_14_val:.1f}")
                    
            except Exception as e:
                logger.debug(f"Ошибка при расчёте ADX: {e}")
            
            # ════════════════════════════════════════════════════════════
            # 2️⃣ MACD - Проверка дивергенции (цена растёт, MACD падает)
            # ════════════════════════════════════════════════════════════
            try:
                macd = ta.trend.macd(pd.Series(close))
                
                # Сравниваем направления: цена vs MACD за последние 30 дней
                price_30_days_ago = close[-30] if len(close) >= 30 else close[0]
                macd_30_days_ago = macd.iloc[-30] if len(macd) >= 30 else macd.iloc[0]
                
                price_direction = "up" if close[-1] > price_30_days_ago else "down"
                macd_direction = "up" if macd.iloc[-1] > macd_30_days_ago else "down"
                
                # Дивергенция: цена растёт, но MACD падает!
                if price_direction == "up" and macd_direction == "down":
                    reasons.append(f"MACD дивергенция: цена растёт, но MACD падает")
                    logger.warning(f"  ⚠️ MACD дивергенция обнаружена")
                    
            except Exception as e:
                logger.debug(f"Ошибка при расчёте MACD: {e}")
            
            # ════════════════════════════════════════════════════════════
            # 3️⃣ OBV (On-Balance Volume) - Подтверждение объёмом
            # ════════════════════════════════════════════════════════════
            try:
                obv = ta.volume.on_balance_volume(pd.Series(close), pd.Series(volume))
                obv_ma = obv.rolling(window=30).mean()
                
                # Если цена растёт (последние 30 дней), но OBV падает - объём не подтверждает!
                price_rising = close[-1] > close[-30] if len(close) >= 30 else True
                obv_falling = obv.iloc[-1] < obv_ma.iloc[-1]
                
                if price_rising and obv_falling:
                    reasons.append(f"OBV: цена растёт, но объём не подтверждает (OBV ниже MA)")
                    logger.warning(f"  ⚠️ OBV не подтверждает рост цены")
                    
            except Exception as e:
                logger.debug(f"Ошибка при расчёте OBV: {e}")
            
            # ════════════════════════════════════════════════════════════
            # 4️⃣ RSI - Перекупленность + отсутствие долгосроч тренда
            # ════════════════════════════════════════════════════════════
            try:
                rsi = ta.momentum.rsi(pd.Series(close), window=14)
                rsi_val = float(rsi.iloc[-1])
                
                # RSI > 80 = очень перекуплено, обычно идёт откат
                # Особенно опасно если нет долгосроч тренда
                try:
                    adx_50_val = float(adx_50.iloc[-1]) if not pd.isna(adx_50.iloc[-1]) else 0
                except:
                    adx_50_val = 0
                
                if rsi_val > 80 and adx_50_val < 20:
                    reasons.append(f"RSI перекупленность (RSI={rsi_val:.0f}) без долгосроч тренда (ADX-50={adx_50_val:.1f})")
                    logger.warning(f"  ⚠️ RSI высокий ({rsi_val:.0f}) - риск отката")
                    
            except Exception as e:
                logger.debug(f"Ошибка при расчёте RSI: {e}")
            
            # ════════════════════════════════════════════════════════════
            # 5️⃣ Bollinger Bands - Цена на экстремуме
            # ════════════════════════════════════════════════════════════
            try:
                bb_high = ta.volatility.bollinger_hband(pd.Series(close), window=20, window_dev=2)
                bb_low = ta.volatility.bollinger_lband(pd.Series(close), window=20, window_dev=2)
                
                # Считаем позицию цены относительно лент (0-1)
                current_price = close[-1]
                upper = bb_high.iloc[-1]
                lower = bb_low.iloc[-1]
                
                if upper > lower:
                    price_position = (current_price - lower) / (upper - lower)
                else:
                    price_position = 0.5
                
                # Если цена на ВЕРХНЕЙ ленте (> 0.8) после падения - отскок!
                try:
                    adx_50_val = float(adx_50.iloc[-1]) if not pd.isna(adx_50.iloc[-1]) else 0
                except:
                    adx_50_val = 0
                
                if price_position > 0.8 and adx_50_val < 20:
                    reasons.append(f"Bollinger Bands: цена на верхней ленте ({price_position:.2%}) без тренда")
                    logger.warning(f"  ⚠️ Цена на верхней ленте Bollinger - локальный максимум")
                    
            except Exception as e:
                logger.debug(f"Ошибка при расчёте Bollinger Bands: {e}")
            
            # ════════════════════════════════════════════════════════════
            # ФИНАЛЬНЫЙ ВЫВОД
            # ════════════════════════════════════════════════════════════
            is_false = len(reasons) >= 2  # Нужно минимум 2 причины для исключения
            
            if is_false:
                logger.warning(f"🚨 ЛОЖНЫЙ ОТСКОК ОБНАРУЖЕН! Причины ({len(reasons)}):")
                for i, reason in enumerate(reasons, 1):
                    logger.warning(f"   {i}. {reason}")
            
            return is_false, reasons
            
        except Exception as e:
            logger.error(f"Ошибка в is_false_recovery: {e}")
            return False, []


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
            current_price = df['CLOSE'].iloc[-1]
            
            # Находим локальные максимумы (сопротивление)
            resistance_levels = []
            for i in range(window, len(df) - window):
                if df['HIGH'].iloc[i] == df['HIGH'].iloc[i - window:i + window].max():
                    # Берем только уровни выше текущей цены
                    if df['HIGH'].iloc[i] > current_price:
                        resistance_levels.append(df['HIGH'].iloc[i])

            # Находим локальные минимумы (поддержка)
            support_levels = []
            for i in range(window, len(df) - window):
                if df['LOW'].iloc[i] == df['LOW'].iloc[i - window:i + window].min():
                    # Берем только уровни ниже текущей цены
                    if df['LOW'].iloc[i] < current_price:
                        support_levels.append(df['LOW'].iloc[i])

            # Если уровней нет, берем ближайшие к цене
            if not resistance_levels:
                # Ищем ближайший максимум выше цены
                highs_above = df[df['HIGH'] > current_price]['HIGH']
                if not highs_above.empty:
                    resistance_levels = [highs_above.min()]
            
            if not support_levels:
                # Ищем ближайший минимум ниже цены
                lows_below = df[df['LOW'] < current_price]['LOW']
                if not lows_below.empty:
                    support_levels = [lows_below.max()]

            # Берем средние значения (или ближайшие уровни)
            if resistance_levels:
                # Берем 2-3 ближайших уровня сопротивления
                resistance = np.mean(sorted(resistance_levels)[:3]) if len(resistance_levels) >= 3 else np.mean(resistance_levels)
            else:
                resistance = None
            
            if support_levels:
                # Берем 2-3 ближайших уровня поддержки
                support = np.mean(sorted(support_levels, reverse=True)[:3]) if len(support_levels) >= 3 else np.mean(support_levels)
            else:
                support = None

            result = {
                'support': support,
                'resistance': resistance,
                'current_price': current_price,
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
        Определяет текущий тренд (up/down/sideways) используя ADX и МА.

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
            high = df.get('HIGH', df['CLOSE'])
            low = df.get('LOW', df['CLOSE'])

            # Нужно минимум 50 свечей для корректного расчёта
            if len(df) < 50:
                logger.warning(f"Недостаточно данных для анализа тренда: {len(df)} < 50")
                return {'trend': 'sideways', 'strength': 'weak', 'adx': 0}

            # 1️⃣ Расчитываем ADX (профессиональный индикатор тренда)
            # ADX > 25 = сильный тренд, ADX < 20 = нет тренда
            try:
                adx = ta.trend.adx(high, low, close, window=14)
                adx_value = float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 0
            except Exception as e:
                logger.error(f"Ошибка при расчёте ADX: {e}")
                raise  # Если ta не работает, это критическая ошибка

            # 2️⃣ Скользящие средние (долгосрочный тренд)
            ma_20 = close.rolling(window=20).mean()
            ma_50 = close.rolling(window=50).mean()
            ma_200 = close.rolling(window=200).mean()

            # Последние значения
            last_close = close.iloc[-1]
            last_ma20 = ma_20.iloc[-1]
            last_ma50 = ma_50.iloc[-1]
            last_ma200 = ma_200.iloc[-1]

            # 3️⃣ Определяем тренд (используем ADX как приоритет)
            if adx_value > 25:
                # Сильный тренд - определяем направление по МА и CLOSE
                if last_close > last_ma50:
                    trend = 'up'
                    strength = 'strong'
                else:
                    trend = 'down'
                    strength = 'strong'
            elif adx_value > 20:
                # Умеренный тренд
                if last_close > last_ma50:
                    trend = 'up'
                    strength = 'moderate'
                else:
                    trend = 'down'
                    strength = 'moderate'
            else:
                # Слабый тренд / боковик
                trend = 'sideways'
                strength = 'weak'

            # 4️⃣ Общее изменение цены за весь период
            price_change_pct = ((last_close - close.iloc[0]) / close.iloc[0]) * 100 if len(close) > 0 else 0
            
            # 5️⃣ Угол наклона за последние 30 дней (для подтверждения)
            recent_closes = close.tail(30).values
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
                'ma_200': float(last_ma200) if not pd.isna(last_ma200) else None,
                'adx': float(adx_value),  # ← НОВОЕ: ADX индикатор
                'angle': float(angle),
                'above_ma20': last_close > last_ma20,
                'above_ma50': last_close > last_ma50,
                'price_change_overall': float(price_change_pct)  # ← НОВОЕ: общее изменение
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

            # 1. EMA (используем та напрямую)
            try:
                df['EMA_20'] = ta.trend.ema_indicator(df['CLOSE'], window=20, fillna=True)
                df['EMA_50'] = ta.trend.ema_indicator(df['CLOSE'], window=50, fillna=True)
                df['EMA_200'] = ta.trend.ema_indicator(df['CLOSE'], window=200, fillna=True)
                logger.info("EMA индикаторы (20, 50, 200) рассчитаны")
            except Exception as e:
                logger.error(f"Ошибка при расчете EMA: {e}")

            # 2. RSI (используем та напрямую)
            try:
                df['RSI'] = ta.momentum.rsi(df['CLOSE'], window=14, fillna=True)
                logger.info("RSI индикатор рассчитан")
            except Exception as e:
                logger.error(f"Ошибка при расчете RSI: {e}")

            # 3. Поддержка/сопротивление
            # ВАРИАНТ 1: Приоритет конфигу
            support_resistance = analyzer.find_support_resistance(df, window=20)
            
            # Проверяем наличие ручных уровней в конфиге
            if CONFIG_MANAGER_AVAILABLE:
                try:
                    config_levels = ConfigManager.get_key_levels(ticker)
                    if config_levels:
                        # Если есть значения в поддержке
                        if config_levels.get('support') and len(config_levels.get('support', [])) > 0:
                            support = np.mean(config_levels['support'])
                            support_resistance['support'] = support
                            logger.info(f"[{ticker}] Используются ручные уровни поддержки: {config_levels['support']}")
                        
                        # Если есть значения в сопротивлении
                        if config_levels.get('resistance') and len(config_levels.get('resistance', [])) > 0:
                            resistance = np.mean(config_levels['resistance'])
                            support_resistance['resistance'] = resistance
                            logger.info(f"[{ticker}] Используются ручные уровни сопротивления: {config_levels['resistance']}")
                        
                        # Если есть пометка источника
                        if config_levels.get('notes'):
                            support_resistance['source'] = config_levels['notes']
                except Exception as e:
                    logger.warning(f"Не удалось получить уровни из конфига для {ticker}: {e}")

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

