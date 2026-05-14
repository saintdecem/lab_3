import sys
import os
from abc import ABC, abstractmethod
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel,
    QSpinBox, QMessageBox, QFileDialog, QHeaderView, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.figure import Figure
import pandas as pd


# Абстрактные интерфейсы - DIP (принцип инверсии зависимостей)
# MainWindow зависит от этих абстракций, а не от pandas/matplotlib напрямую
class IDataLoader(ABC):
    """Интерфейс загрузчика данных. Любой загрузчик должен уметь load()."""
    @abstractmethod
    def load(self, path: str) -> list:
        pass


class IForecaster(ABC):
    """Интерфейс прогнозатора. Любой метод должен уметь forecast()."""
    @abstractmethod
    def forecast(self, data: list, window: int, periods: int) -> list:
        pass


class IAnalyzer(ABC):
    """Интерфейс анализатора. Любой анализатор должен уметь analyze()."""
    @abstractmethod
    def analyze(self, data: list) -> str:
        pass


# Маппинг названий колонок - OCP (принцип открытости/закрытости)
# Чтобы добавить новый тип преступности, добавь запись сюда
# Код классов менять не нужно
COLUMN_MAPPING = {
    'year':     ['year', 'god', 'let'],
    'murder':   ['murder', 'murders', 'ubiystva', 'ubiy', 'killing', 'homicide'],
    'robbery':  ['robbery', 'robberies', 'razboi', 'razboy', 'rob'],
    'theft':    ['theft', 'thefts', 'krazha', 'krazhi', 'kraz', 'steal'],
    'fraud':    ['fraud', 'trickery', 'moshennichestvo', 'mosh', 'scam'],
    'drugs':    ['drugs', 'drug', 'narkotiki', 'narko', 'narc'],
    'economic': ['economic', 'economy', 'ekonomicheskie', 'ekonom', 'econ'],
}

# Настройки отображения графиков - меняй цвета/подписи здесь
# Код отрисовки трогать не придётся
PLOT_CONFIG = {
    'murder':   {'label': 'Murder',   'color': '#e74c3c'},
    'robbery':  {'label': 'Robbery',  'color': '#e67e22'},
    'theft':    {'label': 'Theft',    'color': '#3498db'},
    'fraud':    {'label': 'Fraud',    'color': '#2ecc71'},
    'drugs':    {'label': 'Drugs',    'color': '#9b59b6'},
    'economic': {'label': 'Economic', 'color': '#1abc9c'},
}

# Обязательные поля данных
REQUIRED_FIELDS = ['year', 'murder', 'robbery', 'theft', 'fraud', 'drugs', 'economic']


# SRP (принцип единственной ответственности)
# Этот класс ТОЛЬКО загружает и парсит Excel, ничего больше
class ExcelDataLoader(IDataLoader):
    """Загрузка данных о преступности из Excel. Автоопределение колонок."""
    
    def load(self, path: str) -> list:
        """Загрузить данные из Excel-файла. Возвращает список словарей."""
        if not os.path.exists(path):
            raise FileNotFoundError(f'File not found:\n{path}')
        
        df = pd.read_excel(path)
        column_map = self._map_columns(df)      # Сопоставляем колонки
        self._check_missing(column_map)          # Проверяем что всё нашли
        return self._parse_rows(df, column_map)  # Парсим в список
    
    def _map_columns(self, df) -> dict:
        """Сопоставить колонки Excel с нужными ключами по названиям."""
        mapping = {}
        for col in df.columns:
            col_lower = str(col).strip().lower()
            for key, names in COLUMN_MAPPING.items():
                if key not in mapping:
                    for name in names:
                        if name in col_lower:
                            mapping[key] = col
                            break
        return mapping
    
    def _check_missing(self, mapping: dict):
        """Выдать ошибку если какие-то колонки не найдены."""
        missing = [k for k in REQUIRED_FIELDS if k not in mapping]
        if missing:
            raise KeyError(f'Missing columns: {missing}')
    
    def _parse_rows(self, df, mapping: dict) -> list:
        """Преобразовать строки DataFrame в список словарей."""
        data = []
        for _, row in df.iterrows():
            record = {}
            for key in REQUIRED_FIELDS:
                val = row[mapping[key]]
                if isinstance(val, str):
                    val = val.replace(',', '.')  # На случай если число с запятой
                record[key] = float(val)
            record['year'] = int(record['year'])
            data.append(record)
        return data


