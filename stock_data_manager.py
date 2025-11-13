"""
Менеджер для скачивания и управления данными акций с Мосбиржи.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_data_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StockDataManager:
    """Менеджер для работы с данными акций Мосбиржи."""

    BASE_URL = "https://iss.moex.com/iss/history/engines/stock/markets/shares/securities"
    DATA_DIR = Path("stock_data")
    BATCH_SIZE = 100  # Максимум записей за запрос

    def __init__(self):
        """Инициализация менеджера."""
        self._create_data_directory()
        self._setup_session()
        logger.info("StockDataManager инициализирован")

    def _create_data_directory(self) -> None:
        """Создает директорию для хранения данных."""
        self.DATA_DIR.mkdir(exist_ok=True)
        logger.info(f"Директория данных: {self.DATA_DIR}")

    def _setup_session(self) -> None:
        """Настраивает сессию с повторными попытками при сбое."""
        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _get_csv_path(self, ticker: str) -> Path:
        """Возвращает путь к CSV файлу тикера."""
        return self.DATA_DIR / f"{ticker}_full.csv"

    def _get_last_date_in_file(self, ticker: str) -> Optional[datetime]:
        """Определяет последнюю дату в файле CSV."""
        csv_path = self._get_csv_path(ticker)
        
        if not csv_path.exists():
            logger.info(f"Файл для {ticker} не найден. Начнем с начала.")
            return None
        
        try:
            df = pd.read_csv(csv_path, parse_dates=['DATE'])
            if df.empty:
                logger.warning(f"Файл {ticker} пуст.")
                return None
            
            last_date = df['DATE'].max()
            logger.info(f"Последняя дата для {ticker}: {last_date.date()}")
            return last_date
        
        except Exception as e:
            logger.error(f"Ошибка при чтении файла {ticker}: {e}")
            return None

    def _fetch_data_batch(
        self, 
        ticker: str, 
        start: int = 0
    ) -> Tuple[List[Dict], bool]:
        """
        Скачивает батч данных с API Мосбиржи.
        
        Args:
            ticker: Тикер акции
            start: Начальная позиция для пагинации
            
        Returns:
            Кортеж (список данных, есть ли еще данные)
        """
        url = f"{self.BASE_URL}/{ticker}.json"
        
        params = {
            'start': start,
            'limit': self.BATCH_SIZE
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Проверяем, есть ли данные в ответе
            if 'history' not in data or not data['history']['data']:
                logger.warning(f"Нет данных для {ticker} с позиции {start}")
                return [], False
            
            history_data = data['history']['data']
            columns = data['history']['columns']
            
            # Преобразуем в список словарей
            records = []
            for row in history_data:
                record = dict(zip(columns, row))
                records.append(record)
            
            # Проверяем, есть ли еще данные
            has_more = len(history_data) == self.BATCH_SIZE
            
            logger.info(f"Загружено {len(records)} записей для {ticker} " 
                       f"(позиция {start}, еще: {has_more})")
            
            return records, has_more
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка API при загрузке {ticker}: {e}")
            return [], False
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Ошибка парсинга данных для {ticker}: {e}")
            return [], False

    def download_stock_data(
        self, 
        ticker: str, 
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Скачивает данные по акции с Мосбиржи.
        
        Args:
            ticker: Тикер акции
            from_date: Начальная дата в формате YYYY-MM-DD
            to_date: Конечная дата в формате YYYY-MM-DD
            
        Returns:
            DataFrame с данными
        """
        logger.info(f"Начинаем загрузку данных для {ticker}")
        
        all_records = []
        start = 0
        
        while True:
            records, has_more = self._fetch_data_batch(ticker, start)
            
            if not records:
                break
            
            all_records.extend(records)
            
            if not has_more:
                break
            
            start += self.BATCH_SIZE
        
        if not all_records:
            logger.warning(f"Не удалось загрузить данные для {ticker}")
            return pd.DataFrame()
        
        # Преобразуем в DataFrame
        df = pd.DataFrame(all_records)
        
        # Переименовываем столбцы (API может вернуть разные названия)
        column_mapping = {
            'TRADEDATE': 'DATE',
            'OPEN': 'OPEN',
            'HIGH': 'HIGH',
            'LOW': 'LOW',
            'CLOSE': 'CLOSE',
            'VOLUME': 'VOLUME'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Оставляем только нужные столбцы
        required_columns = ['DATE', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']
        available_columns = [col for col in required_columns if col in df.columns]
        df = df[available_columns]
        
        # Конвертируем дату
        df['DATE'] = pd.to_datetime(df['DATE'])
        
        # Фильтруем по датам если указаны
        if from_date:
            from_dt = pd.to_datetime(from_date)
            df = df[df['DATE'] >= from_dt]
        
        if to_date:
            to_dt = pd.to_datetime(to_date)
            df = df[df['DATE'] <= to_dt]
        
        # Сортируем по дате
        df = df.sort_values('DATE').reset_index(drop=True)
        
        logger.info(f"Загружено {len(df)} записей для {ticker}")
        
        return df

    def _merge_data(
        self, 
        existing_df: pd.DataFrame, 
        new_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Объединяет существующие и новые данные.
        
        Args:
            existing_df: Существующие данные
            new_df: Новые данные
            
        Returns:
            Объединенный DataFrame
        """
        # Объединяем оба DataFrame
        merged_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # Удаляем дубликаты, оставляя последнюю версию
        merged_df = merged_df.drop_duplicates(subset=['DATE'], keep='last')
        
        # Сортируем по дате
        merged_df = merged_df.sort_values('DATE').reset_index(drop=True)
        
        return merged_df

    def save_to_csv(self, ticker: str, data: pd.DataFrame) -> bool:
        """
        Сохраняет данные в CSV файл.
        
        Args:
            ticker: Тикер акции
            data: DataFrame для сохранения
            
        Returns:
            True если успешно, False в противном случае
        """
        try:
            csv_path = self._get_csv_path(ticker)
            
            # Убеждаемся, что DATE в формате string для CSV
            df_to_save = data.copy()
            df_to_save['DATE'] = df_to_save['DATE'].dt.strftime('%Y-%m-%d')
            
            df_to_save.to_csv(csv_path, index=False)
            logger.info(f"Данные {ticker} сохранены: {csv_path}")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка при сохранении {ticker}: {e}")
            return False

    def update_watchlist(self, tickers_list: List[str]) -> Dict[str, bool]:
        """
        Обновляет данные для списка акций.
        
        Args:
            tickers_list: Список тикеров
            
        Returns:
            Словарь с результатами обновления
        """
        results = {}
        
        logger.info(f"Начинаем обновление для {len(tickers_list)} акций")
        
        for ticker in tickers_list:
            try:
                logger.info(f"\n--- Обновление {ticker} ---")
                
                # Получаем последнюю дату в существующем файле
                last_date = self._get_last_date_in_file(ticker)
                
                # Определяем начальную дату для загрузки
                if last_date:
                    # Начинаем со дня после последнего
                    from_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
                    logger.info(f"Загружаем новые данные с {from_date}")
                else:
                    # Если нет файла, загружаем со значения по умолчанию
                    # Например, за последний год
                    one_year_ago = datetime.now() - timedelta(days=365)
                    from_date = one_year_ago.strftime('%Y-%m-%d')
                    logger.info(f"Загружаем исторические данные с {from_date}")
                
                # Скачиваем данные
                new_data = self.download_stock_data(ticker, from_date=from_date)
                
                if new_data.empty:
                    logger.warning(f"Нет новых данных для {ticker}")
                    results[ticker] = False
                    continue
                
                # Если существует файл, объединяем данные
                if last_date is not None:
                    existing_data = pd.read_csv(
                        self._get_csv_path(ticker),
                        parse_dates=['DATE']
                    )
                    merged_data = self._merge_data(existing_data, new_data)
                    logger.info(f"Объединено данных для {ticker}: "
                               f"{len(existing_data)} + {len(new_data)} = {len(merged_data)}")
                else:
                    merged_data = new_data
                
                # Сохраняем данные
                success = self.save_to_csv(ticker, merged_data)
                results[ticker] = success
                
                if success:
                    logger.info(f"✓ {ticker} успешно обновлен ({len(merged_data)} записей)")
                else:
                    logger.warning(f"✗ Ошибка при обновлении {ticker}")
            
            except Exception as e:
                logger.error(f"Критическая ошибка при обновлении {ticker}: {e}")
                results[ticker] = False
        
        # Итоговый отчет
        successful = sum(1 for v in results.values() if v)
        logger.info(f"\n{'='*50}")
        logger.info(f"Обновление завершено: {successful}/{len(tickers_list)} успешно")
        logger.info(f"{'='*50}\n")
        
        return results

    def get_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Получает сохраненные данные по тикеру.
        
        Args:
            ticker: Тикер акции
            
        Returns:
            DataFrame с данными или None
        """
        csv_path = self._get_csv_path(ticker)
        
        if not csv_path.exists():
            logger.warning(f"Данные для {ticker} не найдены")
            return None
        
        try:
            df = pd.read_csv(csv_path, parse_dates=['DATE'])
            logger.info(f"Загружены данные для {ticker}: {len(df)} записей")
            return df
        
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных {ticker}: {e}")
            return None

    def get_statistics(self, ticker: str) -> Dict:
        """
        Получает статистику по данным акции.
        
        Args:
            ticker: Тикер акции
            
        Returns:
            Словарь со статистикой
        """
        df = self.get_data(ticker)
        
        if df is None or df.empty:
            return {}
        
        return {
            'ticker': ticker,
            'total_records': len(df),
            'date_from': df['DATE'].min().strftime('%Y-%m-%d'),
            'date_to': df['DATE'].max().strftime('%Y-%m-%d'),
            'avg_price': df['CLOSE'].mean(),
            'min_price': df['CLOSE'].min(),
            'max_price': df['CLOSE'].max(),
            'total_volume': df['VOLUME'].sum()
        }


def main():
    """Пример использования менеджера."""
    manager = StockDataManager()
    
    # Список популярных акций Мосбиржи
    tickers = ['SBER', 'GAZP', 'NVTK', 'PHOR', 'TATN']
    
    # Обновляем данные
    results = manager.update_watchlist(tickers)
    
    # Выводим статистику
    print("\n" + "="*60)
    print("СТАТИСТИКА ПО АКЦИЯМ")
    print("="*60)
    
    for ticker in tickers:
        stats = manager.get_statistics(ticker)
        if stats:
            print(f"\n{ticker}:")
            print(f"  Записей: {stats['total_records']}")
            print(f"  Период: {stats['date_from']} - {stats['date_to']}")
            print(f"  Цена (средняя): {stats['avg_price']:.2f}")
            print(f"  Цена (min-max): {stats['min_price']:.2f} - {stats['max_price']:.2f}")
            print(f"  Объем торгов: {stats['total_volume']:,.0f}")


if __name__ == "__main__":
    main()

