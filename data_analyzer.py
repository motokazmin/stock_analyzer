"""
Утилита для анализа данных акций
"""

import pandas as pd
from pathlib import Path
from stock_data_manager import StockDataManager
import logging

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """Анализатор данных акций."""
    
    def __init__(self):
        """Инициализация анализатора."""
        self.manager = StockDataManager()
    
    def get_daily_changes(self, ticker: str) -> pd.DataFrame:
        """
        Получает дневные изменения цен.
        
        Args:
            ticker: Тикер акции
            
        Returns:
            DataFrame с колонками: DATE, CLOSE, CHANGE, CHANGE_PCT
        """
        df = self.manager.get_data(ticker)
        
        if df is None or df.empty:
            return pd.DataFrame()
        
        df = df.copy()
        df['CHANGE'] = df['CLOSE'].diff()
        df['CHANGE_PCT'] = df['CLOSE'].pct_change() * 100
        
        return df[['DATE', 'CLOSE', 'CHANGE', 'CHANGE_PCT']]
    
    def get_volatility(self, ticker: str, window: int = 20) -> float:
        """
        Вычисляет волатильность (стандартное отклонение).
        
        Args:
            ticker: Тикер акции
            window: Количество дней для расчета
            
        Returns:
            Волатильность в процентах
        """
        df = self.manager.get_data(ticker)
        
        if df is None or df.empty or len(df) < window:
            return 0.0
        
        returns = df['CLOSE'].pct_change()
        volatility = returns.tail(window).std() * 100
        
        return volatility
    
    def get_moving_average(
        self, 
        ticker: str, 
        window: int = 20
    ) -> pd.DataFrame:
        """
        Получает скользящее среднее.
        
        Args:
            ticker: Тикер акции
            window: Количество дней для окна
            
        Returns:
            DataFrame с колонками: DATE, CLOSE, MA
        """
        df = self.manager.get_data(ticker)
        
        if df is None or df.empty:
            return pd.DataFrame()
        
        df = df.copy()
        df['MA'] = df['CLOSE'].rolling(window=window).mean()
        
        return df[['DATE', 'CLOSE', 'MA']].dropna()
    
    def get_price_range(self, ticker: str) -> dict:
        """
        Получает диапазон цен.
        
        Args:
            ticker: Тикер акции
            
        Returns:
            Словарь с информацией о диапазоне
        """
        df = self.manager.get_data(ticker)
        
        if df is None or df.empty:
            return {}
        
        return {
            'ticker': ticker,
            'current': df['CLOSE'].iloc[-1],
            'high': df['CLOSE'].max(),
            'low': df['CLOSE'].min(),
            'avg': df['CLOSE'].mean(),
            'high_date': df.loc[df['CLOSE'].idxmax(), 'DATE'],
            'low_date': df.loc[df['CLOSE'].idxmin(), 'DATE'],
        }
    
    def compare_tickers(self, tickers: list) -> pd.DataFrame:
        """
        Сравнивает несколько акций.
        
        Args:
            tickers: Список тикеров
            
        Returns:
            DataFrame для сравнения
        """
        data = []
        
        for ticker in tickers:
            stats = self.manager.get_statistics(ticker)
            if stats:
                volatility = self.get_volatility(ticker)
                data.append({
                    'Тикер': ticker,
                    'Записей': stats['total_records'],
                    'Ср. цена': f"{stats['avg_price']:.2f}",
                    'Мин': f"{stats['min_price']:.2f}",
                    'Макс': f"{stats['max_price']:.2f}",
                    'Волатильность': f"{volatility:.2f}%",
                    'Объем': f"{stats['total_volume']:,.0f}"
                })
        
        return pd.DataFrame(data)
    
    def export_comparison(self, tickers: list, filename: str = "comparison.csv"):
        """
        Экспортирует сравнение в CSV.
        
        Args:
            tickers: Список тикеров
            filename: Имя файла
        """
        df = self.compare_tickers(tickers)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"Сравнение экспортировано в {filename}")
    
    def export_ticker_data(
        self, 
        ticker: str, 
        output_dir: str = "exports"
    ):
        """
        Экспортирует данные тикера с техническими индикаторами.
        
        Args:
            ticker: Тикер акции
            output_dir: Директория для сохранения
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        df = self.manager.get_data(ticker)
        
        if df is None or df.empty:
            logger.warning(f"Данные для {ticker} не найдены")
            return
        
        # Добавляем технические индикаторы
        df_export = df.copy()
        df_export['MA20'] = df['CLOSE'].rolling(window=20).mean()
        df_export['MA50'] = df['CLOSE'].rolling(window=50).mean()
        df_export['CHANGE'] = df['CLOSE'].diff()
        df_export['CHANGE_PCT'] = df['CLOSE'].pct_change() * 100
        
        # Сохраняем
        filename = output_path / f"{ticker}_analysis.csv"
        df_export.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"Данные экспортированы в {filename}")
    
    def print_summary(self, ticker: str):
        """
        Выводит сводку по акции.
        
        Args:
            ticker: Тикер акции
        """
        print(f"\n{'='*60}")
        print(f"СВОДКА ПО {ticker}")
        print(f"{'='*60}")
        
        stats = self.manager.get_statistics(ticker)
        if not stats:
            print(f"Данные для {ticker} не найдены")
            return
        
        print(f"\nОсновная информация:")
        print(f"  Всего записей: {stats['total_records']}")
        print(f"  Период: {stats['date_from']} - {stats['date_to']}")
        
        print(f"\nЦены (₽):")
        print(f"  Текущая: {stats['avg_price']:.2f}")
        print(f"  Минимум: {stats['min_price']:.2f}")
        print(f"  Максимум: {stats['max_price']:.2f}")
        print(f"  Диапазон: {stats['max_price'] - stats['min_price']:.2f}")
        
        volatility = self.get_volatility(ticker)
        print(f"\nВолатильность:")
        print(f"  (20 дней): {volatility:.2f}%")
        
        daily_changes = self.get_daily_changes(ticker)
        if not daily_changes.empty:
            latest = daily_changes.iloc[-1]
            print(f"\nПоследний день:")
            print(f"  Дата: {latest['DATE'].date()}")
            print(f"  Цена закрытия: {latest['CLOSE']:.2f}")
            if pd.notna(latest['CHANGE']):
                print(f"  Изменение: {latest['CHANGE']:+.2f} ({latest['CHANGE_PCT']:+.2f}%)")
        
        print(f"\nОбъем торгов:")
        print(f"  Всего: {stats['total_volume']:,.0f}")
        print(f"\n{'='*60}\n")


def main():
    """Пример использования анализатора."""
    analyzer = DataAnalyzer()
    
    # Сводка по акции
    analyzer.print_summary('SBER')
    
    # Волатильность
    print("\nВолатильность:")
    for ticker in ['SBER', 'GAZP', 'LKOH']:
        volatility = analyzer.get_volatility(ticker)
        print(f"  {ticker}: {volatility:.2f}%")
    
    # Сравнение акций
    print("\nСравнение акций:")
    comparison = analyzer.compare_tickers(['SBER', 'GAZP', 'LKOH', 'NVTK'])
    print(comparison.to_string(index=False))
    
    # Экспорт
    analyzer.export_comparison(['SBER', 'GAZP', 'LKOH'])


if __name__ == "__main__":
    main()

