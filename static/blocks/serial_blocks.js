// 串口相关的 Blockly 块定义

if (typeof Blockly === 'undefined') {
    throw Error('Blockly is not loaded');
}

// 定义串口控制块
Blockly.Blocks['serial_port_select'] = {
    init: function() {
        // 初始化为默认选项
        this.jsonInit({
            "message0": "串口选择 %1",
            "args0": [
                {
                    "type": "field_dropdown",
                    "name": "PORT",
                    "options": [["COM3", "COM3"]]  // 修正显示值和实际值一致
                }
            ],
            "output": "String",
            "colour": 160,
            "tooltip": "选择串口"
        });
    },
    
    // 添加自定义更新方法
    updateOptions: function(ports) {
        var field = this.getField('PORT');
        if (field && ports && ports.length > 0) {
            // 将端口列表转换为下拉选项格式
            var options = ports.map(function(port) {
                return [port, port];
            });
            field.menuGenerator_ = options;
            
            // 设置默认值为第一个可用端口
            console.log("Setting new value to:", ports[0] || 'COM3');
            field.setValue(ports[0] || 'COM3');
            
            // 强制重新渲染
            field.forceRerender();
        }
    }
};

// 生成 Python 代码
Blockly.Python['serial_port_select'] = function(block) {
    var port = block.getFieldValue('PORT');
    console.log('Selected port:', port);
    // 确保端口值被引号包围
    return [`"${port}"`, Blockly.Python.ORDER_ATOMIC];
};

// 定义其他串口控制块
Blockly.defineBlocksWithJsonArray([
    {
        "type": "serial_config",
        "message0": "串口配置 端口 %1 波特率 %2 数据位 %3 校验位 %4 停止位 %5",
        "args0": [
            {
                "type": "input_value",
                "name": "PORT",
                "check": ["String", "text"],
                "align": "RIGHT"
            },
            {
                "type": "field_dropdown",
                "name": "BAUDRATE",
                "options": [
                    ["9600", "9600"],
                    ["19200", "19200"],
                    ["38400", "38400"],
                    ["57600", "57600"],
                    ["115200", "115200"]
                ]
            },
            {
                "type": "field_dropdown",
                "name": "DATABITS",
                "options": [
                    ["8位", "8"],
                    ["7位", "7"],
                    ["6位", "6"],
                    ["5位", "5"]
                ]
            },
            {
                "type": "field_dropdown",
                "name": "PARITY",
                "options": [
                    ["无校验", "N"],
                    ["奇校验", "O"],
                    ["偶校验", "E"]
                ]
            },
            {
                "type": "field_dropdown",
                "name": "STOPBITS",
                "options": [
                    ["1位", "1"],
                    ["1.5位", "1.5"],
                    ["2位", "2"]
                ]
            }
        ],
        "inputsInline": false,
        "output": "SerialConfig",
        "colour": 160,
        "tooltip": "配置串口参数",
        "helpUrl": ""
    },
    {
        "type": "text",
        "message0": "%1",
        "args0": [{
            "type": "field_input",
            "name": "TEXT",
            "text": ""
        }],
        "output": "String",
        "colour": 160,
        "tooltip": "文本",
        "helpUrl": ""
    },
    {
        "type": "device_address",
        "message0": "设备地址 %1",
        "args0": [
            {
                "type": "field_number",
                "name": "ADDRESS",
                "value": 1,
                "min": 1,
                "max": 99,
                "precision": 1
            }
        ],
        "output": "Number",
        "colour": 160,
        "tooltip": "设置设备地址（1-99）",
        "helpUrl": ""
    },
    {
        "type": "serial_close",
        "message0": "关闭串口",
        "previousStatement": null,
        "nextStatement": null,
        "colour": 160,
        "tooltip": "关闭串口连接"
    },
    {
        "type": "serial_save_settings",
        "message0": "保存串口设置 %1",
        "args0": [
            {
                "type": "input_value",
                "name": "SERIAL",
                "check": "Serial"
            }
        ],
        "previousStatement": null,
        "nextStatement": null,
        "colour": 230,
        "tooltip": "保存当前串口设置"
    }
]);

// 生成串口配置的 Python 代码
Blockly.Python['serial_config'] = function(block) {
    // 获取端口输入，如果没有连接则使用 COM3
    var port = Blockly.Python.valueToCode(block, 'PORT', Blockly.Python.ORDER_ATOMIC);
    if (!port || port === 'None') {
        console.warn('No port connected to serial_config block');
        port = '"COM3"';  
    }
    console.log('Port value:', port);
    
    var baudrate = block.getFieldValue('BAUDRATE');
    var databits = block.getFieldValue('DATABITS');
    var parity = block.getFieldValue('PARITY');
    var stopbits = block.getFieldValue('STOPBITS');
    
    // 生成配置字典
    var code = `{
    'port': ${port},
    'baudrate': ${baudrate},
    'databits': ${databits},
    'parity': '${parity}',
    'stopbits': ${stopbits},
    'flowcontrol': 'N'
}`;
    
    console.log('Generated config:', code);
    return [code, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['text'] = function(block) {
    var text = block.getFieldValue('TEXT');
    return ['"' + text + '"', Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['device_address'] = function(block) {
    var address = block.getFieldValue('ADDRESS');
    return [address.toString(), Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['serial_close'] = function(block) {
    return `# 关闭串口
if serial_controller.is_connected:
    logger.info("正在关闭串口...")
    serial_controller.disconnect()
`;
};

Blockly.Python['serial_save_settings'] = function(block) {
    var serial = Blockly.Python.valueToCode(block, 'SERIAL', Blockly.Python.ORDER_ATOMIC) || 'None';
    return 'serial_settings.save()\n';
};
