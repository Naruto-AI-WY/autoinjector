from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSplitter, QMessageBox, QApplication, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QMetaObject, Q_ARG, pyqtSignal, QObject, pyqtSlot
from PyQt5.QtSerialPort import QSerialPortInfo
from PyQt5.QtWebChannel import QWebChannel
import logging
import json
from serial.tools import list_ports
import sys

from components.blockly_workspace import BlocklyWorkspace
from components.code_editor import CodeEditor
from components.log_viewer import LogViewer
from components.toolbar import Toolbar
from devices.pump_controller import PumpController
from devices.serial_controller import SerialController
from devices.serial_settings import SerialSettings
from line_tracer import LineTracer

logger = logging.getLogger(__name__)

class WebBridge(QObject):
    """Web bridge for communication between QWebEngine and Python"""
    
    # 信号定义
    codeGenerated = pyqtSignal(str)
    highlightBlock = pyqtSignal(str)
    portsUpdated = pyqtSignal()  # 新增串口更新信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    @pyqtSlot(str)
    def log(self, message):
        """Log message from JavaScript"""
        logging.info(f"JS: {message}")
    
    @pyqtSlot(result=str)
    def getAvailablePorts(self):
        """获取可用的串口列表"""
        try:
            ports = self.serial_controller.get_available_ports()
            if not ports:
                ports = ['COM3']  # 如果没有可用端口，默认显示 COM3
            logger.info(f"发现可用串口: {', '.join(ports)}")
            return json.dumps({'ports': ports})
        except Exception as e:
            logger.error(f"获取串口列表失败: {e}")
            return json.dumps({'ports': ['COM3']})  # 发生错误时也返回 COM3


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置日志处理器
        class LogHandler(logging.Handler):
            """日志处理器"""
            
            def __init__(self, log_viewer):
                super().__init__()
                self.log_viewer = log_viewer
                # 设置格式化器
                self.setFormatter(
                    logging.Formatter('%(message)s')
                )
                
            def emit(self, record):
                """发送日志记录"""
                try:
                    msg = self.format(record)
                    # 直接在主线程中更新日志
                    self.log_viewer.append_log(msg, record.levelname)
                    # 立即刷新应用程序
                    QApplication.processEvents()
                except Exception as e:
                    print(f"Error in log handler: {e}", file=sys.stderr)
        
        # 创建日志查看器（需要最先创建以捕获所有日志）
        self.log_viewer = LogViewer()
        
        # 添加日志处理器
        handler = LogHandler(self.log_viewer)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)
        
        # 创建串口控制器（在 Blockly 之前创建）
        self.serial_controller = SerialController()
        self.serial_settings = SerialSettings()
        
        # 创建 Web Bridge
        self.web_bridge = WebBridge()
        
        # 创建其他界面元素
        self.toolbar = Toolbar()
        self.blockly = BlocklyWorkspace(self)
        self.blockly.set_web_bridge(self.web_bridge)  # 设置 Web Bridge
        self.code_editor = CodeEditor()
        
        # 设置代码编辑器
        self.blockly.code_editor = self.code_editor
        
        # 创建泵控制器（在串口控制器之后创建）
        self.pump = PumpController(self.serial_controller)
        
        # 初始化UI
        self.init_ui()
        
        # 连接工具栏信号
        self.toolbar.connect_clicked.connect(self.on_connect_clicked)
        self.toolbar.run_clicked.connect(self.on_run_clicked)
        self.toolbar.stop_clicked.connect(self.on_stop_clicked)
        self.toolbar.log_clicked.connect(self.toggle_log_viewer)
        self.toolbar.clear_log_clicked.connect(self.clear_log)
        self.toolbar.refresh_clicked.connect(self.update_ports)
        self.toolbar.port_changed.connect(self.on_port_changed)
        
        # 连接其他信号
        self.blockly.code_generated.connect(self.on_code_generated)
        self.serial_controller.data_received.connect(self.on_data_received)
        self.serial_controller.ports_discovered.connect(self.on_ports_discovered)
        
        # 加载串口设置
        self._load_serial_settings()
        
        # 初始化串口列表并发送更新信号
        self.update_ports()
        
    def init_ui(self):
        """初始化UI"""
        # 设置窗口标题
        self.setWindowTitle('自动注射泵控制系统')
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # 添加工具栏
        main_layout.addWidget(self.toolbar)
        
        # 创建水平分割器
        hsplitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(hsplitter)
        
        # 添加 Blockly 工作区
        hsplitter.addWidget(self.blockly)
        
        # 创建右侧垂直分割器
        vsplitter = QSplitter(Qt.Vertical)
        hsplitter.addWidget(vsplitter)
        
        # 添加代码编辑器
        vsplitter.addWidget(self.code_editor)
        
        # 添加日志查看器
        self.log_viewer.hide()  # 初始隐藏日志查看器
        vsplitter.addWidget(self.log_viewer)
        
        # 设置分割器的初始大小比例
        hsplitter.setStretchFactor(0, 7)  # Blockly 工作区占 70%
        hsplitter.setStretchFactor(1, 3)  # 右侧部分占 30%
        
        vsplitter.setStretchFactor(0, 7)  # 代码编辑器占 70%
        vsplitter.setStretchFactor(1, 3)  # 日志查看器占 30%
        
        # 最大化窗口
        self.showMaximized()
        
    def _load_serial_settings(self):
        """加载串口设置"""
        try:
            # 获取默认设置
            settings = self.serial_settings.get_default_settings()
            
            # 更新工具栏
            self.toolbar.set_port(settings['port'])
            self.toolbar.set_baud_rate(settings['baudrate'])
            
        except Exception as e:
            logger.error(f"加载串口设置失败: {e}")
            
    def on_code_generated(self, code):
        """代码生成完成事件"""
        try:
            # 执行生成的代码
            self.execute_code(code)
        except Exception as e:
            logger.error(f"代码执行出错: {str(e)}")
            
    def execute_code(self, code):
        """执行代码"""
        try:
            # 使用 BlocklyWorkspace 的 execute_code 方法
            self.blockly.execute_code(code)
        except Exception as e:
            logger.error(f"代码执行失败: {str(e)}")
            raise
            
    def toggle_log_viewer(self):
        """切换日志查看器显示状态"""
        if self.log_viewer.isVisible():
            self.log_viewer.hide()
            self.toolbar.log_btn.setText("显示日志")
        else:
            self.log_viewer.show()
            self.toolbar.log_btn.setText("隐藏日志")

    def update_ports(self):
        """更新可用串口列表"""
        try:
            # 获取可用串口列表
            ports = []
            for port in QSerialPortInfo.availablePorts():
                ports.append(port.portName())
            
            # 也获取 pyserial 检测到的串口
            serial_ports = [port.device for port in list_ports.comports()]
            
            # 合并两个列表并去重
            all_ports = list(set(ports + serial_ports))
            all_ports.sort()  # 排序以保持稳定的顺序
            
            # 更新工具栏的串口列表
            self.toolbar.update_ports(all_ports)
            
            # 记录日志
            logger.info(f"发现可用串口: {', '.join(all_ports)}")
            
            # 通知 WebBridge 更新串口列表
            if self.blockly and self.blockly.web_bridge:
                self.blockly.web_bridge.portsUpdated.emit()
                logger.debug("已发送串口更新信号")
            
        except Exception as e:
            logger.error(f"更新串口列表时出错: {e}")
            
    def on_port_changed(self, port):
        """串口改变事件"""
        if port:  # 只在有实际选择时记录
            logger.info(f"选择串口: {port}")
        
    def on_connect_clicked(self):
        """连接按钮点击事件"""
        try:
            if not self.serial_controller.is_connected:
                # 获取串口设置
                settings = self.serial_settings.get_settings()
                # 连接串口
                if self.serial_controller.connect(settings):
                    logger.info(f"已连接到串口 {settings['port']}")
                    self.toolbar.set_connected(True)
                else:
                    logger.error("串口连接失败")
                    self.toolbar.set_connected(False)
            else:
                self.serial_controller.disconnect()
                logger.info("已断开串口连接")
                self.toolbar.set_connected(False)
        except Exception as e:
            logger.error(f"串口操作失败: {str(e)}")
            self.show_error("串口操作失败", str(e))
            
    def show_error(self, message, error):
        """显示错误信息"""
        self.log_viewer.append_log(message, "ERROR")
        logger.error(f"{message}: {error}")
        
    def on_data_received(self, data):
        """处理接收到的数据"""
        self.log_viewer.append_log(data, "RECV")
        
    def on_data_sent(self, data):
        """处理发送的数据"""
        self.log_viewer.append_log(data, "SEND")
        
    def clear_log(self):
        """清空日志"""
        self.log_viewer.clear()
        logger.info("日志已清空")

    def on_run_clicked(self):
        """运行按钮点击事件"""
        try:
            # 获取生成的代码
            self.blockly.get_generated_code()
        except Exception as e:
            logger.error(f"代码执行出错: {str(e)}")
            
    def on_stop_clicked(self):
        """停止按钮点击事件"""
        try:
            logger.info("正在停止...")
            if hasattr(self, 'pump'):
                self.pump.stop()
            logger.info("已停止")
        except Exception as e:
            logger.error(f"停止时出错: {str(e)}")

    def on_ports_discovered(self, ports):
        """处理发现新串口的信号"""
        if ports:
            logging.info(f"发现可用串口: {', '.join(ports)}")
            # 发送串口更新信号
            if hasattr(self, 'web_bridge'):
                self.web_bridge.portsUpdated.emit()

class LineTracer:
    """行追踪器"""
    def __init__(self, lines, blockly_workspace):
        self.lines = lines
        self.blockly_workspace = blockly_workspace
        
    def get_line_description(self, line_number):
        """获取行描述"""
        try:
            if line_number < len(self.lines):
                line = self.lines[line_number]
                block_id = self.blockly_workspace.get_block_id(line_number)
                if block_id:
                    return f"执行操作：{block_id}"
                else:
                    logger.debug("No block ID found for this line")
                    return "执行代码"
            return ""
        except Exception as e:
            logger.error(f"获取行描述失败: {e}")
            return ""
