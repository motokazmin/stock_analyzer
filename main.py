#!/usr/bin/env python3
"""
Stock Analyzer - CLI интерфейс для управления и анализа акций.

Команды:
  python main.py update              - обновить данные акций
  python main.py analyze             - анализ и создание отчёта
  python main.py add <ticker>        - добавить акцию в watchlist
  python main.py remove <ticker>     - удалить из watchlist
  python main.py list                - показать watchlist
  python main.py info <ticker>       - информация по акции
  python main.py status              - статус приложения
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from stock_data_manager import StockDataManager
from technical_analysis import TechnicalAnalyzer
from report_generator import ReportGenerator
from audit_manager import AuditManager
from audit_report_generator import AuditReportGenerator
from news_integration import NewsIntegration

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Пути
CONFIG_FILE = Path("config.json")
DEFAULT_WATCHLIST = ['SBER', 'GAZP', 'LKOH', 'NVTK', 'TATN']


class ConfigManager:
    """Менеджер конфигурации приложения."""

    @staticmethod
    def load_config() -> Dict:
        """Загружает конфигурацию из файла."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка при загрузке config.json: {e}")
                return ConfigManager.create_default_config()
        else:
            return ConfigManager.create_default_config()

    @staticmethod
    def create_default_config() -> Dict:
        """Создаёт конфигурацию по умолчанию."""
        config = {
            'watchlist': DEFAULT_WATCHLIST,
            'last_updated': None,
            'last_report': None,
            'settings': {
                'auto_update': False,
                'report_format': 'markdown',
                'theme': 'default'
            }
        }
        ConfigManager.save_config(config)
        logger.info("✅ Создана конфигурация по умолчанию")
        return config

    @staticmethod
    def save_config(config: Dict) -> bool:
        """Сохраняет конфигурацию в файл."""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении config.json: {e}")
            return False

    @staticmethod
    def get_watchlist() -> List[str]:
        """Получает список акций для мониторинга."""
        config = ConfigManager.load_config()
        return config.get('watchlist', DEFAULT_WATCHLIST)

    @staticmethod
    def add_to_watchlist(ticker: str) -> bool:
        """Добавляет акцию в watchlist."""
        config = ConfigManager.load_config()
        ticker = ticker.upper()

        if ticker in config['watchlist']:
            logger.warning(f"⚠️ {ticker} уже в watchlist")
            return False

        config['watchlist'].append(ticker)
        if ConfigManager.save_config(config):
            logger.info(f"✅ {ticker} добавлен в watchlist")
            return True
        return False

    @staticmethod
    def remove_from_watchlist(ticker: str) -> bool:
        """Удаляет акцию из watchlist."""
        config = ConfigManager.load_config()
        ticker = ticker.upper()

        if ticker not in config['watchlist']:
            logger.warning(f"⚠️ {ticker} не в watchlist")
            return False

        config['watchlist'].remove(ticker)
        if ConfigManager.save_config(config):
            logger.info(f"✅ {ticker} удален из watchlist")
            return True
        return False

    @staticmethod
    def update_timestamp(key: str) -> None:
        """Обновляет timestamp события."""
        config = ConfigManager.load_config()
        config[key] = datetime.now().isoformat()
        ConfigManager.save_config(config)


