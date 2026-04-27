import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel,
    QSpinBox, QMessageBox, QFileDialog, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QBrush
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = []
        self.init_ui()
        self.auto_load_data()
    
    def init_ui(self):
        self.setWindowTitle('Курс рубля к USD и EUR')
        self.setGeometry(100, 100, 1200, 900)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.reload_btn = QPushButton('Обновить данные')
        self.reload_btn.clicked.connect(self.auto_load_data)
        btn_layout.addWidget(self.reload_btn)
        
        self.export_btn = QPushButton('Сохранить график')
        self.export_btn.clicked.connect(self.save_plot)
        btn_layout.addWidget(self.export_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Таблица
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table, 2)
        
        # Статистика
        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setFont(QFont('Arial', 11))
        self.stats_label.setStyleSheet("""
            QLabel { 
                background-color: #2b5b84; 
                color: white; 
                padding: 12px; 
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        self.stats_label.setMinimumHeight(50)
        layout.addWidget(self.stats_label)
        
        # График
        self.figure = Figure(figsize=(12, 5))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas, 3)
    
    def auto_load_data(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'currency_data.xlsx')
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, 'Предупреждение', 
                               f'Файл не найден: {file_path}\n\n'
                               'Создайте файл currency_data.xlsx в папке с программой.\n'
                               'Колонки: Date, RUB_USD, RUB_EUR')
            return
        
        try:
            if os.path.getsize(file_path) == 0:
                QMessageBox.warning(self, 'Предупреждение', 'Файл пустой.')
                return
            
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
            self.plot_data()
            self.statusBar().showMessage(f'Загружено {len(self.data)} дней')
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки: {e}')
    
    def show_table(self):
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
            
            if i > 0:
                usd_prev = self.data[i-1]['usd']
                usd_curr = row['usd']
                usd_diff = abs(usd_curr - usd_prev)
                
                if usd_diff >= 1.0:
                    if usd_curr > usd_prev:
                        usd_item.setBackground(QBrush(QColor(255, 160, 160)))  # КРАСНЫЙ (курс вырос)
                    elif usd_curr < usd_prev:
                        usd_item.setBackground(QBrush(QColor(144, 238, 144)))  # ЗЕЛЕНЫЙ (курс упал)
            
            if i > 0:
                eur_prev = self.data[i-1]['eur']
                eur_curr = row['eur']
                eur_diff = abs(eur_curr - eur_prev)
                
                if eur_diff >= 1.0:
                    if eur_curr > eur_prev:
                        eur_item.setBackground(QBrush(QColor(255, 160, 160)))  # КРАСНЫЙ (курс вырос)
                    elif eur_curr < eur_prev:
                        eur_item.setBackground(QBrush(QColor(144, 238, 144)))  # ЗЕЛЕНЫЙ (курс упал)
    
    def show_stats(self):
        if len(self.data) < 2:
            self.stats_label.setText("Недостаточно данных для статистики")
            return
        
        # USD
        usd_changes = []
        for i in range(1, len(self.data)):
            change = self.data[i]['usd'] - self.data[i-1]['usd']
            usd_changes.append(change)
        
        max_usd_gain = max(usd_changes)
        max_usd_loss = min(usd_changes)
        gain_day = self.data[usd_changes.index(max_usd_gain) + 1]['date']
        loss_day = self.data[usd_changes.index(max_usd_loss) + 1]['date']
        
        # EUR
        eur_changes = []
        for i in range(1, len(self.data)):
            change = self.data[i]['eur'] - self.data[i-1]['eur']
            eur_changes.append(change)
        
        max_eur_gain = max(eur_changes)
        max_eur_loss = min(eur_changes)
        gain_day_eur = self.data[eur_changes.index(max_eur_gain) + 1]['date']
        loss_day_eur = self.data[eur_changes.index(max_eur_loss) + 1]['date']
        
        stats = (f"USD: ▲ +{max_usd_gain:.2f} руб ({gain_day}) | "
                f"▼ {max_usd_loss:.2f} руб ({loss_day})   ||   "
                f"EUR: ▲ +{max_eur_gain:.2f} руб ({gain_day_eur}) | "
                f"▼ {max_eur_loss:.2f} руб ({loss_day_eur})")
        self.stats_label.setText(stats)
    
    def plot_data(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        dates = [d['date'] for d in self.data]
        usd = [d['usd'] for d in self.data]
        eur = [d['eur'] for d in self.data]
        
        x = list(range(len(dates)))
        
        ax.plot(x, usd, 'b-o', label='USD/RUB', markersize=4, linewidth=2)
        ax.plot(x, eur, 'r-o', label='EUR/RUB', markersize=4, linewidth=2)
        
        step = max(1, len(dates) // 12)
        ax.set_xticks(x[::step])
        ax.set_xticklabels([dates[i] for i in x[::step]], rotation=45, ha='right', fontsize=8)
        
        ax.set_xlabel('Дата')
        ax.set_ylabel('Курс (RUB)')
        ax.set_title('Курс рубля к USD и EUR')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def save_plot(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Сохранить график', 'currency_graph.png', 
            'PNG (*.png);;PDF (*.pdf);;SVG (*.svg)'
        )
        if file_path:
            self.figure.savefig(file_path, dpi=150, bbox_inches='tight')
            QMessageBox.information(self, 'Готово', f'Сохранено: {file_path}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())