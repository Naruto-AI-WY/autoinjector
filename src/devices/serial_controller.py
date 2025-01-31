from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
import logging
from serial.tools import list_ports

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
        
        logger.info("SerialController initialized")

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
        self.data_sent.emit(data.decode())  # 发送数据发送信号
        return True

    def send_command(self, command):
        """发送命令"""
        try:
            return self.write(command.encode())
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