class StockAnalyzerCLI:
    """CLI интерфейс для Stock Analyzer."""

    def __init__(self):
        """Инициализация."""
        self.manager = StockDataManager()
        self.analyzer = TechnicalAnalyzer()
        self.reporter = ReportGenerator()
        self.audit = AuditManager()

    def update_data(self, args) -> int:
        """Команда: обновить данные."""
        print("\n" + "="*60)
        print("📥 ОБНОВЛЕНИЕ ДАННЫХ АКЦИЙ")
        print("="*60 + "\n")

        watchlist = ConfigManager.get_watchlist()
        
        if not watchlist:
            print("❌ Watchlist пуст. Добавьте акции командой: python main.py add <ticker>")
            return 1

        print(f"📊 Обновляем {len(watchlist)} акций: {', '.join(watchlist)}\n")

        results = self.manager.update_watchlist(watchlist)

        # Статистика
        successful = sum(1 for v in results.values() if v)
        failed = len(results) - successful

        print(f"\n✅ Успешно: {successful}")
        print(f"❌ Ошибок: {failed}")

        if failed == 0:
            ConfigManager.update_timestamp('last_updated')
            print("\n✅ Все данные обновлены!")
            return 0
        else:
            print(f"\n⚠️ Некоторые акции не обновлены")
            return 1

    def analyze_data(self, args) -> int:
        """Команда: анализ и отчёт."""
        print("\n" + "="*60)
        print("📊 АНАЛИЗ И СОЗДАНИЕ ОТЧЁТА")
        print("="*60 + "\n")

        watchlist = ConfigManager.get_watchlist()

        if not watchlist:
            print("❌ Watchlist пуст")
            return 1

        print(f"🔍 Анализируем {len(watchlist)} акций...\n")

        # Генерируем отчёт
        filepath = self.reporter.generate_and_save(watchlist)

        if filepath:
            print(f"\n✅ Отчёт создан: {filepath}")
            ConfigManager.update_timestamp('last_report')

            # 📰 Попытка загрузить новости (используется Mock провайдер)
            print("\n📰 Инициализирую систему новостей...")
            try:
                news_integration = NewsIntegration()
                print(f"   {news_integration.get_provider_info()}")
                
                # Парсим отчёт чтобы найти BUY сигналы
                buy_signals = self._extract_buy_signals(filepath)
                
                if buy_signals:
                    print(f"   Найдено {len(buy_signals)} BUY сигналов: {', '.join(buy_signals)}")
                    news_results = news_integration.get_news_for_analysis(buy_signals)
                    
                    if news_results:
                        # Сохраняем новости в JSON
                        news_file = Path("stock_news.json")
                        with open(news_file, 'w', encoding='utf-8') as f:
                            json.dump(news_results, f, ensure_ascii=False, indent=2)
                        
                        print(f"✅ Новости сохранены: {news_file}")
                        
                        # Выводим статистику
                        total_articles = sum(len(v) for v in news_results.values())
                        print(f"   📊 Всего статей найдено: {total_articles}")
                        for ticker, articles in news_results.items():
                            sentiments = [a.get('sentiment') for a in articles]
                            print(f"   - {ticker}: {len(articles)} статей ({', '.join(set(sentiments))})")
                    else:
                        print("   ℹ️ Новостей не получено (используется Mock провайдер)")
                        print("   ⚠️ Когда появится MOEX API - новости будут автоматически добавлены")
                else:
                    print("   ℹ️ BUY сигналов не найдено")
                    
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при работе с новостями: {e}")

            # Выводим первую часть отчёта
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                print(f"\n📄 Первая часть отчёта:")
                print("─" * 60)
                print('\n'.join(lines[:40]))
                print("─" * 60)
                print(f"...\n(Смотрите полный отчёт в {filepath})")

            return 0
        else:
            print("\n❌ Ошибка при создании отчёта")
            return 1

    @staticmethod
    def _extract_buy_signals(filepath: Path) -> List[str]:
        """Извлекает BUY сигналы из markdown отчёта.
        
        Args:
            filepath: Путь к markdown отчёту
            
        Returns:
            Список тикеров с BUY сигналами
        """
        buy_tickers = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Ищем строки с BUY сигналами в таблице
            import re
            # Паттерн: | # | **TICKER** | ... | 🟢 BUY |
            matches = re.findall(r'\*\*([A-Z0-9\-]+)\*\*.*?🟢 BUY', content)
            buy_tickers.extend(matches)
            
            # Ищем в списке "Сигналы на ПОКУПКУ"
            # Паттерн: - **TICKER** (...)
            if '### 🟢 Сигналы на ПОКУПКУ' in content:
                signals_section = content.split('### 🟢 Сигналы на ПОКУПКУ')[1]
                if '### 🟡 HOLD' in signals_section:
                    signals_section = signals_section.split('### 🟡 HOLD')[0]
                
                matches = re.findall(r'- \*\*([A-Z0-9\-]+)\*\*', signals_section)
                buy_tickers.extend(matches)
            
            # Убираем дубликаты и исключённые (с ⚠️)
            buy_tickers = list(set(buy_tickers))
            
            return buy_tickers
            
        except Exception as e:
            logger.warning(f"Ошибка при парсинге отчёта: {e}")
            return []

    def add_ticker(self, args) -> int:
        """Команда: добавить акцию."""
        ticker = args.ticker.upper()

        print(f"\n➕ Добавляем {ticker}...\n")

        # Проверяем, существует ли акция
        print(f"🔍 Проверяем {ticker}...")
        try:
            result = self.analyzer.analyze_stock(ticker)
            if result:
                print(f"✅ {ticker} найден!")

                if ConfigManager.add_to_watchlist(ticker):
                    print(f"\n✅ {ticker} добавлен в watchlist")
                    return 0
                else:
                    return 1
            else:
                print(f"\n❌ Акция {ticker} не найдена или нет данных")
                return 1
        except Exception as e:
            print(f"❌ Ошибка при проверке: {e}")
            return 1

    def remove_ticker(self, args) -> int:
        """Команда: удалить акцию."""
        ticker = args.ticker.upper()

        print(f"\n➖ Удаляем {ticker}...\n")

        if ConfigManager.remove_from_watchlist(ticker):
            print(f"✅ {ticker} удален из watchlist")
            return 0
        else:
            return 1

    def list_watchlist(self, args) -> int:
        """Команда: показать watchlist."""
        print("\n" + "="*60)
        print("📋 ТЕКУЩИЙ WATCHLIST")
        print("="*60 + "\n")

        watchlist = ConfigManager.get_watchlist()

        if not watchlist:
            print("Watchlist пуст\n")
            return 0

        print(f"Отслеживаем {len(watchlist)} акций:\n")

        for idx, ticker in enumerate(watchlist, 1):
            print(f"  {idx}. {ticker}")

        print()
        return 0

    def get_ticker_info(self, args) -> int:
        """Команда: информация по акции."""
        ticker = args.ticker.upper()

        print("\n" + "="*60)
        print(f"📊 ИНФОРМАЦИЯ ПО {ticker}")
        print("="*60 + "\n")

        try:
            result = self.analyzer.analyze_stock(ticker)

            if not result:
                print(f"❌ Не удалось получить информацию по {ticker}")
                return 1

            print(f"Цена: {result['current_price']:.2f} ₽")
            print(f"Изменение: {result['price_change']:+.2f} ({result['price_change_pct']:+.2f}%)")
            print(f"Период: {result['date_from']} - {result['date_to']}")
            print(f"Данных: {result['data_points']} дней\n")

            # Индикаторы
            print("Технические индикаторы:")
            ind = result['technical_indicators']
            print(f"  EMA 20: {ind['ema_20']:.2f}" if ind['ema_20'] else "  EMA 20: N/A")
            print(f"  EMA 50: {ind['ema_50']:.2f}" if ind['ema_50'] else "  EMA 50: N/A")
            print(f"  RSI: {ind['rsi']:.2f} ({ind['rsi_signal']})" if ind['rsi'] else "  RSI: N/A")

            # Тренд
            trend = result['trend']
            print(f"\nТренд:")
            print(f"  Направление: {trend['trend'].upper()}")
            print(f"  Сила: {trend['strength']}")
            print(f"  Выше MA20: {'✅ Да' if trend['above_ma20'] else '❌ Нет'}")
            print(f"  Выше MA50: {'✅ Да' if trend['above_ma50'] else '❌ Нет'}")

            # Сигнал
            from report_generator import ReportGenerator
            signals = ReportGenerator.find_signals(result)
            print(f"\nСигнал: {signals['primary']} ({signals['strength']})")

            print()
            return 0

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return 1

    def show_status(self, args) -> int:
        """Команда: статус приложения."""
        print("\n" + "="*60)
        print("📈 СТАТУС STOCK ANALYZER")
        print("="*60 + "\n")

        config = ConfigManager.load_config()

        print("Информация о приложении:")
        print(f"  Версия: 1.0.0")
        print(f"  Статус: ✅ Активно\n")

        print("Конфигурация:")
        watchlist = config.get('watchlist', [])
        print(f"  Акций в watchlist: {len(watchlist)}")
        print(f"  Список: {', '.join(watchlist) if watchlist else 'пуст'}")

        last_updated = config.get('last_updated')
        if last_updated:
            print(f"  Последнее обновление: {last_updated}")
        else:
            print(f"  Последнее обновление: никогда")

        last_report = config.get('last_report')
        if last_report:
            print(f"  Последний отчёт: {last_report}")
        else:
            print(f"  Последний отчёт: не создан")

        print("\nДоступные данные:")
        data_dir = Path("stock_data")
        if data_dir.exists():
            csv_files = list(data_dir.glob("*.csv"))
            print(f"  CSV файлов: {len(csv_files)}")
            if csv_files:
                for csv_file in csv_files[:5]:
                    size = csv_file.stat().st_size / 1024
                    print(f"    • {csv_file.name} ({size:.1f} KB)")
                if len(csv_files) > 5:
                    print(f"    ... и ещё {len(csv_files) - 5}")
        else:
            print(f"  CSV файлов: нет (папка stock_data не создана)")

        print("\nОтчёты:")
        reports_dir = Path("reports")
        if reports_dir.exists():
            report_files = list(reports_dir.glob("*.md"))
            print(f"  Markdown отчётов: {len(report_files)}")
            if report_files:
                # Последний отчёт
                latest = max(report_files, key=lambda x: x.stat().st_mtime)
                print(f"    Последний: {latest.name}")
        else:
            print(f"  Markdown отчётов: нет (папка reports не создана)")

        print()
        return 0

    def audit_recommendations(self, args) -> int:
        """Команда: аудит рекомендаций."""
        print("\n" + "="*60)
        print("📊 АУДИТ ТОРГОВЫХ РЕКОМЕНДАЦИЙ")
        print("="*60 + "\n")

        print("🔍 Проверяем все активные рекомендации...\n")

        try:
            # Проверяем рекомендации
            results = self.audit.audit_all()

            if not results:
                print("⚠️ Нет рекомендаций для проверки")
                return 0

            # Выводим результаты
            print(f"✅ Проверено рекомендаций: {len(results)}\n")

            for result in results:
                ticker = result.get('ticker', 'N/A')
                status = result.get('status', 'N/A')
                result_pct = result.get('result_pct', 0)
                
                emoji = "✅" if result_pct > 0 else "❌" if result_pct < 0 else "⏳"
                print(f"{emoji} {ticker}: {status} ({result_pct:+.2f}%)")

            # Получаем статистику
            stats = self.audit.get_statistics()
            print(f"\n📈 Статистика:")
            print(f"  Всего: {stats['total_recommendations']}")
            print(f"  Выполнено: {stats['completed']}")
            print(f"  Провалено: {stats['failed']}")
            print(f"  Активно: {stats['active']}")
            print(f"  Успешность: {stats['success_rate']}%")
            print(f"  Средний результат: {stats['avg_profit']:+.2f}%")

            # Генерируем HTML отчёт
            print(f"\n📄 Создаём HTML отчёт...")
            generator = AuditReportGenerator()
            report_path = generator.save_report()
            print(f"✅ Отчёт сохранён: {report_path}")

            print()
            return 0

        except Exception as e:
            print(f"❌ Ошибка при аудите: {e}")
            return 1


