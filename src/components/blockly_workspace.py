from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl, pyqtSignal
import os
import logging
import sys

logger = logging.getLogger(__name__)

STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../static'))

class BlocklyPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        logger.debug(f"JS[{lineNumber}]: {message}")

class BlocklyWorkspace(QWebEngineView):
    """Blockly工作区"""
    
    # 定义信号
    code_generated = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """初始化工作区"""
        super().__init__(parent)
        self.main_window = parent
        self.web_bridge = None
        self.code_editor = None
        self._page = None
        
        # 创建自定义页面
        self._page = BlocklyPage(self)
        self.setPage(self._page)
        
        # 设置页面
        self.setUrl(QUrl.fromLocalFile(os.path.join(STATIC_DIR, 'blockly.html')))
        
        # 等待页面加载完成
        self.loadFinished.connect(self._on_load_finished)

    def _on_load_finished(self, ok):
        """页面加载完成时的处理"""
        if ok:
            # 设置 Web Channel
            channel = QWebChannel(self)
            self._page.setWebChannel(channel)
            
            if self.web_bridge:
                channel.registerObject('webBridge', self.web_bridge)
        else:
            logger.error("Blockly页面加载失败")

    def set_web_bridge(self, bridge):
        """设置Web Bridge"""
        self.web_bridge = bridge
        
        # 如果页面已加载，立即注册bridge
        if self._page:
            channel = QWebChannel(self)
            self._page.setWebChannel(channel)
            channel.registerObject('webBridge', bridge)

    def get_generated_code(self):
        """获取生成的代码"""
        if self._page:
            self._page.runJavaScript('Blockly.Python.workspaceToCode(workspace);', self.handle_code_generated)
    
    def handle_code_generated(self, code):
        """处理生成的代码"""
        if code:
            # 移除多余的 blockId 注释
            code_lines = code.split('\n')
            clean_lines = [line for line in code_lines if not line.strip().startswith('# blockId:')]
            clean_code = '\n'.join(clean_lines)
            
            # 发送代码到代码编辑器
            if hasattr(self, 'code_editor'):
                self.code_editor.setPlainText(clean_code)
            
            # 发送信号
            self.code_generated.emit(clean_code)
        else:
            logger.warning("没有生成任何代码")
    
    def highlight_block(self, block_id):
        """高亮显示指定的块"""
        if self._page:
            self._page.runJavaScript(f'highlightBlock("{block_id}");')
    
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

    @property
    def page(self):
        """获取页面对象"""
        return self._page
