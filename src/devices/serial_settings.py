import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SerialSettings:
    """串口设置管理器"""
    
    @staticmethod
    def get_default_settings():
        """获取默认串口设置"""
        return {
            'port': 'COM3',  # 默认使用 COM3
            'baudrate': 9600,
            'databits': 8,
            'parity': 'N',
            'stopbits': 1,
            'flowcontrol': 'N',
            'device_address': '1'
        }
        
    def __init__(self):
        self.settings_file = Path("settings/serial_settings.json")
        self.default_settings = self.get_default_settings()
        self.current_settings = self.default_settings.copy()
        self._load_settings()
        
    def _load_settings(self):
        """加载设置"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    self.current_settings.update(json.load(f))
                logger.info("已加载串口设置")
        except Exception as e:
            logger.error(f"加载串口设置失败: {e}")
            
    def save_settings(self):
        """保存设置"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.current_settings, f, indent=4)
            logger.info("已保存串口设置")
            return True
        except Exception as e:
            logger.error(f"保存串口设置失败: {e}")
            return False
            
    def update_settings(self, **kwargs):
        """更新设置"""
        self.current_settings.update(kwargs)
        
    def get_settings(self):
        """获取当前设置"""
        return self.current_settings.copy()
        
    def reset_settings(self):
        """重置为默认设置"""
        self.current_settings = self.default_settings.copy()
        return self.save_settings()
