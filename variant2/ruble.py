import sys, os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QBrush
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import pandas as pd


class MovingAverageCalculator:
    """Расчет скользящей средней и прогноза"""
    def __init__(self):
        pass
    
    def calculate_moving_average(self, data, period):
        # Вычисляет скользящую среднюю: для каждого элемента берет среднее арифметическое с period-1 предыдущими
        if len(data) < period:
            return [None] * len(data)
        result = [None] * (period - 1)
        for i in range(period - 1, len(data)):
            result.append(sum(data[i-period+1:i+1]) / period)
        return result
    
    def forecast(self, data, period, n_days):
        # Прогнозирует следующие n_days значений, последовательно добавляя рассчитанные средние в данные
        if len(data) < period:
            return [None] * n_days
        forecast_values = []
        extended_data = data.copy()
        for _ in range(n_days):
            extended_data.append(sum(extended_data[-period:]) / period)
            forecast_values.append(extended_data[-1])
        return forecast_values


class DataManager:
    """Управление данными: загрузка, фильтрация и расчет статистики"""
    def __init__(self):
        self.data = []
    
    def load_from_excel(self, file_path):
        # Загружает данные из Excel-файла с колонками Date, RUB_USD, RUB_EUR 
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        df = pd.read_excel(file_path)
        if df.empty:
            raise ValueError("Файл не содержит данных")
        
        required = ['Date', 'RUB_USD', 'RUB_EUR']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Отсутствуют колонки: {missing}")
        
        self.data = []
        for _, row in df.iterrows():
            date_str = str(row['Date']).split()[0]
            usd_val = float(str(row['RUB_USD']).replace(',', '.'))
            eur_val = float(str(row['RUB_EUR']).replace(',', '.'))
            self.data.append({'date': date_str, 'usd': usd_val, 'eur': eur_val})
        
        return self.data
    
    def filter_by_period(self, period_text):
        # Возвращает последние N дней данных в зависимости от выбранного периода фильтрации
        if not self.data or period_text == 'Все данные':
            return self.data.copy()
        
        days_map = {'Последние 7 дней': 7, 'Последние 14 дней': 14, 
                    'Последние 30 дней': 30, 'Последние 90 дней': 90}
        days = days_map.get(period_text, len(self.data))
        return self.data[-days:]
    
    def get_stats(self):
        # Рассчитывает максимальный рост и падение курса USD и EUR с указанием дат
        if len(self.data) < 2:
            return None
        
        usd_changes = [self.data[i]['usd'] - self.data[i-1]['usd'] for i in range(1, len(self.data))]
        eur_changes = [self.data[i]['eur'] - self.data[i-1]['eur'] for i in range(1, len(self.data))]
        
        max_usd = max(usd_changes)
        min_usd = min(usd_changes)
        max_eur = max(eur_changes)
        min_eur = min(eur_changes)
        
        return {
            'usd_max': max_usd, 'usd_max_date': self.data[usd_changes.index(max_usd) + 1]['date'],
            'usd_min': min_usd, 'usd_min_date': self.data[usd_changes.index(min_usd) + 1]['date'],
            'eur_max': max_eur, 'eur_max_date': self.data[eur_changes.index(max_eur) + 1]['date'],
            'eur_min': min_eur, 'eur_min_date': self.data[eur_changes.index(min_eur) + 1]['date']
        }


