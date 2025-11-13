#!/usr/bin/env python3
"""
Ежедневное обновление данных акций Мосбиржи
Подходит для запуска через cron или Task Scheduler
"""

import sys
import logging
from datetime import datetime
from stock_data_manager import StockDataManager
from config import DEFAULT_WATCHLIST, LOG_FILE

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Основная функция."""
    logger.info("="*60)
    logger.info("Начало ежедневного обновления данных Мосбиржи")
    logger.info("="*60)
    
    try:
        # Инициализация менеджера
        manager = StockDataManager()
        
        # Список акций для обновления
        tickers = DEFAULT_WATCHLIST
        logger.info(f"Обновляем тикеры: {', '.join(tickers)}")
        
        # Обновление данных
        results = manager.update_watchlist(tickers)
        
        # Анализ результатов
        successful = sum(1 for v in results.values() if v)
        failed = len(results) - successful
        
        logger.info(f"Результаты: {successful} успешно, {failed} ошибок")
        
        # Статистика
        logger.info("="*60)
        logger.info("Статистика по акциям:")
        for ticker in tickers:
            stats = manager.get_statistics(ticker)
            if stats:
                logger.info(f"\n{ticker}:")
                logger.info(f"  Всего записей: {stats['total_records']}")
                logger.info(f"  Период: {stats['date_from']} - {stats['date_to']}")
                logger.info(f"  Цена: {stats['avg_price']:.2f} (мин: {stats['min_price']:.2f}, "
                           f"макс: {stats['max_price']:.2f})")
        
        logger.info("="*60)
        logger.info("Обновление завершено успешно")
        logger.info("="*60)
        
        return 0 if failed == 0 else 1
    
    except Exception as e:
        logger.error(f"Критическая ошибка при обновлении: {e}", exc_info=True)
        logger.info("="*60)
        logger.info("Обновление завершено с ошибкой")
        logger.info("="*60)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

