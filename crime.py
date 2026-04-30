import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel,
    QSpinBox, QMessageBox, QFileDialog, QHeaderView, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd

from matplotlib.dates import DateFormatter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = []
        self.init_ui()
        self.auto_load_data()
    
    def init_ui(self):
        self.setWindowTitle('Crime Statistics in Russia (Variant 13)')
        self.setGeometry(100, 100, 1350, 920)
        
        # ===== STRICT DARK STYLE =====
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # ===== HEADER =====
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #000000;
                border: 1px solid #333333;
                padding: 5px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        header = QLabel('CRIME STATISTICS IN RUSSIA')
        header.setFont(QFont('Consolas', 18, QFont.Bold))
        header.setStyleSheet("color: #cccccc; background: transparent; padding: 12px;")
        header.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(header)
        
        subheader = QLabel('ANALYTICAL REPORT  |  2010-2024  |  FORECASTING BY MOVING AVERAGE')
        subheader.setFont(QFont('Consolas', 10))
        subheader.setStyleSheet("color: #666666; background: transparent; padding-bottom: 10px;")
        subheader.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subheader)
        
        layout.addWidget(header_frame)
        
        # ===== CONTROL PANEL =====
        control_frame = QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                padding: 8px;
            }
        """)
        ctrl_layout = QHBoxLayout(control_frame)
        
        btn_style = """
            QPushButton {
                background-color: #2a2a2a;
                color: #999999;
                border: 1px solid #444444;
                padding: 10px 20px;
                font-size: 12px;
                font-family: 'Consolas';
                text-transform: uppercase;
            }
            QPushButton:hover {
                background-color: #333333;
                color: #cccccc;
                border-color: #666666;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
                border-color: #555555;
            }
        """
        
        self.reload_btn = QPushButton('Load Data')
        self.reload_btn.setStyleSheet(btn_style)
        self.reload_btn.clicked.connect(self.auto_load_data)
        ctrl_layout.addWidget(self.reload_btn)
        
        self.export_btn = QPushButton('Export Graph')
        self.export_btn.setStyleSheet(btn_style)
        self.export_btn.clicked.connect(self.save_plot)
        ctrl_layout.addWidget(self.export_btn)
        
        ctrl_layout.addStretch()
        
        lbl_style = "color: #888888; font-family: 'Consolas'; font-size: 11px;"
        
        wlbl = QLabel('WINDOW (n):')
        wlbl.setStyleSheet(lbl_style)
        ctrl_layout.addWidget(wlbl)
        
        spin_style = """
            QSpinBox {
                background-color: #252525;
                color: #cccccc;
                border: 1px solid #444444;
                padding: 6px;
                font-size: 12px;
                font-family: 'Consolas';
                min-width: 60px;
            }
            QSpinBox:focus {
                border-color: #888888;
            }
        """
        
        self.window_spin = QSpinBox()
        self.window_spin.setRange(1, 10)
        self.window_spin.setValue(3)
        self.window_spin.setStyleSheet(spin_style)
        ctrl_layout.addWidget(self.window_spin)
        
        flbl = QLabel('FORECAST (years):')
        flbl.setStyleSheet(lbl_style)
        ctrl_layout.addWidget(flbl)
        
        self.periods_spin = QSpinBox()
        self.periods_spin.setRange(1, 10)
        self.periods_spin.setValue(3)
        self.periods_spin.setStyleSheet(spin_style)
        ctrl_layout.addWidget(self.periods_spin)
        
        self.forecast_btn = QPushButton('Update Forecast')
        self.forecast_btn.setStyleSheet("""
            QPushButton {
                background-color: #252525;
                color: #888888;
                border: 1px solid #555555;
                padding: 10px 25px;
                font-size: 12px;
                font-family: 'Consolas';
                text-transform: uppercase;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                color: #aaaaaa;
                border-color: #777777;
            }
        """)
        self.forecast_btn.clicked.connect(self.plot_data)
        ctrl_layout.addWidget(self.forecast_btn)
        
        layout.addWidget(control_frame)
        
        # ===== TABLE =====
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: #b0b0b0;
                border: 1px solid #333333;
                gridline-color: #2a2a2a;
                font-family: 'Consolas';
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #333333;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #000000;
                color: #999999;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #444444;
                font-family: 'Consolas';
                font-size: 11px;
                text-transform: uppercase;
            }
        """)
        layout.addWidget(self.table, 2)
        
        # ===== STATS =====
        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setFont(QFont('Consolas', 11))
        self.stats_label.setMinimumHeight(50)
        self.stats_label.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                color: #999999;
                padding: 14px;
                border: 1px solid #333333;
                font-family: 'Consolas';
            }
        """)
        layout.addWidget(self.stats_label)
        
        # ===== GRAPH =====
        self.figure = Figure(figsize=(13, 5), facecolor='#1a1a1a')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas, 3)
    
    def auto_load_data(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'crime_data.xlsx')
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, 'File Not Found', 
                f'File not found!\n\n{file_path}')
            return
        
        try:
            df = pd.read_excel(file_path)
            
            self.data = []
            for _, row in df.iterrows():
                record = {}
                record['year'] = int(row['year'])
                record['murder'] = float(str(row['murders']).replace(',', '.'))
                record['robbery'] = float(str(row['robberies']).replace(',', '.'))
                record['theft'] = float(str(row['thefts']).replace(',', '.'))
                record['fraud'] = float(str(row['trickery']).replace(',', '.'))
                record['drugs'] = float(str(row['drugs']).replace(',', '.'))
                record['economic'] = float(str(row['economic']).replace(',', '.'))
                self.data.append(record)
            
            self.show_table()
            self.show_stats()
            self.plot_data()
            
        except Exception as e:
            print(f"Error: {e}")
    
    def show_table(self):
        self.table.setRowCount(len(self.data))
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['Year', 'Murder', 'Robbery', 'Theft', 'Fraud', 'Drugs', 'Economic'])
        
        for i, row in enumerate(self.data):
            items = [
                str(row['year']),
                f"{row['murder']:.1f}",
                f"{row['robbery']:.1f}",
                f"{row['theft']:.1f}",
                f"{row['fraud']:.1f}",
                f"{row['drugs']:.1f}",
                f"{row['economic']:.1f}"
            ]
            for j, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, j, item)
    
    def show_stats(self):
        if not self.data:
            return
        first = self.data[0]
        last = self.data[-1]
        
        changes = {}
        for field in ['murder', 'robbery', 'theft', 'fraud', 'drugs', 'economic']:
            if first[field] != 0:
                changes[field] = ((last[field] - first[field]) / first[field]) * 100
        
        most_decreased = min(changes, key=changes.get)
        most_increased = max(changes, key=changes.get)
        
        names = {
            'murder': 'MURDER', 'robbery': 'ROBBERY', 'theft': 'THEFT',
            'fraud': 'FRAUD', 'drugs': 'DRUGS', 'economic': 'ECONOMIC'
        }
        
        stats = (f"MAX DECREASE: {names[most_decreased]} = {changes[most_decreased]:.1f}%   |   "
                f"MAX INCREASE: {names[most_increased]} = +{changes[most_increased]:.1f}%")
        self.stats_label.setText(stats)
    
    def moving_average(self, data, window, periods):
        result = []
        working = data.copy()
        for _ in range(periods):
            avg = sum(working[-window:]) / window
            result.append(avg)
            working.append(avg)
        return result
    
    def plot_data(self):
        if not self.data:
            return
        
        window = self.window_spin.value()
        periods = self.periods_spin.value()
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#1a1a1a')
        
        years = [d['year'] for d in self.data]
        colors = ['#e74c3c', '#e67e22', '#3498db', '#2ecc71', '#9b59b6', '#1abc9c']
        fields = ['murder', 'robbery', 'theft', 'fraud', 'drugs', 'economic']
        labels = ['Murder', 'Robbery', 'Theft', 'Fraud', 'Drugs', 'Economic']
        
        for field, color, label in zip(fields, colors, labels):
            values = [d[field] for d in self.data]
            ax.plot(years, values, 'o-', color=color, label=label, markersize=5, linewidth=2)
            
            forecast = self.moving_average(values, window, periods)
            last_year = years[-1]
            forecast_years = list(range(last_year + 1, last_year + periods + 1))
            ax.plot([last_year] + forecast_years, [values[-1]] + forecast, 
                   '--', color=color, linewidth=2, alpha=0.4)
        
        ax.set_xlabel('YEAR', color='#888888', fontsize=10, fontfamily='monospace')
        ax.set_ylabel('CRIMES (thousands)', color='#888888', fontsize=10, fontfamily='monospace')
        ax.set_title(f'CRIME DYNAMICS & FORECAST (MOVING AVERAGE, n={window})', 
                    color='#aaaaaa', fontsize=12, fontfamily='monospace')
        ax.legend(loc='upper left', fontsize=8, facecolor='#1a1a1a', 
                 edgecolor='#444444', labelcolor='#cccccc')
        ax.grid(True, alpha=0.12, color='#444444')
        ax.tick_params(colors='#888888', labelsize=9)
        ax.spines['bottom'].set_color('#444444')
        ax.spines['left'].set_color('#444444')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def save_plot(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Save Graph', 'crime_graph.png', 
            'PNG (*.png);;PDF (*.pdf);;SVG (*.svg)'
        )
        if file_path:
            self.figure.savefig(file_path, dpi=150, bbox_inches='tight', 
                              facecolor='#1a1a1a')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())