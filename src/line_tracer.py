import logging

logger = logging.getLogger(__name__)

class LineTracer:
    """代码行追踪器"""
    
    def __init__(self, lines, blockly_workspace):
        """初始化追踪器
        
        Args:
            lines: 代码行列表
            blockly_workspace: Blockly工作区实例
        """
        self.lines = lines
        self.blockly = blockly_workspace
        self.block_ids = {}  # 行号到块ID的映射
        self._parse_block_ids()
        
    def _parse_block_ids(self):
        """解析代码中的块ID注释"""
        for i, line in enumerate(self.lines):
            if '# block_id:' in line:
                block_id = line.split('# block_id:')[1].strip()
                self.block_ids[i] = block_id
                logger.debug(f"Found block ID {block_id} at line {i}")
                
    def on_line(self, line_no):
        """处理代码行执行
        
        Args:
            line_no: 当前执行的行号
            
        Returns:
            str: 块的描述信息，如果没有对应的块则返回None
        """
        try:
            if 0 <= line_no < len(self.lines):
                block_id = self.block_ids.get(line_no)
                if block_id:
                    logger.debug(f"Highlighting block {block_id}")
                    desc = self.blockly.highlight_block(block_id)
                    if desc:
                        return desc
                    return f"执行操作：{block_id}"
            return None
        except Exception as e:
            logger.error(f"Error in line tracer: {e}")
            return None

    def get_line_description(self, frame, event, arg):
        """获取代码行的描述信息（用于 sys.settrace）
        
        Args:
            frame: 当前帧
            event: 事件类型
            arg: 事件参数
            
        Returns:
            self: 继续追踪
        """
        if event == 'line':
            try:
                # 获取当前行号（转换为0基索引）
                line_no = frame.f_lineno - 1
                
                # 获取当前行的内容
                if 0 <= line_no < len(self.lines):
                    line = self.lines[line_no].strip()
                    logger.debug(f"Executing line {line_no + 1}: {line}")
                    
                    # 高亮对应的块
                    if line_no in self.block_ids:
                        block_id = self.block_ids[line_no]
                        self.blockly.highlight_block(block_id)
                        
            except Exception as e:
                logger.error(f"Error in line tracer: {e}")
                
        return self.get_line_description  # 返回自身以继续追踪
