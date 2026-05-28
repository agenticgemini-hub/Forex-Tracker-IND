import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, QPoint, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import pyqtgraph as pg
import datetime

import data_manager
import scraper

class FetchDataThread(QThread):
    finished = pyqtSignal(object, object)

    def run(self):
        hdfc_rate = scraper.get_hdfc_bank_usd_buy()
        axis_rate = scraper.get_axis_bank_usd_buy()
        self.finished.emit(hdfc_rate, axis_rate)

class FloatingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._dragging = False
        self.initUI()
        self._install_drag_filter(self.container)
        self.refresh_data()

        # Timer to auto-refresh data if app is left open
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        # Refresh every 12 hours just in case
        self.timer.start(12 * 60 * 60 * 1000)

        self.oldPos = self.pos()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(300, 250)

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)

        # Container widget for styling
        self.container = QWidget()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QWidget#container {
                background-color: rgba(30, 30, 30, 220);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 50);
            }
            QLabel {
                color: white;
            }
        """)
        container_layout = QVBoxLayout(self.container)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("💵 USD Buy Rate")
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
        
        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(25, 25)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #F44336;
                font-weight: bold;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                color: #E57373;
            }
            QPushButton:pressed {
                color: #D32F2F;
            }
        """)
        self.close_btn.clicked.connect(self.close)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        header_layout.addWidget(self.close_btn)
        container_layout.addLayout(header_layout)

        # Rates layout
        self.hdfc_label = QLabel("HDFC: Loading...")
        self.hdfc_label.setFont(QFont("Segoe UI", 10))
        self.axis_label = QLabel("Axis: Loading...")
        self.axis_label.setFont(QFont("Segoe UI", 10))
        
        container_layout.addWidget(self.hdfc_label)
        container_layout.addWidget(self.axis_label)

        # Graph
        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setBackground('transparent')
        self.graphWidget.getAxis('left').setPen('w')
        self.graphWidget.getAxis('left').setTextPen('w')
        self.graphWidget.getAxis('bottom').setPen('w')
        self.graphWidget.getAxis('bottom').setTextPen('w')
        self.graphWidget.setFixedHeight(150)
        self.graphWidget.addLegend(offset=(5, 5))
        
        # Hover indicator line and tooltip text item
        self.hover_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(color=(255, 255, 255, 80), width=1, style=Qt.PenStyle.DashLine))
        self.hover_line.setVisible(False)
        
        self.tooltip = pg.TextItem(html="", fill=QColor(30, 30, 30, 51), border=pg.mkPen(255, 255, 255, 50))
        self.tooltip.setVisible(False)

        self.graphWidget.scene().sigMouseMoved.connect(self.on_mouse_moved)
        
        container_layout.addWidget(self.graphWidget)

        layout.addWidget(self.container)
        self.setLayout(layout)

    def refresh_data(self):
        self.refresh_btn.setEnabled(False)
        self.hdfc_label.setText("HDFC: Fetching...")
        self.axis_label.setText("Axis: Fetching...")
        
        self.fetch_thread = FetchDataThread()
        self.fetch_thread.finished.connect(self.on_data_fetched)
        self.fetch_thread.start()

    def on_data_fetched(self, hdfc_rate, axis_rate):
        if hdfc_rate:
            data_manager.save_rate("HDFC", "USD", hdfc_rate)
            self.hdfc_label.setText(f"HDFC: ₹{hdfc_rate:.2f}")
        else:
            self.hdfc_label.setText("HDFC: Error")

        if axis_rate:
            data_manager.save_rate("Axis", "USD", axis_rate)
            self.axis_label.setText(f"Axis: ₹{axis_rate:.2f}")
        else:
            self.axis_label.setText("Axis: Error")

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
                    
                # Format tooltip HTML with vertical alignment
                html = f"<div style='padding: 5px; font-family: Segoe UI; font-size: 8pt; color: white; line-height: 1.3;'>"
                html += f"<div style='text-align: center; font-weight: bold; border-bottom: 1px solid rgba(255,255,255,50); padding-bottom: 2px; margin-bottom: 4px;'>{day_month}</div>"
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

    # Allow dragging from anywhere on the widget, including child widgets
    def _install_drag_filter(self, widget):
        """Recursively install event filter on all child widgets for drag support."""
        widget.installEventFilter(self)
        for child in widget.findChildren(QWidget):
            # Skip buttons so they remain clickable
            if not isinstance(child, QPushButton):
                child.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == event.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self.oldPos = event.globalPosition().toPoint()
            return True
        elif event.type() == event.Type.MouseMove and self._dragging:
            delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPosition().toPoint()
            return True
        elif event.type() == event.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            return True
        return super().eventFilter(obj, event)

if __name__ == '__main__':
    # Initialize DB before running
    data_manager.init_db()
    
    app = QApplication(sys.argv)
    ex = FloatingWidget()
    ex.show()
    sys.exit(app.exec())
