from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
import logging
from serial.tools import list_ports
import time

logger = logging.getLogger(__name__)

class SerialController(QObject):
    # 定义信号
    connected = pyqtSignal(bool)  # 连接状态改变信号
    error_occurred = pyqtSignal(str)  # 错误信号
    data_received = pyqtSignal(str)  # 数据接收信号
    data_sent = pyqtSignal(str)  # 数据发送信号
    ports_discovered = pyqtSignal(list)  # 发现串口时发出信号

    def __init__(self):
        super().__init__()
        self.serial = QSerialPort()
        self.serial.readyRead.connect(self._on_data_ready)
        self.serial.errorOccurred.connect(self._on_error)
        self._buffer = ""
        self._port = None  # 添加端口属性
        
        # 初始化时检查可用串口
        ports = self.get_available_ports()
        if ports:
            self.ports_discovered.emit(ports)
            
        # 添加定时器检查串口状态
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._check_port_status)
        self._check_timer.start(1000)  # 每秒检查一次
        
        logger.info("SerialController initialized")

    def _check_port_status(self):
        """检查串口状态"""
        if self.is_connected:
            # 检查串口是否仍然存在
            current_ports = self.get_available_ports()
            if self._port not in current_ports:
                logger.warning(f"串口 {self._port} 已断开")
                self.disconnect()
                self.error_occurred.emit(f"串口 {self._port} 已断开连接")

    @property
    def is_connected(self) -> bool:
        """返回是否已连接"""
        return self.serial.isOpen()

    @property
    def port(self):
        """获取当前端口名"""
        return self._port

    def connect(self, settings: dict) -> bool:
        """连接到串口
        
        Args:
            settings: 串口配置字典，包含以下字段：
                - port: 串口名称
                - baudrate: 波特率
                - databits: 数据位
                - parity: 校验位
                - stopbits: 停止位
                - flowcontrol: 流控制
        """
        try:
            # 检查端口是否存在
            available_ports = self.get_available_ports()
            if settings['port'] not in available_ports:
                raise ConnectionError(f"串口 {settings['port']} 不存在")
                
            # 如果已经连接，先断开
            if self.is_connected:
                self.disconnect()
                
            # 设置串口参数
            self.serial.setPortName(settings['port'])
            self.serial.setBaudRate(int(settings['baudrate']))
            
            # 设置数据位
            data_bits_map = {
                5: QSerialPort.Data5,
                6: QSerialPort.Data6,
                7: QSerialPort.Data7,
                8: QSerialPort.Data8
            }
            self.serial.setDataBits(data_bits_map.get(int(settings['databits']), QSerialPort.Data8))
            
            # 设置校验位
            parity_map = {
                'N': QSerialPort.NoParity,
                'E': QSerialPort.EvenParity,
                'O': QSerialPort.OddParity
            }
            self.serial.setParity(parity_map.get(settings['parity'], QSerialPort.NoParity))
            
            # 设置停止位
            stop_bits_map = {
                1: QSerialPort.OneStop,
                1.5: QSerialPort.OneAndHalfStop,
                2: QSerialPort.TwoStop
            }
            self.serial.setStopBits(stop_bits_map.get(float(settings['stopbits']), QSerialPort.OneStop))
            
            # 设置流控制
            flow_control_map = {
                'N': QSerialPort.NoFlowControl,
                'H': QSerialPort.HardwareControl,
                'S': QSerialPort.SoftwareControl
            }
            self.serial.setFlowControl(flow_control_map.get(settings['flowcontrol'], QSerialPort.NoFlowControl))
            
            # 打开串口
            if not self.serial.open(QSerialPort.ReadWrite):
                raise Exception(f"无法打开串口 {settings['port']}")
                
            # 保存端口名
            self._port = settings['port']
            
            # 发送连接状态信号
            self.connected.emit(True)
            logger.info(f"串口 {settings['port']} 已连接")
            return True
            
        except Exception as e:
            logger.error(f"串口连接失败: {str(e)}")
            self.error_occurred.emit(str(e))
            return False

    def disconnect(self):
        """断开连接"""
        if self.is_connected:
            logger.info("Disconnecting from serial port")
            self.serial.close()
            self._port = None  # 清除端口名
            self.connected.emit(False)

    def write(self, data: bytes):
        """写入数据"""
        if not self.is_connected:
            logger.error("Attempted to write while not connected")
            raise ConnectionError("串口未连接")

        logger.debug(f"Writing data: {data}")
        written = self.serial.write(data)
        if written == -1:
            error = self.serial.errorString()
            logger.error(f"Failed to write data: {error}")
            self.error_occurred.emit(f"写入数据失败：{error}")
            return False
        
        self.serial.flush()
        self.data_sent.emit(data.hex())  # 发送数据发送信号，使用十六进制显示
        return True

    def read(self, size: int) -> bytes:
        """读取指定字节数的数据
        
        Args:
            size: 要读取的字节数
            
        Returns:
            bytes: 读取的数据
            
        Raises:
            ConnectionError: 串口未连接时抛出
        """
        if not self.is_connected:
            logger.error("Attempted to read while not connected")
            raise ConnectionError("串口未连接")
            
        data = self.serial.readAll().data()
        if data:
            logger.debug(f"Read data: {data.hex()}")  # 使用十六进制显示
            return data
        return bytes()

    def read_with_retry(self, size: int, retries: int = 3, timeout: float = 2.0) -> bytes:
        """读取指定字节数的数据，带重试和超时机制
        
        Args:
            size: 要读取的字节数
            retries: 重试次数
            timeout: 每次重试的超时时间（秒）
        
        Returns:
            bytes: 读取的数据
        
        Raises:
            ConnectionError: 串口未连接时抛出
        """
        if not self.is_connected:
            logger.error("Attempted to read while not connected")
            raise ConnectionError("串口未连接")

        attempt = 0
        while attempt < retries:
            data = self.serial.readAll().data()
            if data:
                logger.debug(f"Read data: {data.hex()}")  # 使用十六进制显示
                return data
            else:
                logger.warning(f"No data received, retrying... ({attempt + 1}/{retries})")
                time.sleep(timeout)
                attempt += 1

        logger.error("Failed to receive data after multiple attempts")
        return bytes()

    def send_command(self, command):
        """发送命令并等待反馈
        
        Args:
            command: 要发送的命令
            
        Returns:
            bool: 命令是否成功执行
        """
        try:
            # 发送命令
            if not self.write(command.encode()):
                return False
                
            # 等待并读取反馈
            response = self.read_with_retry(size=1024, retries=3, timeout=1.0)
            if response:
                logger.info(f"<<< {response.hex()}")  # 使用十六进制显示接收到的数据
                self.data_received.emit(response.decode())  # 发送反馈信号
                return True
            else:
                logger.error("No response received from device")
                self.error_occurred.emit("未收到设备响应")
                return False
                
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            self.error_occurred.emit(f"发送命令失败：{str(e)}")
            return False

    def _on_data_ready(self):
        """数据就绪时调用"""
        try:
            data = self.serial.readAll().data().decode()
            self._buffer += data
            
            # 处理完整的行
            while '\n' in self._buffer:
                line, self._buffer = self._buffer.split('\n', 1)
                line = line.strip()
                if line:  # 忽略空行
                    logger.debug(f"Received line: {line}")
                    self.data_received.emit(line)
                    
        except Exception as e:
            logger.error(f"Error reading data: {e}")
            self.error_occurred.emit(f"读取数据失败：{str(e)}")

    def _on_error(self, error):
        """错误发生时调用"""
        self.error_occurred.emit(str(error))

    def get_available_ports(self):
        """获取可用串口列表"""
        ports = []
        for port in QSerialPortInfo.availablePorts():
            ports.append(port.portName())
        
        # 也获取 pyserial 检测到的串口
        serial_ports = [port.device for port in list_ports.comports()]
        
        # 合并两个列表并去重
        all_ports = list(set(ports + serial_ports))
        all_ports.sort()  # 排序以保持稳定的顺序
        
        return all_ports
