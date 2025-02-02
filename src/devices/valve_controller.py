import logging
import time
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class ValveController:
    """12通旋转阀控制器"""
    
    # 指令常量
    START_BYTE = 0x03
    ROTATE_CMD = 0x66  # 阀位控制
    QUERY_POS_CMD = 0x33  # 查询当前孔位
    QUERY_LAST_POS_CMD = 0x44  # 查询断电前孔位
    STATUS_CMD = 0x55  # 查询状态
    
    # 状态码
    STATUS_SUCCESS = 0x00
    STATUS_INVALID_CMD = 0x01
    STATUS_BUSY = 0x02
    STATUS_INVALID_PARAM = 0x03
    STATUS_TIMEOUT = 0x04
    STATUS_UNKNOWN = 0x05
    
    STATUS_MESSAGES = {
        STATUS_SUCCESS: "无错误，执行成功",
        STATUS_INVALID_CMD: "无效指令",
        STATUS_BUSY: "设备忙碌",
        STATUS_INVALID_PARAM: "参数错误",
        STATUS_TIMEOUT: "超时错误",
        STATUS_UNKNOWN: "未知错误"
    }
    
    def __init__(self, serial_controller):
        """初始化旋转阀控制器
        
        Args:
            serial_controller: 串口控制器实例
        """
        self.serial_controller = serial_controller
        self.device_address = None
    
    def initialize(self, device_address: int) -> bool:
        """初始化旋转阀
        
        Args:
            device_address: 设备地址
            
        Returns:
            bool: 是否初始化成功
        """
        try:
            self.device_address = device_address
            # 检查设备状态
            status = self.check_status()
            if status == self.STATUS_SUCCESS:
                logger.info(f"旋转阀 (地址: {device_address}) 初始化成功")
                return True
            else:
                logger.error(f"旋转阀 (地址: {device_address}) 初始化失败: {self.STATUS_MESSAGES.get(status, '未知状态')}")
                return False
        except Exception as e:
            logger.error(f"旋转阀初始化出错: {str(e)}")
            return False
    
    def _calculate_checksum(self, data: list) -> int:
        """计算校验和 (XOR)
        
        Args:
            data: 要计算校验和的数据列表
            
        Returns:
            int: 校验和
        """
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum
    
    def _send_command(self, command: list, expected_length: int = 8, retry_count: int = 3, retry_timeout: float = 1.0, read_timeout: float = 2.0) -> Optional[bytes]:
        """发送命令并接收响应
        
        Args:
            command: 命令字节列表
            expected_length: 期望的响应长度
            retry_count: 最大重试次数
            retry_timeout: 每次重试之间的等待时间（秒）
            read_timeout: 每次读取的超时时间（秒）
            
        Returns:
            Optional[bytes]: 响应数据，如果出错则返回 None
        """
        try:
            # 计算并添加校验和
            checksum = self._calculate_checksum(command)
            command.append(checksum)
            
            # 记录发送的指令
            cmd_bytes = bytes(command)
            cmd_str = ' '.join([f'0x{b:02X}' for b in cmd_bytes])
            
            # 如果是旋转命令，添加孔位说明
            if len(command) > 2 and command[1] == self.ROTATE_CMD:
                target_pos = command[6]  # 0-based position
                logger.info(f"发送指令: {cmd_str} (旋转到孔位 {target_pos + 1}，协议中使用从0开始的编号 0x{target_pos:02X})")
            else:
                logger.info(f"发送指令: {cmd_str}")
            
            # 发送命令，最多重试指定次数
            for attempt in range(retry_count):
                try:
                    if not self.serial_controller.write(cmd_bytes):
                        logger.warning(f"发送命令失败，尝试重试... ({attempt + 1}/{retry_count})")
                        time.sleep(retry_timeout)  # 等待指定时间后重试
                        continue
                        
                    # 读取响应，使用带重试的读取方法
                    response = self.serial_controller.read_with_retry(
                        size=expected_length,
                        retries=retry_count,
                        timeout=read_timeout
                    )
                    
                    # 记录接收到的数据
                    if response:
                        resp_str = ' '.join([f'0x{b:02X}' for b in response])
                        if len(response) > 2 and response[1] == self.ROTATE_CMD:
                            current_pos = response[6]  # 0-based position
                            logger.info(f"接收数据: {resp_str} (当前孔位 {current_pos + 1}，协议中使用从0开始的编号 0x{current_pos:02X})")
                        else:
                            logger.info(f"接收数据: {resp_str}")
                            
                        if len(response) != expected_length:
                            logger.warning(f"响应长度错误: 期望 {expected_length} 字节，实际收到 {len(response)} 字节，尝试重试... ({attempt + 1}/{retry_count})")
                            time.sleep(retry_timeout)  # 等待指定时间后重试
                            continue
                            
                        return response
                    else:
                        logger.warning(f"未接收到数据，尝试重试... ({attempt + 1}/{retry_count})")
                        time.sleep(retry_timeout)  # 等待指定时间后重试
                        continue
                        
                except Exception as e:
                    logger.warning(f"通信出错: {str(e)}，尝试重试... ({attempt + 1}/{retry_count})")
                    time.sleep(retry_timeout)  # 等待指定时间后重试
                    continue
                    
            logger.error("发送命令失败: 重试次数已用完")
            return None
            
        except Exception as e:
            logger.error(f"发送命令出错: {str(e)}")
            return None
    
    def check_status(self) -> int:
        """检查设备状态
        
        Returns:
            int: 状态码
        """
        if self.device_address is None:
            logger.error("设备未初始化")
            return self.STATUS_UNKNOWN
            
        command = [self.START_BYTE, self.STATUS_CMD, self.device_address, 0x00, 0x00, 0x00, 0x00]
        response = self._send_command(command)
        
        if response is None:
            return self.STATUS_UNKNOWN
            
        return response[6]
    
    def rotate_to_position(self, position: int) -> bool:
        """旋转到指定孔位
        
        Args:
            position: 目标孔位 (1-12)
            
        Returns:
            bool: 是否成功
        """
        if not 1 <= position <= 12:
            logger.error(f"无效的孔位: {position}，孔位必须在 1-12 之间")
            return False
            
        if self.device_address is None:
            logger.error("设备未初始化")
            return False
            
        # 转换为0基孔位
        zero_based_pos = position - 1
        
        # 构建命令
        command = [self.START_BYTE, self.ROTATE_CMD, self.device_address, 0x00, 0x00, 0x00, zero_based_pos]
        response = self._send_command(command)
        
        if response is None:
            return False
            
        # 检查响应
        if response[6] != zero_based_pos:
            logger.error(f"旋转失败: 目标孔位 {position}，实际孔位 {response[6] + 1}")
            return False
            
        # 检查执行状态
        status = self.check_status()
        if status != self.STATUS_SUCCESS:
            logger.error(f"旋转失败: {self.STATUS_MESSAGES.get(status, '未知状态')}")
            return False
            
        logger.info(f"成功旋转到孔位 {position}")
        return True
    
    def get_current_position(self) -> Optional[int]:
        """获取当前孔位
        
        Returns:
            Optional[int]: 当前孔位 (1-12)，如果出错则返回 None
        """
        if self.device_address is None:
            logger.error("设备未初始化")
            return None
            
        command = [self.START_BYTE, self.QUERY_POS_CMD, self.device_address, 0x01, 0x00, 0x00, 0x00]
        response = self._send_command(command)
        
        if response is None:
            return None
            
        # 检查执行状态
        status = self.check_status()
        if status != self.STATUS_SUCCESS:
            logger.error(f"获取当前孔位失败: {self.STATUS_MESSAGES.get(status, '未知状态')}")
            return None
            
        # 转换为1基孔位
        position = response[6] + 1
        logger.info(f"当前孔位: {position}")
        return position
    
    def get_last_position(self) -> Optional[int]:
        """获取断电前孔位
        
        Returns:
            Optional[int]: 断电前孔位 (1-12)，如果出错则返回 None
        """
        if self.device_address is None:
            logger.error("设备未初始化")
            return None
            
        command = [self.START_BYTE, self.QUERY_LAST_POS_CMD, self.device_address, 0x01, 0x00, 0x00, 0x00]
        response = self._send_command(command)
        
        if response is None:
            return None
            
        # 检查执行状态
        status = self.check_status()
        if status != self.STATUS_SUCCESS:
            logger.error(f"获取断电前孔位失败: {self.STATUS_MESSAGES.get(status, '未知状态')}")
            return None
            
        # 转换为1基孔位
        position = response[6] + 1
        logger.info(f"断电前孔位: {position}")
        return position