class ChartRenderer:
    """Отрисовка графиков: скользящая средняя и прогноз"""
    
    def __init__(self, figure, canvas, calculator):
        self.figure = figure
        self.canvas = canvas
        self.calc = calculator
    
    def render(self, data, period, n_forecast):
        # Строит на графике линии курсов USD/EUR, их скользящие средние и прогноз с серой зоной
        if not data:
            return
        
        self.figure.clear()
        
        dates = [d['date'] for d in data]
        usd = [d['usd'] for d in data]
        eur = [d['eur'] for d in data]
        
        # Короткие даты 
        short_dates = []
        for d in dates:
            parts = d.split('-')
            short_dates.append(f"{parts[2]}.{parts[1]}" if len(parts) == 3 else d)
        
        x = list(range(len(dates)))
        ax = self.figure.add_subplot(111)
        
        # Синий для USD, красный для EUR
        ax.plot(x, usd, 'b-o', label='USD/RUB', markersize=3, linewidth=1.5, alpha=0.7)
        ax.plot(x, eur, 'r-o', label='EUR/RUB', markersize=3, linewidth=1.5, alpha=0.7)
        
        # Скользящая средняя (пунктирные линии)
        if len(usd) >= period:
            ma_usd = self.calc.calculate_moving_average(usd, period)
            ma_eur = self.calc.calculate_moving_average(eur, period)
            
            x_ma = [x[i] for i in range(len(ma_usd)) if ma_usd[i] is not None]
            y_ma_usd = [ma_usd[i] for i in range(len(ma_usd)) if ma_usd[i] is not None]
            y_ma_eur = [ma_eur[i] for i in range(len(ma_eur)) if ma_eur[i] is not None]
            
            ax.plot(x_ma, y_ma_usd, 'b--', linewidth=2, label=f'Ск. средняя USD (n={period})', alpha=0.8)
            ax.plot(x_ma, y_ma_eur, 'r--', linewidth=2, label=f'Ск. средняя EUR (n={period})', alpha=0.8)
        
        # Прогноз 
        if len(usd) >= period:
            usd_forecast = self.calc.forecast(usd, period, n_forecast)
            eur_forecast = self.calc.forecast(eur, period, n_forecast)
            
            forecast_x = list(range(len(x), len(x) + n_forecast))
            forecast_x_line = [len(x) - 1] + forecast_x
            usd_line = [usd[-1]] + usd_forecast
            eur_line = [eur[-1]] + eur_forecast
            
            ax.plot(forecast_x_line, usd_line, 'c:', linewidth=2.5, marker='s', markersize=4, 
                   label=f'Прогноз USD ({n_forecast} дн.)', alpha=0.9)
            ax.plot(forecast_x_line, eur_line, 'm:', linewidth=2.5, marker='s', markersize=4, 
                   label=f'Прогноз EUR ({n_forecast} дн.)', alpha=0.9)
            
            ax.axvspan(forecast_x[0] - 1, forecast_x[-1], alpha=0.15, color='gray', label='Прогноз')
        
        # Настройки осей и отображения
        step = max(1, len(x) // 12)
        ax.set_xticks(x[::step])
        ax.set_xticklabels([short_dates[i] for i in x[::step]], rotation=45, ha='right', fontsize=8)
        ax.set_xlabel('Дата')
        ax.set_ylabel('Курс (руб.)')
        ax.set_title(f'Курс рубля к USD и EUR (период={period}, прогноз на {n_forecast} дн.)')
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
        self.canvas.draw()


class TableRenderer:
    """Отображение таблицы с данными и цветовой подсветкой изменений курса"""
    def __init__(self, table_widget):
        self.table = table_widget
    
    def render(self, data):
        # Заполняет таблицу датами и курсами, выделяя красным рост и зеленым падение более чем на 1 рубль
        if not data:
            self.table.setRowCount(0)
            return
        
        self.table.setRowCount(len(data))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Дата', 'USD/RUB', 'EUR/RUB'])
        
        for i, row in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(row['date']))
            
            usd_item = QTableWidgetItem(f"{row['usd']:.2f}")
            eur_item = QTableWidgetItem(f"{row['eur']:.2f}")
            self.table.setItem(i, 1, usd_item)
            self.table.setItem(i, 2, eur_item)
            
            if i > 0:
                usd_diff = abs(row['usd'] - data[i-1]['usd'])
                if usd_diff >= 1.0:
                    color = QColor(255, 160, 160) if row['usd'] > data[i-1]['usd'] else QColor(144, 238, 144)
                    usd_item.setBackground(QBrush(color))
                
                eur_diff = abs(row['eur'] - data[i-1]['eur'])
                if eur_diff >= 1.0:
                    color = QColor(255, 160, 160) if row['eur'] > data[i-1]['eur'] else QColor(144, 238, 144)
                    eur_item.setBackground(QBrush(color))


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        
        self.data_manager = DataManager()
        self.calculator = MovingAverageCalculator()
        self.table_renderer = None
        
        self.init_ui()
        self.auto_load_data()
    
    def init_ui(self):
        # Создает интерфейс: панель управления, таблицу, панель статистики и график 
        self.setWindowTitle('Анализ курса рубля к USD и EUR')
        self.setGeometry(100, 100, 1400, 900)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Панель управления
        control = QHBoxLayout()
        
        load_btn = QPushButton('Обновить данные')
        load_btn.clicked.connect(self.auto_load_data)
        control.addWidget(load_btn)
        
        control.addWidget(QLabel("Период:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(['Все данные', 'Последние 7 дней', 'Последние 14 дней', 
                                    'Последние 30 дней', 'Последние 90 дней'])
        self.period_combo.currentTextChanged.connect(self.update_plot)
        control.addWidget(self.period_combo)
        
        control.addWidget(QLabel("Период скользящей средней:"))
        self.period_spin = QSpinBox()
        self.period_spin.setRange(2, 30)
        self.period_spin.setValue(5)
        self.period_spin.valueChanged.connect(self.update_plot)
        control.addWidget(self.period_spin)
        
        control.addWidget(QLabel("Прогноз на дней:"))
        self.forecast_spin = QSpinBox()
        self.forecast_spin.setRange(1, 30)
        self.forecast_spin.setValue(7)
        self.forecast_spin.valueChanged.connect(self.update_plot)
        control.addWidget(self.forecast_spin)
        
        layout.addLayout(control)
        
        # Таблица
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_renderer = TableRenderer(self.table)
        layout.addWidget(self.table, 1)
        
        # Статистика 
        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setFont(QFont('Arial', 11, QFont.Bold))
        self.stats_label.setStyleSheet("background-color: #2b5b84; color: white; padding: 12px; border-radius: 5px;")
        self.stats_label.setMinimumHeight(50)
        layout.addWidget(self.stats_label)
        
        # График
        self.figure = Figure(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.chart_renderer = ChartRenderer(self.figure, self.canvas, self.calculator)
        
        # Удаляем лишние кнопки с панели инструментов
        for action in self.toolbar.actions():
            if action.text() in ('Configure subplots', 'Customize', 'Subplots'):
                self.toolbar.removeAction(action)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, 3)
    
    def auto_load_data(self):
        # Автоматически загружает данные из файла currency_data.xlsx 
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'currency_data.xlsx')
        
        try:
            self.data_manager.load_from_excel(file_path)
            self.table_renderer.render(self.data_manager.data)
            self.show_stats()
            self.update_plot()
            self.statusBar().showMessage(f'Загружено {len(self.data_manager.data)} дней')
        except FileNotFoundError as e:
            QMessageBox.warning(self, 'Ошибка', f'{e}\n\nСоздайте файл currency_data.xlsx с колонками: Date, RUB_USD, RUB_EUR')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', str(e))
    
    def show_stats(self):
        # Отображает в панели статистики максимумы и минимумы курсов, а также прогнозные значения
        stats = self.data_manager.get_stats()
        if not stats:
            self.stats_label.setText("Недостаточно данных")
            return
        
        period = self.period_spin.value()
        n_days = self.forecast_spin.value()
        
        forecast_text = ""
        if len(self.data_manager.data) >= period:
            usd_vals = [d['usd'] for d in self.data_manager.data]
            eur_vals = [d['eur'] for d in self.data_manager.data]
            usd_f = self.calculator.forecast(usd_vals, period, n_days)
            eur_f = self.calculator.forecast(eur_vals, period, n_days)
            
            forecast_text = f"\n\nПрогноз (период = {period} дн.): USD через {n_days} дн. -> {usd_f[-1]:.2f} " + \
                           f"(изм: {usd_f[-1] - usd_vals[-1]:+.2f}) | " + \
                           f"EUR через {n_days} дн. -> {eur_f[-1]:.2f} " + \
                           f"(изм: {eur_f[-1] - eur_vals[-1]:+.2f})"
        
        text = (f"USD: максимум +{stats['usd_max']:.2f} руб ({stats['usd_max_date']}) | "
                f"минимум {stats['usd_min']:.2f} руб ({stats['usd_min_date']})   ||   "
                f"EUR: максимум +{stats['eur_max']:.2f} руб ({stats['eur_max_date']}) | "
                f"минимум {stats['eur_min']:.2f} руб ({stats['eur_min_date']}){forecast_text}")
        
        self.stats_label.setText(text)
    
    def update_plot(self):
        # Применяет фильтр по периоду и обновляет график с новыми параметрами прогноза
        if not self.data_manager.data:
            return
        
        filtered = self.data_manager.filter_by_period(self.period_combo.currentText())
        if not filtered:
            return
        
        self.chart_renderer.render(filtered, self.period_spin.value(), self.forecast_spin.value())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())