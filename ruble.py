import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel,
    QSpinBox, QMessageBox, QFileDialog, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
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
        
        btn_layout.addWidget(QLabel('Размер окна (n):'))
        self.window_spin = QSpinBox()
        self.window_spin.setRange(2, 10)
        self.window_spin.setValue(3)
        self.window_spin.setToolTip('Количество дней для расчета скользящей средней')
        btn_layout.addWidget(self.window_spin)
        
        btn_layout.addWidget(QLabel('Дней прогноза:'))
        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 14)
        self.days_spin.setValue(5)
        btn_layout.addWidget(self.days_spin)
        
        self.forecast_btn = QPushButton('Показать прогноз')
        self.forecast_btn.setEnabled(False)
        btn_layout.addWidget(self.forecast_btn)
        
        self.reset_btn = QPushButton('Сбросить прогноз')
        self.reset_btn.setEnabled(False)
        btn_layout.addWidget(self.reset_btn)
        
        self.export_btn = QPushButton('Сохранить график')
        self.export_btn.setEnabled(False)
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
    
    def auto_load_data(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'currency_data.xlsx')
        
        if not os.path.exists(file_path):
            file_path = 'currency_data.xlsx'
        
        try:
            # Читаем Excel
            df = pd.read_excel(file_path)
            
            self.data = []
            for _, row in df.iterrows():
                # Преобразуем дату
                date_str = str(row['Date'])
                if ' ' in date_str:
                    date_str = date_str.split()[0]
                
                # Преобразуем числа (могут быть с запятой или точкой)
                usd_val = row['RUB_USD']
                eur_val = row['RUB_EUR']
                
                # Если строка, заменяем запятую на точку
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
            self.statusBar().showMessage(f'Загружено {len(self.data)} дней')
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки: {e}')
    
    def show_table(self):
        self.table.setRowCount(len(self.data))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Дата', 'USD/RUB', 'EUR/RUB'])
        
        for i, row in enumerate(self.data):
            self.table.setItem(i, 0, QTableWidgetItem(row['date']))
            self.table.setItem(i, 1, QTableWidgetItem(f"{row['usd']:.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{row['eur']:.2f}"))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())