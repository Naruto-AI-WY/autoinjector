from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl, pyqtSignal
import os
import logging
import sys

logger = logging.getLogger(__name__)

class BlocklyPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        logger.debug(f"JS[{lineNumber}]: {message}")

class BlocklyWorkspace(QWebEngineView):
    """Blockly工作区"""
    
    # 定义信号
    code_generated = pyqtSignal(str)
    
    def __init__(self, main_window=None):
        """初始化工作区"""
        super().__init__()
        self.main_window = main_window
        self.web_bridge = None
        self.code_editor = None
        
        # 加载 Blockly 页面
        self.load_blockly_page()
        
    def load_blockly_page(self):
        """加载 Blockly 页面"""
        # 创建自定义页面
        self.page = BlocklyPage(self)
        self.setPage(self.page)
        
        # 创建 WebChannel
        self.channel = QWebChannel()
        
        # 创建并添加 WebBridge
        from main_window import WebBridge
        self.web_bridge = None  # 将在 MainWindow 中设置
        
        # 连接 WebBridge 信号
        # self.web_bridge.codeGenerated.connect(self.handle_code_generated)
        
        # 设置 WebChannel
        self.page.setWebChannel(self.channel)
        
        # 加载 Blockly 页面
        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../static/blockly.html'))
        self.setUrl(QUrl.fromLocalFile(html_path))
    
    def set_web_bridge(self, bridge):
        """设置 Web Bridge"""
        self.web_bridge = bridge
        self.channel.registerObject('webBridge', bridge)
        logger.debug("Web Bridge 已设置")
        self.web_bridge.codeGenerated.connect(self.handle_code_generated)
    
    def handle_code_generated(self, code):
        """处理生成的代码"""
        if code:
            logger.info(f"Blockly生成的原始代码:\n{code}")
            # 移除多余的 blockId 注释
            code_lines = code.split('\n')
            clean_lines = [line for line in code_lines if not line.strip().startswith('# blockId:')]
            clean_code = '\n'.join(clean_lines)
            logger.info(f"清理后的代码:\n{clean_code}")
            
            # 发送代码到代码编辑器
            if hasattr(self, 'code_editor'):
                self.code_editor.setPlainText(clean_code)
            
            # 发送信号
            self.code_generated.emit(clean_code)
        else:
            logger.warning("没有生成任何代码")
    
    def get_generated_code(self):
        """获取生成的代码"""
        self.page.runJavaScript(
            'Blockly.Python.workspaceToCode(workspace);',
            self.handle_code_generated
        )
    
    def highlight_block(self, block_id):
        """高亮显示指定的块"""
        if hasattr(self, 'web_bridge'):
            self.web_bridge.highlightBlock.emit(block_id)
    
    def execute_code(self, code):
        """执行生成的代码
        
        Args:
            code: 要执行的代码字符串
        """
        try:
            logger.info("开始执行代码...")
            
            # 准备执行环境
            exec_globals = {
                'pump': self.main_window.pump,
                'serial_controller': self.main_window.serial_controller,
                'logger': logger
            }
            
            # 准备代码行列表
            code_lines = code.split('\n')
            
            # 创建行追踪器
            from line_tracer import LineTracer
            tracer = LineTracer(code_lines, self)
            
            # 设置追踪器
            sys.settrace(tracer.get_line_description)
            
            # 执行代码
            exec(code, exec_globals)
            
            logger.info("代码执行完成")
            
        except Exception as e:
            logger.error(f"代码执行失败: {e}")
            raise
            
        finally:
            # 清除追踪器
            sys.settrace(None)