def main():
    """Основная функция CLI."""
    parser = argparse.ArgumentParser(
        description='Stock Analyzer - анализ акций Мосбиржи',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python main.py update                 Обновить все акции
  python main.py analyze                Создать анализ и отчёт
  python main.py add SBER               Добавить SBER в watchlist
  python main.py remove GAZP            Удалить GAZP из watchlist
  python main.py list                   Показать watchlist
  python main.py info LKOH              Информация по LKOH
  python main.py status                 Статус приложения

Для справки по команде:
  python main.py <команда> -h
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')

    # Команда: update
    subparsers.add_parser(
        'update',
        help='Обновить данные всех акций из watchlist'
    )

    # Команда: analyze
    subparsers.add_parser(
        'analyze',
        help='Провести анализ и создать отчёт'
    )

    # Команда: add
    add_parser = subparsers.add_parser(
        'add',
        help='Добавить акцию в watchlist'
    )
    add_parser.add_argument(
        'ticker',
        help='Тикер акции (например, SBER)'
    )

    # Команда: remove
    remove_parser = subparsers.add_parser(
        'remove',
        help='Удалить акцию из watchlist'
    )
    remove_parser.add_argument(
        'ticker',
        help='Тикер акции'
    )

    # Команда: list
    subparsers.add_parser(
        'list',
        help='Показать текущий watchlist'
    )

    # Команда: info
    info_parser = subparsers.add_parser(
        'info',
        help='Получить информацию по акции'
    )
    info_parser.add_argument(
        'ticker',
        help='Тикер акции'
    )

    # Команда: status
    subparsers.add_parser(
        'status',
        help='Показать статус приложения'
    )

    # Команда: audit
    subparsers.add_parser(
        'audit',
        help='Аудит торговых рекомендаций и создание отчёта'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Инициализируем CLI
    cli = StockAnalyzerCLI()

    # Выполняем команду
    try:
        if args.command == 'update':
            return cli.update_data(args)
        elif args.command == 'analyze':
            return cli.analyze_data(args)
        elif args.command == 'add':
            return cli.add_ticker(args)
        elif args.command == 'remove':
            return cli.remove_ticker(args)
        elif args.command == 'list':
            return cli.list_watchlist(args)
        elif args.command == 'info':
            return cli.get_ticker_info(args)
        elif args.command == 'status':
            return cli.show_status(args)
        elif args.command == 'audit':
            return cli.audit_recommendations(args)
        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️ Прервано пользователем")
        return 130
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())

