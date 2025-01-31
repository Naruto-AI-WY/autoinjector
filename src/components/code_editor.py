from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtGui import QFont, QPainter, QTextFormat, QColor
from PyQt5.QtCore import Qt, QRect
import logging

logger = logging.getLogger(__name__)

class CodeEditor(QPlainTextEdit):
    """代码编辑器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 设置字体
        font = QFont("Consolas", 12)
        font.setFixedPitch(True)
        self.setFont(font)
        
        # 设置只读
        self.setReadOnly(True)
        
        # 设置样式
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #282c34;
                color: #abb2bf;
                selection-background-color: #3e4451;
                selection-color: #abb2bf;
                border: none;
            }
        """)
        
    def paintEvent(self, event):
        """重写绘制事件，添加行号区域"""
        # 调用父类的绘制方法
        super().paintEvent(event)
        
        # 绘制行号区域背景
        painter = QPainter(self.viewport())
        painter.fillRect(
            QRect(0, 0, self.line_number_area_width(), self.height()),
            QColor("#21252b")
        )
        
    def line_number_area_width(self):
        """计算行号区域宽度"""
        digits = len(str(self.blockCount()))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
        
    def resizeEvent(self, event):
        """重写大小改变事件"""
        super().resizeEvent(event)
        
        # 更新视口边距
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        
    def setPlainText(self, text):
        """重写设置文本方法"""
        super().setPlainText(text)
        
        # 设置滚动条到顶部
        self.verticalScrollBar().setValue(0)
        
        # 更新视口边距
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
