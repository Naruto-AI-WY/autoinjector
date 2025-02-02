from typing import Optional
from .serial_controller import SerialController
import logging

# 配置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PumpController:
    """注射泵控制器"""
    
    def __init__(self, serial_controller: SerialController, pump_address: str = '1'):
        """初始化注射泵控制器
        
        Args:
            serial_controller: 串口控制器
            pump_address: 泵地址，默认为'1'
        """
        self.serial = serial_controller
        self.pump_address = pump_address
        self.serial.data_received.connect(self.on_data_received)
        self.volume_range = 25.0  # 默认量程25ml
        self.total_steps = 6000   # 默认总步数6000步
        logger.info("注射泵控制器已初始化")
        
    def on_data_received(self, data):
        """处理接收到的串口数据"""
        # 数据已经在 MainWindow 中记录，这里只处理命令响应
        logger.info(f"<<< {data}")  
        pass

    def send_command(self, command):
        """发送命令到泵"""
        if not self.serial.is_connected:
            raise ConnectionError("串口未连接")
        # 添加泵地址和结束符
        full_command = f"/{self.pump_address}{command}R"
        logger.info(f">>> {full_command}")  
        return self.serial.send_command(full_command)

    def initialize(self) -> bool:
        """初始化注射泵"""
        logger.info("Initializing pump")
        return self.send_command("Z")

    def switch_to_input(self) -> bool:
        """切换到输入模式"""
        logger.info("Switching to input mode")
        return self.send_command("I")

    def switch_to_output(self) -> bool:
        """切换到输出模式"""
        logger.info("Switching to output mode")
        return self.send_command("O")

    def set_speed(self, speed: float) -> bool:
        """设置注射速度 (Hz)"""
        # 将速度转换为4位数字，不足补0
        speed_str = f"{int(speed):04d}"
        logger.info(f"Setting pump speed to {speed} Hz")
        return self.send_command(f"V{speed_str}")

    def _volume_to_steps(self, volume_ml: float) -> int:
        """将体积（ml）转换为步数"""
        if self.total_steps <= 0 or self.volume_range <= 0:
            raise ValueError("总步数和量程必须大于0")
        steps_per_ml = self.total_steps / self.volume_range
        return int(volume_ml * steps_per_ml)

    def _steps_to_volume(self, steps: int) -> float:
        """将步数转换为体积（ml）"""
        if self.total_steps <= 0 or self.volume_range <= 0:
            raise ValueError("总步数和量程必须大于0")
        return (steps * self.volume_range) / self.total_steps

    def set_volume_range(self, volume_ml: float) -> bool:
        """设置注射泵的量程（单位：ml）"""
        if volume_ml <= 0:
            logger.error("量程必须大于0")
            return False
        self.volume_range = volume_ml
        logger.info(f"Setting pump volume range to {volume_ml} ml")
        return True

    def set_total_steps(self, steps: int) -> bool:
        """设置注射泵的总步数"""
        if steps <= 0:
            logger.error("总步数必须大于0")
            return False
        self.total_steps = steps
        logger.info(f"Setting pump total steps to {steps}")
        return True

    def aspirate(self, volume_ml: float) -> bool:
        """吸液指定体积（单位：ml）"""
        try:
            steps = self._volume_to_steps(volume_ml)
            logger.info(f"Aspirating {volume_ml} ml (steps: {steps})")
            return self.send_command(f"A{steps}")
        except ValueError as e:
            logger.error(f"吸液失败：{str(e)}")
            return False

    def dispense(self, volume_ml: float) -> bool:
        """排液指定体积（单位：ml）"""
        try:
            steps = self._volume_to_steps(volume_ml)
            logger.info(f"Dispensing {volume_ml} ml (steps: {steps})")
            return self.send_command(f"P{steps}")
        except ValueError as e:
            logger.error(f"排液失败：{str(e)}")
            return False

    def stop(self) -> bool:
        """停止当前操作"""
        logger.info("Stopping pump")
        return self.send_command("T")  # 假设停止命令是 T

    def save_settings(self) -> bool:
        """保存设置"""
        # 这个命令在新的协议中可能不需要
        logger.info("Saving settings is not supported in current protocol")
        return False