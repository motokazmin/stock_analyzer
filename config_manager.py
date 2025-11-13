"""
Менеджер конфигурации приложения.

Управляет чтением, написанием и валидацией конфигурации из config.json.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Путь к конфигурационному файлу
CONFIG_FILE = Path("config.json")

# Конфигурация по умолчанию
DEFAULT_CONFIG = {
    "app": {
        "name": "Stock Analyzer",
        "version": "1.0.0",
        "language": "ru"
    },
    "watchlist": ["SBER", "GAZP", "LKOH", "NVTK", "TATN"],
    "folders": {
        "data_folder": "stock_data",
        "reports_folder": "reports",
        "logs_folder": "logs"
    },
    "analysis": {
        "period_months": 6,
        "min_data_points": 60,
        "ema_periods": [20, 50, 200],
        "rsi_period": 14,
        "volume_bins": 20,
        "support_resistance_window": 20
    },
    "key_levels": {},
    "trading": {
        "min_rsi_for_buy": 30,
        "max_rsi_for_sell": 70,
        "min_volume_multiplier": 1.2,
        "risk_reward_ratio": 1.5
    },
    "reporting": {
        "format": "markdown",
        "include_detailed_analysis": True,
        "include_entry_exit_points": True,
        "theme": "default"
    },
    "last_updated": None,
    "last_report": None,
    "settings": {
        "auto_update": False,
        "update_interval_hours": 4,
        "save_history": True,
        "verbose_logging": False
    }
}


class ConfigManager:
    """Менеджер конфигурации приложения."""

    @staticmethod
    def load_config() -> Dict[str, Any]:
        """
        Загружает конфигурацию из файла.

        Returns:
            Словарь с конфигурацией
        """
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"✅ Конфигурация загружена: {CONFIG_FILE}")
                return config
            except json.JSONDecodeError as e:
                logger.error(f"❌ Ошибка парсинга config.json: {e}")
                return ConfigManager.create_default_config()
            except Exception as e:
                logger.error(f"❌ Ошибка при загрузке config.json: {e}")
                return ConfigManager.create_default_config()
        else:
            logger.warning(f"⚠️ config.json не найден, создаём новый")
            return ConfigManager.create_default_config()

    @staticmethod
    def save_config(config: Dict[str, Any]) -> bool:
        """
        Сохраняет конфигурацию в файл.

        Args:
            config: Словарь с конфигурацией

        Returns:
            True если успешно, False в противном случае
        """
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Конфигурация сохранена: {CONFIG_FILE}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении config.json: {e}")
            return False

    @staticmethod
    def create_default_config() -> Dict[str, Any]:
        """
        Создаёт конфигурацию по умолчанию.

        Returns:
            Конфигурация по умолчанию
        """
        config = DEFAULT_CONFIG.copy()
        ConfigManager.save_config(config)
        logger.info("✅ Создана конфигурация по умолчанию")
        return config

    @staticmethod
    def get_watchlist() -> List[str]:
        """Получает список акций для мониторинга."""
        config = ConfigManager.load_config()
        return config.get('watchlist', DEFAULT_CONFIG['watchlist'])

    @staticmethod
    def set_watchlist(tickers: List[str]) -> bool:
        """
        Устанавливает список акций.

        Args:
            tickers: Список тикеров

        Returns:
            True если успешно
        """
        config = ConfigManager.load_config()
        config['watchlist'] = [t.upper() for t in tickers]
        return ConfigManager.save_config(config)

    @staticmethod
    def add_to_watchlist(ticker: str) -> bool:
        """
        Добавляет акцию в watchlist.

        Args:
            ticker: Тикер акции

        Returns:
            True если успешно
        """
        config = ConfigManager.load_config()
        ticker = ticker.upper()

        if ticker in config['watchlist']:
            logger.warning(f"⚠️ {ticker} уже в watchlist")
            return False

        config['watchlist'].append(ticker)
        success = ConfigManager.save_config(config)

        if success:
            logger.info(f"✅ {ticker} добавлен в watchlist")
        return success

    @staticmethod
    def remove_from_watchlist(ticker: str) -> bool:
        """
        Удаляет акцию из watchlist.

        Args:
            ticker: Тикер акции

        Returns:
            True если успешно
        """
        config = ConfigManager.load_config()
        ticker = ticker.upper()

        if ticker not in config['watchlist']:
            logger.warning(f"⚠️ {ticker} не в watchlist")
            return False

        config['watchlist'].remove(ticker)
        success = ConfigManager.save_config(config)

        if success:
            logger.info(f"✅ {ticker} удален из watchlist")
        return success

    @staticmethod
    def get_key_levels(ticker: str) -> Optional[Dict[str, Any]]:
        """
        Получает ключевые уровни для акции.

        Args:
            ticker: Тикер акции

        Returns:
            Dict с уровнями или None
        """
        config = ConfigManager.load_config()
        ticker = ticker.upper()
        return config.get('key_levels', {}).get(ticker)

    @staticmethod
    def set_key_levels(ticker: str, levels: Dict[str, Any]) -> bool:
        """
        Устанавливает ключевые уровни для акции.

        Args:
            ticker: Тикер акции
            levels: Dict с поддержкой и сопротивлением

        Returns:
            True если успешно
        """
        config = ConfigManager.load_config()
        ticker = ticker.upper()

        if 'key_levels' not in config:
            config['key_levels'] = {}

        config['key_levels'][ticker] = levels
        success = ConfigManager.save_config(config)

        if success:
            logger.info(f"✅ Ключевые уровни для {ticker} сохранены")
        return success

    @staticmethod
    def get_data_folder() -> Path:
        """Получает путь к папке данных."""
        config = ConfigManager.load_config()
        folder = config.get('folders', {}).get('data_folder', 'stock_data')
        path = Path(folder)
        path.mkdir(exist_ok=True)
        return path

    @staticmethod
    def get_reports_folder() -> Path:
        """Получает путь к папке отчётов."""
        config = ConfigManager.load_config()
        folder = config.get('folders', {}).get('reports_folder', 'reports')
        path = Path(folder)
        path.mkdir(exist_ok=True)
        return path

    @staticmethod
    def get_logs_folder() -> Path:
        """Получает путь к папке логов."""
        config = ConfigManager.load_config()
        folder = config.get('folders', {}).get('logs_folder', 'logs')
        path = Path(folder)
        path.mkdir(exist_ok=True)
        return path

    @staticmethod
    def get_analysis_settings() -> Dict[str, Any]:
        """Получает настройки анализа."""
        config = ConfigManager.load_config()
        return config.get('analysis', DEFAULT_CONFIG['analysis'])

    @staticmethod
    def get_trading_settings() -> Dict[str, Any]:
        """Получает торговые настройки."""
        config = ConfigManager.load_config()
        return config.get('trading', DEFAULT_CONFIG['trading'])

    @staticmethod
    def get_reporting_settings() -> Dict[str, Any]:
        """Получает настройки отчётирования."""
        config = ConfigManager.load_config()
        return config.get('reporting', DEFAULT_CONFIG['reporting'])

    @staticmethod
    def update_last_updated() -> None:
        """Обновляет timestamp последнего обновления."""
        config = ConfigManager.load_config()
        config['last_updated'] = datetime.now().isoformat()
        ConfigManager.save_config(config)

    @staticmethod
    def update_last_report() -> None:
        """Обновляет timestamp последнего отчёта."""
        config = ConfigManager.load_config()
        config['last_report'] = datetime.now().isoformat()
        ConfigManager.save_config(config)

    @staticmethod
    def get_setting(key_path: str, default: Any = None) -> Any:
        """
        Получает значение по пути в конфиге.

        Args:
            key_path: Путь вида "app.name" или "analysis.ema_periods"
            default: Значение по умолчанию

        Returns:
            Значение или default
        """
        config = ConfigManager.load_config()
        keys = key_path.split('.')
        value = config

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default

        return value if value is not None else default

    @staticmethod
    def set_setting(key_path: str, value: Any) -> bool:
        """
        Устанавливает значение по пути в конфиге.

        Args:
            key_path: Путь вида "app.name" или "analysis.ema_periods"
            value: Новое значение

        Returns:
            True если успешно
        """
        config = ConfigManager.load_config()
        keys = key_path.split('.')

        # Навигируемся по конфигу
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Устанавливаем значение
        current[keys[-1]] = value

        return ConfigManager.save_config(config)

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Проверяет конфигурацию на ошибки.

        Args:
            config: Конфигурация для проверки

        Returns:
            Кортеж (валидна ли, список ошибок)
        """
        errors = []

        # Проверка обязательных полей
        required_fields = ['watchlist', 'folders', 'analysis']
        for field in required_fields:
            if field not in config:
                errors.append(f"Отсутствует обязательное поле: {field}")

        # Проверка watchlist
        if 'watchlist' in config:
            if not isinstance(config['watchlist'], list):
                errors.append("watchlist должен быть списком")
            elif not config['watchlist']:
                errors.append("watchlist не может быть пустым")

        # Проверка folders
        if 'folders' in config:
            if not isinstance(config['folders'], dict):
                errors.append("folders должен быть словарём")

        # Проверка analysis
        if 'analysis' in config:
            if not isinstance(config['analysis'], dict):
                errors.append("analysis должен быть словарём")
            if 'period_months' in config['analysis']:
                if not isinstance(config['analysis']['period_months'], int):
                    errors.append("period_months должен быть числом")

        return len(errors) == 0, errors

    @staticmethod
    def reset_to_default() -> bool:
        """
        Сбрасывает конфигурацию на значения по умолчанию.

        Returns:
            True если успешно
        """
        logger.warning("⚠️ Сброс конфигурации на значения по умолчанию")
        return ConfigManager.save_config(DEFAULT_CONFIG)

    @staticmethod
    def export_config(filepath: str) -> bool:
        """
        Экспортирует конфигурацию в файл.

        Args:
            filepath: Путь для экспорта

        Returns:
            True если успешно
        """
        try:
            config = ConfigManager.load_config()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Конфигурация экспортирована: {filepath}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при экспорте конфигурации: {e}")
            return False

    @staticmethod
    def import_config(filepath: str) -> bool:
        """
        Импортирует конфигурацию из файла.

        Args:
            filepath: Путь для импорта

        Returns:
            True если успешно
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Валидируем
            is_valid, errors = ConfigManager.validate_config(config)
            if not is_valid:
                logger.error(f"❌ Конфигурация невалидна: {errors}")
                return False

            # Сохраняем
            success = ConfigManager.save_config(config)
            if success:
                logger.info(f"✅ Конфигурация импортирована: {filepath}")
            return success

        except Exception as e:
            logger.error(f"❌ Ошибка при импорте конфигурации: {e}")
            return False

    @staticmethod
    def print_config() -> None:
        """Выводит конфигурацию в консоль."""
        config = ConfigManager.load_config()
        print("\n" + "="*60)
        print("📋 КОНФИГУРАЦИЯ")
        print("="*60 + "\n")

        print("Приложение:")
        app = config.get('app', {})
        print(f"  Имя: {app.get('name')}")
        print(f"  Версия: {app.get('version')}")
        print(f"  Язык: {app.get('language')}\n")

        print("Watchlist:")
        watchlist = config.get('watchlist', [])
        print(f"  Акций: {len(watchlist)}")
        for ticker in watchlist:
            print(f"    • {ticker}")
        print()

        print("Папки:")
        folders = config.get('folders', {})
        print(f"  Данные: {folders.get('data_folder')}")
        print(f"  Отчёты: {folders.get('reports_folder')}")
        print(f"  Логи: {folders.get('logs_folder')}\n")

        print("Анализ:")
        analysis = config.get('analysis', {})
        print(f"  Период: {analysis.get('period_months')} месяцев")
        print(f"  EMA: {analysis.get('ema_periods')}")
        print(f"  RSI период: {analysis.get('rsi_period')}\n")

        print("Торговля:")
        trading = config.get('trading', {})
        print(f"  Min RSI для покупки: {trading.get('min_rsi_for_buy')}")
        print(f"  Max RSI для продажи: {trading.get('max_rsi_for_sell')}")
        print(f"  Risk/Reward: {trading.get('risk_reward_ratio')}\n")

        print("Последние операции:")
        print(f"  Обновление: {config.get('last_updated', 'никогда')}")
        print(f"  Отчёт: {config.get('last_report', 'никогда')}\n")


def main():
    """Пример использования ConfigManager."""
    print("\n" + "="*60)
    print("ПРИМЕРЫ РАБОТЫ ConfigManager")
    print("="*60)

    # Пример 1: Загрузка конфигурации
    print("\n1️⃣ Загрузка конфигурации:")
    config = ConfigManager.load_config()
    print(f"   Загружено {len(config.get('watchlist', []))} акций")

    # Пример 2: Получение watchlist
    print("\n2️⃣ Получение watchlist:")
    watchlist = ConfigManager.get_watchlist()
    print(f"   {', '.join(watchlist)}")

    # Пример 3: Добавление акции
    print("\n3️⃣ Добавление акции:")
    if ConfigManager.add_to_watchlist("PLZL"):
        print("   ✅ PLZL добавлена")

    # Пример 4: Получение ключевых уровней
    print("\n4️⃣ Получение ключевых уровней:")
    levels = ConfigManager.get_key_levels("SBER")
    if levels:
        print(f"   SBER: поддержка={levels.get('support')}, сопротивление={levels.get('resistance')}")

    # Пример 5: Установка ключевых уровней
    print("\n5️⃣ Установка ключевых уровней:")
    new_levels = {
        "support": [280, 290],
        "resistance": [310, 320],
        "notes": "Новые уровни"
    }
    if ConfigManager.set_key_levels("PLZL", new_levels):
        print("   ✅ Уровни установлены")

    # Пример 6: Получение настроек
    print("\n6️⃣ Получение настроек анализа:")
    settings = ConfigManager.get_analysis_settings()
    print(f"   Период: {settings.get('period_months')} месяцев")
    print(f"   EMA: {settings.get('ema_periods')}")

    # Пример 7: Получение значения по пути
    print("\n7️⃣ Получение значения по пути:")
    version = ConfigManager.get_setting('app.version')
    print(f"   Версия: {version}")

    # Пример 8: Вывод конфигурации
    print("\n8️⃣ Вывод всей конфигурации:")
    ConfigManager.print_config()

    # Пример 9: Валидация конфигурации
    print("\n9️⃣ Валидация конфигурации:")
    is_valid, errors = ConfigManager.validate_config(config)
    if is_valid:
        print("   ✅ Конфигурация валидна")
    else:
        print(f"   ❌ Ошибки: {errors}")

    # Пример 10: Получение папок
    print("\n🔟 Получение путей папок:")
    data_folder = ConfigManager.get_data_folder()
    reports_folder = ConfigManager.get_reports_folder()
    print(f"   Данные: {data_folder}")
    print(f"   Отчёты: {reports_folder}")


if __name__ == "__main__":
    main()

