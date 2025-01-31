from PyQt5.QtWidgets import QToolBar, QComboBox, QPushButton, QWidget, QHBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QSize
import logging

logger = logging.getLogger(__name__)

class Toolbar(QToolBar):
    """工具栏"""
    
    # 定义信号
    connect_clicked = pyqtSignal()  # 连接按钮点击信号
    port_changed = pyqtSignal(str)  # 串口改变信号
    run_clicked = pyqtSignal()      # 运行按钮点击信号
    stop_clicked = pyqtSignal()     # 停止按钮点击信号
    log_clicked = pyqtSignal()      # 日志按钮点击信号
    clear_log_clicked = pyqtSignal()# 清除日志按钮点击信号
    refresh_clicked = pyqtSignal()  # 刷新按钮点击信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setIconSize(QSize(32, 32))
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        
        # 创建串口标签
        port_label = QLabel("串口：")
        main_layout.addWidget(port_label)
        
        # 创建串口选择下拉框
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(100)
        self.port_combo.currentTextChanged.connect(self.port_changed)
        main_layout.addWidget(self.port_combo)
        
        # 创建刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setMinimumWidth(60)
        self.refresh_btn.clicked.connect(self.refresh_clicked)
        main_layout.addWidget(self.refresh_btn)
        
        # 创建波特率标签
        baud_label = QLabel("波特率：")
        main_layout.addWidget(baud_label)
        
        # 创建波特率选择下拉框
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '19200', '38400', '57600', '115200'])
        self.baud_combo.setCurrentText('9600')
        self.baud_combo.setMinimumWidth(100)
        main_layout.addWidget(self.baud_combo)
        
        # 创建连接按钮
        self.connect_btn = QPushButton("连接")
        self.connect_btn.setMinimumWidth(60)
        self.connect_btn.clicked.connect(self.connect_clicked)
        main_layout.addWidget(self.connect_btn)
        
        # 添加分隔
        main_layout.addSpacing(20)
        
        # 运行按钮
        self.run_btn = QPushButton("运行")
        self.run_btn.clicked.connect(self.run_clicked)
        self.run_btn.setMinimumWidth(60)
        main_layout.addWidget(self.run_btn)
        
        # 停止按钮
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_clicked)
        self.stop_btn.setMinimumWidth(60)
        main_layout.addWidget(self.stop_btn)
        
        # 添加分隔
        main_layout.addSpacing(20)
        
        # 日志按钮
        self.log_btn = QPushButton("显示日志")
        self.log_btn.clicked.connect(self.log_clicked)
        self.log_btn.setMinimumWidth(80)
        main_layout.addWidget(self.log_btn)
        
        # 清除日志按钮
        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.clicked.connect(self.clear_log_clicked)
        self.clear_log_btn.setMinimumWidth(80)
        main_layout.addWidget(self.clear_log_btn)
        
        # 添加弹性空间
        main_layout.addStretch()
        
        # 设置固定高度
        main_widget.setFixedHeight(50)
        self.addWidget(main_widget)
        
        # 设置工具栏样式
        self.setStyleSheet("""
            QToolBar {
                background-color: #f5f5f5;
                border-bottom: 1px solid #e0e0e0;
            }
            QLabel {
                color: #424242;
                font-size: 12pt;
            }
            QComboBox {
                background-color: white;
                color: #424242;
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                padding: 3px;
                min-width: 100px;
                font-size: 12pt;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 15px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #9e9e9e;
            }
        """)
        
    def update_ports(self, ports):
        """更新可用串口列表"""
        current = self.port_combo.currentText()
        self.port_combo.blockSignals(True)  # 暂时阻止信号发送
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        if current in ports:
            self.port_combo.setCurrentText(current)
        self.port_combo.blockSignals(False)  # 恢复信号发送
        
    def get_port(self):
        """获取当前选择的串口"""
        return self.port_combo.currentText()
        
    def get_baud_rate(self):
        """获取当前选择的波特率"""
        return int(self.baud_combo.currentText())
        
    def set_connected(self, connected):
        """设置连接状态"""
        self.connect_btn.setText("断开" if connected else "连接")
        
    def set_port(self, port):
        """设置串口"""
        if port in [self.port_combo.itemText(i) for i in range(self.port_combo.count())]:
            self.port_combo.setCurrentText(port)
            
    def set_baud_rate(self, baud_rate):
        """设置波特率"""
        self.baud_combo.setCurrentText(str(baud_rate))
