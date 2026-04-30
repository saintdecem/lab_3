import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel,
    QSpinBox, QFileDialog, QHeaderView, QGroupBox, QComboBox,
    QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QBrush
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import pandas as pd


class MovingAverageCalculator:
    """Класс для расчета скользящей средней и прогнозирования."""
    
    def calculate_moving_average(self, data, period):
        """Рассчитывает скользящую среднюю для ряда данных."""
        if len(data) < period:
            return [None] * len(data)
        
        result = [None] * (period - 1)
        for i in range(period - 1, len(data)):
            window = data[i - period + 1:i + 1]
            result.append(sum(window) / period)
        
        return result
    
    def forecast(self, data, period, n_days):
        """Прогнозирует следующие N дней методом скользящей средней."""
        if len(data) < period:
            return [None] * n_days
        
        forecast_values = []
        extended_data = data.copy()
        
        for _ in range(n_days):
            window = extended_data[-period:]
            next_val = sum(window) / period
            forecast_values.append(next_val)
            extended_data.append(next_val)
        
        return forecast_values


class MainWindow(QMainWindow):
    """Главное окно приложения для анализа валютных курсов."""
    
    def __init__(self):
        super().__init__()
        self.data = []
        self.filtered_data = []
        self.calculator = MovingAverageCalculator()
        self.init_ui()
        self.auto_load_data()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        self.setWindowTitle('Анализ курса рубля к USD и EUR с прогнозированием')
        self.setGeometry(100, 100, 1400, 900)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Панель управления
        control_panel = QHBoxLayout()
        
        # Группа загрузки данных
        load_group = QGroupBox("Загрузка")
        load_layout = QHBoxLayout()
        self.reload_btn = QPushButton('Обновить данные')
        self.reload_btn.clicked.connect(self.auto_load_data)
        load_layout.addWidget(self.reload_btn)
        load_group.setLayout(load_layout)
        control_panel.addWidget(load_group)
        
        # Группа настройки отображения
        plot_group = QGroupBox("Отображение")
        plot_layout = QHBoxLayout()
        
        plot_layout.addWidget(QLabel("Период:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(['Все данные', 'Последние 7 дней', 'Последние 14 дней', 
                                    'Последние 30 дней', 'Последние 90 дней'])
        self.period_combo.currentTextChanged.connect(self.update_plot)
        plot_layout.addWidget(self.period_combo)
        
        plot_group.setLayout(plot_layout)
        control_panel.addWidget(plot_group)
        
        forecast_group = QGroupBox("Прогнозирование")
        forecast_layout = QHBoxLayout()
        
        forecast_layout.addWidget(QLabel("Период скользящей средней:"))
        self.avg_period_spin = QSpinBox()
        self.avg_period_spin.setRange(2, 30)
        self.avg_period_spin.setValue(5)
        self.avg_period_spin.setToolTip("Количество предыдущих дней для расчета среднего")
        self.avg_period_spin.valueChanged.connect(self.update_plot)
        forecast_layout.addWidget(self.avg_period_spin)
        
        forecast_layout.addWidget(QLabel("Прогноз на дней:"))
        self.forecast_days_spin = QSpinBox()
        self.forecast_days_spin.setRange(1, 30)
        self.forecast_days_spin.setValue(7)
        self.forecast_days_spin.setToolTip("Количество дней для прогноза")
        self.forecast_days_spin.valueChanged.connect(self.update_plot)
        forecast_layout.addWidget(self.forecast_days_spin)
        
        forecast_group.setLayout(forecast_layout)
        control_panel.addWidget(forecast_group)
        
        main_layout.addLayout(control_panel)
        
        # Таблица данных
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.table, 1)
        
        # Статистическая информация
        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setFont(QFont('Arial', 11))
        self.stats_label.setStyleSheet("""
            QLabel {background-color: #2b5b84; color: white; padding: 12px; border-radius: 5px; font-weight: bold;}
        """)
        self.stats_label.setMinimumHeight(50)
        main_layout.addWidget(self.stats_label)
        
        # График
        self.figure = Figure(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        
        # Панель инструментов для навигации по графику 
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Удаление ненужных кнопок
        for action in self.toolbar.actions():
            text = action.text()
            if text in ('Configure subplots', 'Customize', 'Subplots'):
                self.toolbar.removeAction(action)
        
        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.canvas, 3)
    
    def filter_data_by_period(self, period_text):
        """Фильтрует данные по выбранному временному периоду."""
        if not self.data:
            return []
        
        if period_text == 'Все данные':
            return self.data
        
        days_map = {
            'Последние 7 дней': 7,
            'Последние 14 дней': 14,
            'Последние 30 дней': 30,
            'Последние 90 дней': 90
        }
        
        days = days_map.get(period_text, len(self.data))
        return self.data[-days:]
    
    def auto_load_data(self):
        """Автоматическая загрузка данных из Excel-файла."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'currency_data.xlsx')
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, 'Предупреждение', 
                               f'Файл не найден: {file_path}\n\n'
                               'Создайте файл currency_data.xlsx в папке с программой.\n'
                               'Колонки: Date, RUB_USD, RUB_EUR')
            return
        
        try:
            df = pd.read_excel(file_path)
            
            if df.empty:
                QMessageBox.warning(self, 'Предупреждение', 'Файл не содержит данных.')
                return
            
            required = ['Date', 'RUB_USD', 'RUB_EUR']
            missing = [col for col in required if col not in df.columns]
            if missing:
                QMessageBox.warning(self, 'Предупреждение', f'Отсутствуют колонки: {missing}')
                return
            
            self.data = []
            for _, row in df.iterrows():
                date_str = str(row['Date']).split()[0]
                usd_val = row['RUB_USD']
                eur_val = row['RUB_EUR']
                
                if isinstance(usd_val, str):
                    usd_val = float(usd_val.replace(',', '.'))
                if isinstance(eur_val, str):
                    eur_val = float(eur_val.replace(',', '.'))
                
                self.data.append({
                    'date': date_str,
                    'usd': float(usd_val),
                    'eur': float(eur_val)
                })
            
            self.show_table()
            self.show_stats()
            self.update_plot()
            self.statusBar().showMessage(f'Загружено {len(self.data)} дней')
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки: {e}')
    
    def show_table(self):
        """Отображение данных в табличном виде с цветовой индикацией изменений."""
        self.table.setRowCount(len(self.data))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Дата', 'USD/RUB', 'EUR/RUB'])
        
        for i, row in enumerate(self.data):
            date_item = QTableWidgetItem(row['date'])
            self.table.setItem(i, 0, date_item)
            
            usd_item = QTableWidgetItem(f"{row['usd']:.2f}")
            self.table.setItem(i, 1, usd_item)
            
            eur_item = QTableWidgetItem(f"{row['eur']:.2f}")
            self.table.setItem(i, 2, eur_item)
            
            # Подсветка значительных изменений курса
            if i > 0:
                usd_prev = self.data[i-1]['usd']
                usd_curr = row['usd']
                usd_diff = abs(usd_curr - usd_prev)
                
                if usd_diff >= 1.0:
                    if usd_curr > usd_prev:
                        usd_item.setBackground(QBrush(QColor(255, 160, 160)))
                    elif usd_curr < usd_prev:
                        usd_item.setBackground(QBrush(QColor(144, 238, 144)))
            
            if i > 0:
                eur_prev = self.data[i-1]['eur']
                eur_curr = row['eur']
                eur_diff = abs(eur_curr - eur_prev)
                
                if eur_diff >= 1.0:
                    if eur_curr > eur_prev:
                        eur_item.setBackground(QBrush(QColor(255, 160, 160)))
                    elif eur_curr < eur_prev:
                        eur_item.setBackground(QBrush(QColor(144, 238, 144)))
    
    def show_stats(self):
        """Расчет и отображение статистических показателей."""
        if len(self.data) < 2:
            self.stats_label.setText("Недостаточно данных для статистики")
            return
        
        # Анализ изменений курса USD
        usd_changes = []
        for i in range(1, len(self.data)):
            change = self.data[i]['usd'] - self.data[i-1]['usd']
            usd_changes.append(change)
        
        max_usd_gain = max(usd_changes)
        max_usd_loss = min(usd_changes)
        gain_day = self.data[usd_changes.index(max_usd_gain) + 1]['date']
        loss_day = self.data[usd_changes.index(max_usd_loss) + 1]['date']
        
        # Анализ изменений курса EUR
        eur_changes = []
        for i in range(1, len(self.data)):
            change = self.data[i]['eur'] - self.data[i-1]['eur']
            eur_changes.append(change)
        
        max_eur_gain = max(eur_changes)
        max_eur_loss = min(eur_changes)
        gain_day_eur = self.data[eur_changes.index(max_eur_gain) + 1]['date']
        loss_day_eur = self.data[eur_changes.index(max_eur_loss) + 1]['date']
        
        # Прогнозная статистика
        forecast_text = ""
        period = self.avg_period_spin.value()
        if len(self.data) >= period:
            usd_values = [d['usd'] for d in self.data]
            eur_values = [d['eur'] for d in self.data]
            n_days = self.forecast_days_spin.value()
            
            usd_forecast = self.calculator.forecast(usd_values, period, n_days)
            eur_forecast = self.calculator.forecast(eur_values, period, n_days)
            
            last_usd = usd_values[-1]
            last_eur = eur_values[-1]
            
            forecast_text = f"\n\nПрогноз (период = {period} дней):"
            forecast_text += f" USD через {n_days} дн. -> {usd_forecast[-1]:.2f} "
            forecast_text += f"(изменение: {usd_forecast[-1] - last_usd:+.2f}) | "
            forecast_text += f"EUR через {n_days} дн. -> {eur_forecast[-1]:.2f} "
            forecast_text += f"(изменение: {eur_forecast[-1] - last_eur:+.2f})"
        
        stats = (f"USD: максимум +{max_usd_gain:.2f} руб ({gain_day}) | "
                f"минимум {max_usd_loss:.2f} руб ({loss_day})   ||   "
                f"EUR: максимум +{max_eur_gain:.2f} руб ({gain_day_eur}) | "
                f"минимум {max_eur_loss:.2f} руб ({loss_day_eur}){forecast_text}")
        self.stats_label.setText(stats)
    
    def update_plot(self):
        """Обновление графического отображения с учетом фильтрации и прогноза."""
        if not self.data:
            return
        
        self.filtered_data = self.filter_data_by_period(self.period_combo.currentText())
        
        if not self.filtered_data:
            return
        
        self.figure.clear()
        
        period = self.avg_period_spin.value()
        n_forecast = self.forecast_days_spin.value()
        
        dates_full = [d['date'] for d in self.filtered_data]
        usd = [d['usd'] for d in self.filtered_data]
        eur = [d['eur'] for d in self.filtered_data]
        
        # Преобразуем даты для отображения без года
        dates_short = []
        for date_str in dates_full:
            parts = date_str.split('-')
            if len(parts) == 3:
                # Формат: день.месяц (без года)
                dates_short.append(f"{parts[2]}.{parts[1]}")
            else:
                dates_short.append(date_str)
        
        x = list(range(len(dates_full)))
        
        ax = self.figure.add_subplot(111)
        
        # Отображение исторических данных
        ax.plot(x, usd, 'b-o', label='USD/RUB (история)', markersize=3, linewidth=1.5, alpha=0.7)
        ax.plot(x, eur, 'r-o', label='EUR/RUB (история)', markersize=3, linewidth=1.5, alpha=0.7)
        
        # Расчет и отображение скользящей средней для USD
        if len(usd) >= period:
            sliding_avg_usd = self.calculator.calculate_moving_average(usd, period)
            avg_x = [x[i] for i in range(len(sliding_avg_usd)) if sliding_avg_usd[i] is not None]
            avg_y = [sliding_avg_usd[i] for i in range(len(sliding_avg_usd)) if sliding_avg_usd[i] is not None]
            ax.plot(avg_x, avg_y, 'b--', linewidth=2, label=f'Скользящая средняя USD (n={period})', alpha=0.8)
        
        # Расчет и отображение скользящей средней для EUR
        if len(eur) >= period:
            sliding_avg_eur = self.calculator.calculate_moving_average(eur, period)
            avg_x_e = [x[i] for i in range(len(sliding_avg_eur)) if sliding_avg_eur[i] is not None]
            avg_y_e = [sliding_avg_eur[i] for i in range(len(sliding_avg_eur)) if sliding_avg_eur[i] is not None]
            ax.plot(avg_x_e, avg_y_e, 'r--', linewidth=2, label=f'Скользящая средняя EUR (n={period})', alpha=0.8)
        
        # Прогнозирование
        if len(usd) >= period:
            usd_forecast = self.calculator.forecast(usd, period, n_forecast)
            eur_forecast = self.calculator.forecast(eur, period, n_forecast)
            
            forecast_x = list(range(len(x), len(x) + n_forecast))
            forecast_x_with_last = [len(x) - 1] + forecast_x
            usd_forecast_with_last = [usd[-1]] + usd_forecast
            eur_forecast_with_last = [eur[-1]] + eur_forecast
            
            ax.plot(forecast_x_with_last, usd_forecast_with_last, 'c:', linewidth=2.5, 
                   marker='s', markersize=4, label=f'Прогноз USD (на {n_forecast} дн.)', alpha=0.9)
            ax.plot(forecast_x_with_last, eur_forecast_with_last, 'm:', linewidth=2.5, 
                   marker='s', markersize=4, label=f'Прогноз EUR (на {n_forecast} дн.)', alpha=0.9)
            
            # Визуальное выделение зоны прогноза
            ax.axvspan(len(x) - 0.5, len(x) + n_forecast - 0.5, alpha=0.1, color='gray', label='Зона прогноза')
        
        # Настройка подписей оси X с короткими датами
        step = max(1, len(x) // 12)
        ax.set_xticks(x[::step])
        ax.set_xticklabels([dates_short[i] for i in x[::step]], rotation=45, ha='right', fontsize=8)
        
        ax.set_xlabel('Дата')
        ax.set_title(f'Динамика курса рубля к USD и EUR (прогноз методом скользящей средней, период = {period} дней)')
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
        self.canvas.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())