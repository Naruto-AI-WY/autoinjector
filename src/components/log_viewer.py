from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSizePolicy, QTextEdit, QApplication
from PyQt5.QtGui import QFont, QTextCharFormat, QColor, QTextCursor
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LogViewer(QTextEdit):
    """日志查看器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: none;
                font-family: Consolas, Monaco, monospace;
                font-size: 12pt;
            }
        """)
        self.setMinimumHeight(150)
        self.setMaximumHeight(300)

    @pyqtSlot(str, str)
    def append_log(self, msg, level="INFO"):
        """添加日志
        
        Args:
            msg: 日志消息
            level: 日志级别
        """
        color = {
            "ERROR": "#dc3545",    # 红色
            "WARNING": "#ffc107",  # 黄色
            "INFO": "#495057",     # 深灰
            "DEBUG": "#6c757d"     # 浅灰
        }.get(level, "#212529")    # 默认黑色
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] {msg}"
        
        # 添加日志
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        self.setTextCursor(cursor)
        self.insertHtml(f'<span style="color: {color};">{formatted_message}</span><br>')
        
        # 滚动到底部
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        
        # 立即刷新
        QApplication.processEvents()

    def clear(self):
        """清空日志"""
        super().clear()

class LogViewerEdit(QTextEdit):
    """日志查看器编辑器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)  # 设置为只读
        self.setMaximumHeight(200)  # 设置最大高度
        self.setMinimumHeight(100)  # 设置最小高度
        
        # 设置字体
        font = QFont("Consolas, 'Courier New', monospace")
        font.setPixelSize(24)  # 增加到24像素
        self.setFont(font)
        
        # 设置样式
        self.setStyleSheet("""
            QTextEdit {
                background-color: white;
                color: #424242;
                border: none;
                border-top: 1px solid #e0e0e0;
                padding: 5px;
            }
            QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #e0e0e0;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #bdbdbd;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background-color: #f5f5f5;
            }
        """)
        
    def append_log(self, message, level="INFO"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] {message}"
        
        # 根据日志级别设置颜色
        if level == "ERROR":
            color = "#f44336"  # 红色
        elif level == "WARNING":
            color = "#ff9800"  # 橙色
        elif level == "SUCCESS":
            color = "#4caf50"  # 绿色
        else:
            color = "#424242"  # 深灰色
            
        # 使用HTML格式添加带颜色的文本
        self.append(f'<span style="color: {color};">{formatted_message}</span>')
        
        # 滚动到底部
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        
        # 立即刷新显示
        QApplication.processEvents()

    def clear_log(self):
        """清空日志"""
        self.clear()