# SRP - этот класс ТОЛЬКО прогнозирует
class MovingAverageForecaster(IForecaster):
    """Прогнозирование методом скользящей средней."""
    
    def forecast(self, data: list, window: int, periods: int) -> list:
        """
        Построить прогноз на указанное количество периодов.
        
        Параметры:
            data - исторические значения (список чисел)
            window - размер окна для усреднения (n)
            periods - на сколько периодов прогнозировать
        
        Возвращает:
            Список спрогнозированных значений
        """
        result = []
        working = data.copy()
        for _ in range(periods):
            # Берём последние window значений и считаем среднее
            avg = sum(working[-window:]) / window
            result.append(avg)
            working.append(avg)  # Добавляем прогноз в данные для следующего шага
        return result


# SRP - этот класс ТОЛЬКО анализирует
class CrimeAnalyzer(IAnalyzer):
    """Анализ данных: какой тип преступности снизился/вырос больше всего."""
    
    def analyze(self, data: list) -> str:
        """Посчитать проценты изменения и вернуть строку-отчёт."""
        if len(data) < 2:
            return "Not enough data"
        
        first = data[0]    # Первый год
        last = data[-1]    # Последний год
        
        # Считаем процент изменения для каждого типа преступности
        changes = {}
        for field in REQUIRED_FIELDS[1:]:  # Пропускаем year
            if first[field] != 0:          # Избегаем деления на ноль
                changes[field] = ((last[field] - first[field]) / first[field]) * 100
        
        if not changes:
            return "No changes detected"
        
        # Находим что снизилось и что выросло больше всего
        most_decreased = min(changes, key=changes.get)
        most_increased = max(changes, key=changes.get)
        
        stats = (f"MAX DECREASE: {PLOT_CONFIG[most_decreased]['label']} = {changes[most_decreased]:.1f}%   |   "
                f"MAX INCREASE: {PLOT_CONFIG[most_increased]['label']} = +{changes[most_increased]:.1f}%")
        return stats


# Стили интерфейса - OCP (все стили в одном месте)
# Чтобы поменять тему - меняй только здесь
STYLE_QMAIN = "QMainWindow { background-color: #1a1a1a; }"

STYLE_BTN = """
    QPushButton {
        background-color: #2a2a2a; color: #999999;
        border: 1px solid #444444; padding: 12px 24px;
        font-size: 14px; font-family: 'Consolas'; text-transform: uppercase;
    }
    QPushButton:hover {
        background-color: #333333; color: #cccccc; border-color: #666666;
    }
    QPushButton:pressed {
        background-color: #1a1a1a; border-color: #555555;
    }
"""

STYLE_BTN_FORECAST = """
    QPushButton {
        background-color: #252525; color: #888888;
        border: 1px solid #555555; padding: 12px 28px;
        font-size: 14px; font-family: 'Consolas'; text-transform: uppercase;
    }
    QPushButton:hover {
        background-color: #2a2a2a; color: #aaaaaa; border-color: #777777;
    }
"""

STYLE_LABEL = "color: #888888; font-family: 'Consolas'; font-size: 13px;"

STYLE_SPIN = """
    QSpinBox {
        background-color: #252525; color: #cccccc;
        border: 1px solid #444444; padding: 7px;
        font-size: 14px; font-family: 'Consolas'; min-width: 65px;
    }
    QSpinBox:focus { border-color: #888888; }
"""

STYLE_TABLE = """
    QTableWidget {
        background-color: #1a1a1a; color: #cccccc;
        border: 1px solid #333333; gridline-color: #2a2a2a;
        font-family: 'Consolas'; font-size: 16px;
    }
    QTableWidget::item { padding: 10px; }
    QTableWidget::item:selected { background-color: #333333; color: #ffffff; }
    QHeaderView::section {
        background-color: #000000; color: #999999; font-weight: bold;
        padding: 14px; border: none; border-bottom: 2px solid #444444;
        font-family: 'Consolas'; font-size: 16px; text-transform: uppercase;
    }
"""

STYLE_STATS = """
    QLabel {
        background-color: #1e1e1e; color: #999999;
        padding: 16px; border: 1px solid #333333;
        font-family: 'Consolas'; font-size: 14px;
    }
"""

STYLE_FRAME = """
    QFrame {
        background-color: #000000; border: 1px solid #333333; padding: 5px;
    }
"""

STYLE_CONTROL_FRAME = """
    QFrame {
        background-color: #1e1e1e; border: 1px solid #333333; padding: 8px;
    }
"""


