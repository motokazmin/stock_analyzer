"""
Конфигурация для StockDataManager
"""

from pathlib import Path

# Директория для хранения данных
DATA_DIR = Path("stock_data")

# URL API Мосбиржи
MOEX_API_BASE = "https://iss.moex.com/iss/history/engines/stock/markets/shares/securities"

# Максимум записей за один API запрос
BATCH_SIZE = 100

# Таймаут для API запросов (секунды)
REQUEST_TIMEOUT = 10

# Количество повторных попыток при сбое
MAX_RETRIES = 3

# Логирование
LOG_FILE = "stock_data_manager.log"
LOG_LEVEL = "INFO"

# Популярные тикеры Мосбиржи (для быстрого доступа)
POPULAR_TICKERS = {
    # Финансовый сектор
    'SBER': 'Сбербанк',
    'SBERP': 'Сбербанк (префы)',
    'ROLO': 'Роснефть',
    
    # Энергетика
    'GAZP': 'Газпром',
    'GAZPROM': 'Газпром (полное имя)',
    'GMKN': 'ПИК ОАО',
    
    # Нефть и газ
    'LKOH': 'Лукойл',
    'NVTK': 'Новатэк',
    'TATN': 'Татнефть',
    'TATNP': 'Татнефть (префы)',
    'IRAO': 'РусГидро',
    'MAGN': 'Магнит',
    
    # Драгметаллы
    'PLZL': 'Полюс Золото',
    'GLDRUB': 'Золото в рублях',
    
    # Фармацевтика
    'PHOR': 'Фармакор',
    'PIKK': 'ПИК',
    
    # Индексы
    'Si': 'Доллар/Рубль',
    'MOEX': 'Индекс MOEX',
    'RSTI': 'Индекс RSTI',
}

# Список акций для мониторинга по умолчанию
DEFAULT_WATCHLIST = ['SBER', 'GAZP', 'LKOH', 'NVTK', 'TATN']

# Период для инициальной загрузки данных (дни)
INITIAL_PERIOD_DAYS = 365

# Формат CSV
CSV_COLUMNS = ['DATE', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']
CSV_DATE_FORMAT = '%Y-%m-%d'

# Параметры для логирования
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Параметры HTTP запросов
HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# API параметры
API_PARAMS = {
    'iss.json.dates': 'latin',  # Формат дат
    'iss.only': 'history',      # Загружать только history
}

