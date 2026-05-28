import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, QPoint, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon, QPixmap
import pyqtgraph as pg
import datetime

import data_manager
import scraper

# Resolve absolute path for assets relative to script location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "usd_icon.png")

class FetchDataThread(QThread):
    finished = pyqtSignal(object, object)

    def run(self):
        hdfc_rate = scraper.get_hdfc_bank_usd_buy()
        axis_rate = scraper.get_axis_bank_usd_buy()
        self.finished.emit(hdfc_rate, axis_rate)

class FloatingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.refresh_data()

        # Timer to auto-refresh data if app is left open
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        # Refresh every 12 hours just in case
        self.timer.start(12 * 60 * 60 * 1000)

    def initUI(self):
        self.setWindowTitle("Forex Tracker")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.resize(340, 320)
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                color: white;
            }
            QLabel {
                color: white;
            }
        """)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Golden USD Coin Icon in Header
        self.icon_label = QLabel()
        pixmap = QPixmap(ICON_PATH).scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setFixedSize(22, 22)
        
        title = QLabel("USD Buy Rate")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                
        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.setFixedSize(25, 25)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4CAF50;
                font-weight: bold;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                color: #81C784;
            }
            QPushButton:pressed {
                color: #388E3C;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)
        
        header_layout.addWidget(self.icon_label)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        layout.addLayout(header_layout)

        # Graph (increased height from 150 to 190 to take advantage of the freed vertical space)
        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setBackground('transparent')
        self.graphWidget.getAxis('left').setPen('w')
        self.graphWidget.getAxis('left').setTextPen('w')
        self.graphWidget.getAxis('bottom').setPen('w')
        self.graphWidget.getAxis('bottom').setTextPen('w')
        self.graphWidget.setMinimumHeight(180)
        self.graphWidget.showGrid(x=True, y=True, alpha=0.15)  # Enable subtle gridlines
        self.graphWidget.addLegend(offset=(5, 5))
        
        # Hover indicator line and tooltip text item
        self.hover_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(color=(255, 255, 255, 80), width=1, style=Qt.PenStyle.DashLine))
        self.hover_line.setVisible(False)
        
        self.tooltip = pg.TextItem(html="")
        self.tooltip.setVisible(False)

        self.graphWidget.scene().sigMouseMoved.connect(self.on_mouse_moved)
        
        layout.addWidget(self.graphWidget)

        # Footer Layout with 3 Sections
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 10, 0, 0)
        
        self.footer_coded_by = QLabel("Coded by Kaustav Das")
        self.footer_coded_by.setFont(QFont("Segoe UI", 8, QFont.Weight.Medium))
        self.footer_coded_by.setStyleSheet("color: #888888;")
        self.footer_coded_by.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.footer_hdfc = QLabel("HDFC: Loading...")
        self.footer_hdfc.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.footer_hdfc.setStyleSheet("color: #90CAF9;")
        self.footer_hdfc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.footer_axis = QLabel("Axis: Loading...")
        self.footer_axis.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.footer_axis.setStyleSheet("color: #F48FB1;")
        self.footer_axis.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        footer_layout.addWidget(self.footer_coded_by, 2)
        footer_layout.addWidget(self.footer_hdfc, 1)
        footer_layout.addWidget(self.footer_axis, 1)
        
        layout.addLayout(footer_layout)

    def refresh_data(self):
        self.refresh_btn.setEnabled(False)
        self.footer_hdfc.setText("HDFC: Fetching...")
        self.footer_axis.setText("Axis: Fetching...")
        
        self.fetch_thread = FetchDataThread()
        self.fetch_thread.finished.connect(self.on_data_fetched)
        self.fetch_thread.start()

    def on_data_fetched(self, hdfc_rate, axis_rate):
        if hdfc_rate:
            data_manager.save_rate("HDFC", "USD", hdfc_rate)
            self.footer_hdfc.setText(f"HDFC: ₹{hdfc_rate:.2f}")
        else:
            self.footer_hdfc.setText("HDFC: Error")

        if axis_rate:
            data_manager.save_rate("Axis", "USD", axis_rate)
            self.footer_axis.setText(f"Axis: ₹{axis_rate:.2f}")
        else:
            self.footer_axis.setText("Axis: Error")

        self.update_graph()
        self.refresh_btn.setEnabled(True)

    def update_graph(self):
        self.graphWidget.clear()
        
        hdfc_dates, hdfc_rates = data_manager.get_trend("HDFC", "USD")
        axis_dates, axis_rates = data_manager.get_trend("Axis", "USD")

        # 1. Align the data points by their actual calendar dates
        # Get the sorted union of all unique dates present in both series
        all_dates = sorted(list(set(hdfc_dates + axis_dates)))
        date_to_idx = {date: idx for idx, date in enumerate(all_dates)}

        # Store data maps for the mouse hover lookup
        self.all_dates_list = all_dates
        self.hdfc_data_map = dict(zip(hdfc_dates, hdfc_rates))
        self.axis_data_map = dict(zip(axis_dates, axis_rates))

        # Re-add hover items to the cleared PlotWidget
        self.graphWidget.addItem(self.hover_line)
        self.graphWidget.addItem(self.tooltip)
        self.hover_line.setVisible(False)
        self.tooltip.setVisible(False)

        # Map each rate to its corresponding date index on the X-axis
        hdfc_x = [date_to_idx[d] for d in hdfc_dates]
        axis_x = [date_to_idx[d] for d in axis_dates]

        # 2. Revert bottom axis ticks (hide them for minimalism)
        self.graphWidget.getAxis('bottom').setTicks([])

        # 3. Plot aligned data points
        if hdfc_rates:
            self.graphWidget.plot(hdfc_x, hdfc_rates, pen=pg.mkPen(color=(0, 114, 198), width=2), symbol='o', symbolSize=5, symbolBrush=(0, 114, 198), name="HDFC") # Blueish
        if axis_rates:
            self.graphWidget.plot(axis_x, axis_rates, pen=pg.mkPen(color=(174, 39, 95), width=2), symbol='o', symbolSize=5, symbolBrush=(174, 39, 95), name="Axis") # Burgundy/Pinkish

    def on_mouse_moved(self, pos):
        # Prevent crash if data hasn't loaded
        if not hasattr(self, 'all_dates_list') or not self.all_dates_list:
            return

        # Map scene coordinates to view coordinates
        mouse_point = self.graphWidget.plotItem.vb.mapSceneToView(pos)
        x_val = mouse_point.x()
        
        # Find the nearest integer index
        nearest_idx = round(x_val)
        
        # If nearest index is within bounds of all_dates
        if 0 <= nearest_idx < len(self.all_dates_list):
            date_str = self.all_dates_list[nearest_idx]
            
            # Fetch HDFC and Axis rates for this index/date
            hdfc_rate = self.hdfc_data_map.get(date_str)
            axis_rate = self.axis_data_map.get(date_str)
                
            # If we found at least one rate, show the tooltip and line
            if hdfc_rate is not None or axis_rate is not None:
                try:
                    dt = datetime.date.fromisoformat(date_str)
                    day_month = dt.strftime("%d %b")
                except Exception:
                    day_month = date_str
                    
                # Format tooltip HTML with vertical alignment and solid HTML background styling
                html = f"<div style='background-color: #282828; border: 1px solid rgba(255,255,255,100); border-radius: 4px; padding: 6px; font-family: Segoe UI; font-size: 8pt; color: white; line-height: 1.05; text-align: center;'>"
                html += f"<b>{day_month}</b><br>"
                if hdfc_rate is not None:
                    html += f"<span style='color: #90CAF9;'>HDFC: ₹{hdfc_rate:.2f}</span><br>"
                else:
                    html += f"<span style='color: #757575;'>HDFC: N/A</span><br>"
                if axis_rate is not None:
                    html += f"<span style='color: #F48FB1;'>Axis: ₹{axis_rate:.2f}</span>"
                else:
                    html += f"<span style='color: #757575;'>Axis: N/A</span>"
                html += "</div>"
                
                self.tooltip.setHtml(html)
                
                # Position the tooltip
                y_values = [v for v in [hdfc_rate, axis_rate] if v is not None]
                y_pos = sum(y_values) / len(y_values) if y_values else 94.0
                
                # Dynamic anchor selection: if the rate is near a peak, display the tooltip below the point to prevent clipping
                all_loaded_rates = [r for r in list(self.hdfc_data_map.values()) + list(self.axis_data_map.values()) if r is not None]
                if all_loaded_rates:
                    y_min = min(all_loaded_rates)
                    y_max = max(all_loaded_rates)
                    # If y_pos is in the top 35% of the range, display below the point
                    threshold = y_min + 0.65 * (y_max - y_min) if y_max != y_min else y_min
                else:
                    threshold = 94.0
                
                if y_pos > threshold:
                    self.tooltip.setAnchor((0.5, -0.2))  # Display below the point
                else:
                    self.tooltip.setAnchor((0.5, 1.2))   # Display above the point
                
                self.tooltip.setPos(nearest_idx, y_pos)
                self.hover_line.setPos(nearest_idx)
                
                self.tooltip.setVisible(True)
                self.hover_line.setVisible(True)
                return
                
        # Hide if out of bounds
        self.tooltip.setVisible(False)
        self.hover_line.setVisible(False)

if __name__ == '__main__':
    # Initialize DB before running
    data_manager.init_db()
    
    app = QApplication(sys.argv)
    ex = FloatingWidget()
    ex.show()
    sys.exit(app.exec())