# Главное окно - SRP (ТОЛЬКО отрисовка интерфейса)
# Вся логика вынесена в сервисы (загрузчик, прогнозатор, анализатор)
class MainWindow(QMainWindow):
    """Главное окно приложения. Отвечает только за интерфейс."""
    
    def __init__(self, loader: IDataLoader, forecaster: IForecaster, analyzer: IAnalyzer):
        """
        Параметры:
            loader - сервис загрузки данных
            forecaster - сервис прогнозирования
            analyzer - сервис анализа
        """
        super().__init__()
        self._loader = loader          # Инкапсуляция: скрываем внутри класса
        self._forecaster = forecaster
        self._analyzer = analyzer
        self._data = []                # Загруженные данные
        self._init_ui()                # Строим интерфейс
        self._auto_load_data()         # Автозагрузка при старте
    
    def _init_ui(self):
        """Построить весь интерфейс: заголовок, кнопки, таблицу, график."""
        self.setWindowTitle('Crime Statistics in Russia (Variant 13)')
        self.setGeometry(100, 100, 1350, 920)
        self.setStyleSheet(STYLE_QMAIN)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Заголовок
        header_frame = QFrame()
        header_frame.setStyleSheet(STYLE_FRAME)
        h_layout = QVBoxLayout(header_frame)
        h1 = QLabel('CRIME STATISTICS IN RUSSIA')
        h1.setFont(QFont('Consolas', 22, QFont.Bold))
        h1.setStyleSheet("color: #cccccc; background: transparent; padding: 14px;")
        h1.setAlignment(Qt.AlignCenter)
        h_layout.addWidget(h1)
        h2 = QLabel('ANALYTICAL REPORT  |  2010-2024  |  FORECASTING BY MOVING AVERAGE')
        h2.setFont(QFont('Consolas', 12))
        h2.setStyleSheet("color: #666666; background: transparent; padding-bottom: 10px;")
        h2.setAlignment(Qt.AlignCenter)
        h_layout.addWidget(h2)
        layout.addWidget(header_frame)
        
        # Панель управления
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet(STYLE_CONTROL_FRAME)
        ctrl = QHBoxLayout(ctrl_frame)
        
        # Кнопка загрузки
        self._reload_btn = QPushButton('Load Data')
        self._reload_btn.setStyleSheet(STYLE_BTN)
        self._reload_btn.clicked.connect(self._auto_load_data)
        ctrl.addWidget(self._reload_btn)
        
        # Кнопка экспорта
        self._export_btn = QPushButton('Export Graph')
        self._export_btn.setStyleSheet(STYLE_BTN)
        self._export_btn.clicked.connect(self._save_plot)
        ctrl.addWidget(self._export_btn)
        
        ctrl.addStretch()
        
        # Размер окна прогноза (n)
        wlbl = QLabel('WINDOW (n):')
        wlbl.setStyleSheet(STYLE_LABEL)
        ctrl.addWidget(wlbl)
        
        self._window_spin = QSpinBox()
        self._window_spin.setRange(1, 10)
        self._window_spin.setValue(3)
        self._window_spin.setStyleSheet(STYLE_SPIN)
        ctrl.addWidget(self._window_spin)
        
        # Количество лет прогноза
        flbl = QLabel('FORECAST (years):')
        flbl.setStyleSheet(STYLE_LABEL)
        ctrl.addWidget(flbl)
        
        self._periods_spin = QSpinBox()
        self._periods_spin.setRange(1, 10)
        self._periods_spin.setValue(3)
        self._periods_spin.setStyleSheet(STYLE_SPIN)
        ctrl.addWidget(self._periods_spin)
        
        # Кнопка обновления прогноза
        self._forecast_btn = QPushButton('Update Forecast')
        self._forecast_btn.setStyleSheet(STYLE_BTN_FORECAST)
        self._forecast_btn.clicked.connect(self._plot_data)
        ctrl.addWidget(self._forecast_btn)
        
        layout.addWidget(ctrl_frame)

        # Таблица с данными
        self._table = QTableWidget()
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setFont(QFont('Consolas', 14))
        self._table.setStyleSheet(STYLE_TABLE)
        layout.addWidget(self._table, 2)
        
        # Строка статистики
        self._stats_label = QLabel()
        self._stats_label.setAlignment(Qt.AlignCenter)
        self._stats_label.setFont(QFont('Consolas', 13))
        self._stats_label.setMinimumHeight(55)
        self._stats_label.setStyleSheet(STYLE_STATS)
        layout.addWidget(self._stats_label)

        # График
        self._figure = Figure(figsize=(13, 5), facecolor='#1a1a1a')
        self._canvas = FigureCanvas(self._figure)
        layout.addWidget(self._canvas, 3)

        # Панель инструментов графика (зум, перемещение, сохранение)
        self._toolbar = NavigationToolbar2QT(self._canvas, self)
        layout.addWidget(self._toolbar)

    def _auto_load_data(self):
        """Загрузить данные из Excel-файла рядом со скриптом."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, 'crime_data.xlsx')
        
        try:
            self._data = self._loader.load(path)   # Используем сервис загрузки
            self._show_table()                      # Обновляем таблицу
            self._show_stats()                      # Обновляем статистику
            self._plot_data()                       # Рисуем график
        except FileNotFoundError:
            QMessageBox.critical(self, 'Error', f'File not found:\n{path}')
        except ValueError as e:
            QMessageBox.critical(self, 'Data Error', str(e))
        except KeyError as e:
            QMessageBox.critical(self, 'Column Error', str(e))
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))
    
    def _show_table(self):
        """Заполнить таблицу данными."""
        self._table.setRowCount(0)  # Очищаем перед заполнением
        self._table.setRowCount(len(self._data))
        self._table.setColumnCount(7)
        headers = ['Year', 'Murder', 'Robbery', 'Theft', 'Fraud', 'Drugs', 'Economic']
        self._table.setHorizontalHeaderLabels(headers)
        
        for i, row in enumerate(self._data):
            vals = [str(row['year'])] + [f"{row[f]:.1f}" for f in REQUIRED_FIELDS[1:]]
            for j, text in enumerate(vals):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(i, j, item)

    def _show_stats(self):
        """Показать результат анализа (что снизилось/выросло)."""
        text = self._analyzer.analyze(self._data)   # Используем сервис анализа
        self._stats_label.setText(text)
    
    def _plot_data(self):
        """Построить график с историческими данными и прогнозом."""
        if not self._data:
            return
        
        window = self._window_spin.value()
        periods = self._periods_spin.value()
        
        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.set_facecolor('#1a1a1a')   # Тёмный фон графика
        
        years = [d['year'] for d in self._data]
        
        # Рисуем каждый тип преступности своим цветом
        for field, cfg in PLOT_CONFIG.items():
            values = [d[field] for d in self._data]
            # Исторические данные — сплошная линия с точками
            ax.plot(years, values, 'o-', color=cfg['color'], label=cfg['label'],
                   markersize=5, linewidth=2)
            
            # Прогноз — пунктирная линия
            forecast = self._forecaster.forecast(values, window, periods)
            last = years[-1]
            fore_years = list(range(last + 1, last + periods + 1))
            ax.plot([last] + fore_years, [values[-1]] + forecast,
                   '--', color=cfg['color'], linewidth=2, alpha=0.4)
        
        # Оформление графика
        ax.set_xlabel('YEAR', color='#888888', fontsize=12, fontfamily='monospace')
        ax.set_ylabel('CRIMES (thousands)', color='#888888', fontsize=12, fontfamily='monospace')
        ax.set_title(f'CRIME DYNAMICS & FORECAST (n={window})',
                    color='#aaaaaa', fontsize=14, fontfamily='monospace')
        ax.legend(loc='upper left', fontsize=10, facecolor='#1a1a1a',
                 edgecolor='#444444', labelcolor='#cccccc')
        ax.grid(True, alpha=0.12, color='#444444')
        ax.tick_params(colors='#888888', labelsize=10, rotation=0)
        ax.spines['bottom'].set_color('#444444')
        ax.spines['left'].set_color('#444444')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        self._figure.tight_layout()
        self._canvas.draw()
    
    def _save_plot(self):
        """Сохранить график в файл (PNG, PDF, SVG)."""
        if not self._data:
            QMessageBox.warning(self, 'Warning', 'No data to save')
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, 'Save Graph', 'crime_graph.png',
            'PNG (*.png);;PDF (*.pdf);;SVG (*.svg)'
        )
        if path:
            try:
                self._figure.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
            except Exception as e:
                QMessageBox.critical(self, 'Save Error', str(e))


# Точка входа
if __name__ == '__main__':
    loader = ExcelDataLoader()          # Создаём сервис загрузки
    forecaster = MovingAverageForecaster()  # Создаём сервис прогноза
    analyzer = CrimeAnalyzer()          # Создаём сервис анализа
    
    app = QApplication(sys.argv)
    window = MainWindow(loader, forecaster, analyzer)  # Передаём сервисы в окно
    window.show()
    sys.exit(app.exec_())