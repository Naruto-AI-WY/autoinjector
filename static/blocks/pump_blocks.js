// 在这里定义泵控制块的代码
// 这些代码会被注入到 Blockly 页面中执行

if (typeof Blockly === 'undefined') {
    throw Error('Blockly is not loaded');
}

// 使用已存在的 pythonGenerator，不重复声明
const generator = Blockly.Python;

// 定义泵控制块
Blockly.defineBlocksWithJsonArray([
    {
        "type": "pump_initialize",
        "message0": "初始化注射泵 串口设置 %1 设备地址 %2",
        "args0": [
            {
                "type": "input_value",
                "name": "SERIAL_CONFIG",
                "check": ["SerialConfig", "String"],
                "align": "RIGHT"
            },
            {
                "type": "input_value",
                "name": "DEVICE_ADDRESS",
                "check": ["Number", "device_address"],
                "align": "RIGHT"
            }
        ],
        "inputsInline": false,
        "previousStatement": null,
        "nextStatement": null,
        "colour": 230,
        "tooltip": "初始化注射泵，设置串口和设备地址",
        "helpUrl": ""
    },
    {
        "type": "pump_set_volume_range",
        "message0": "设置注射量范围 %1",
        "args0": [
            {
                "type": "input_value",
                "name": "VOLUME",
                "check": "Number"
            }
        ],
        "previousStatement": null,
        "nextStatement": null,
        "colour": 230,
        "tooltip": "设置注射泵的注射量范围"
    },
    {
        "type": "pump_set_total_steps",
        "message0": "设置总步数 %1",
        "args0": [
            {
                "type": "input_value",
                "name": "STEPS",
                "check": "Number"
            }
        ],
        "previousStatement": null,
        "nextStatement": null,
        "colour": 230,
        "tooltip": "设置注射泵的总步数"
    },
    {
        "type": "pump_switch_input",
        "message0": "切换到输入模式",
        "previousStatement": null,
        "nextStatement": null,
        "colour": 230,
        "tooltip": "切换注射泵到输入模式"
    },
    {
        "type": "pump_switch_output",
        "message0": "切换到输出模式",
        "previousStatement": null,
        "nextStatement": null,
        "colour": 230,
        "tooltip": "切换注射泵到输出模式"
    },
    {
        "type": "pump_set_speed",
        "message0": "设置速度 %1",
        "args0": [
            {
                "type": "input_value",
                "name": "SPEED",
                "check": "Number"
            }
        ],
        "previousStatement": null,
        "nextStatement": null,
        "colour": 230,
        "tooltip": "设置注射泵的运行速度"
    },
    {
        "type": "pump_aspirate",
        "message0": "抽取 %1 ml",
        "args0": [
            {
                "type": "input_value",
                "name": "VOLUME",
                "check": "Number"
            }
        ],
        "previousStatement": null,
        "nextStatement": null,
        "colour": 230,
        "tooltip": "抽取指定体积的液体"
    },
    {
        "type": "pump_dispense",
        "message0": "注射 %1 ml",
        "args0": [
            {
                "type": "input_value",
                "name": "VOLUME",
                "check": "Number"
            }
        ],
        "previousStatement": null,
        "nextStatement": null,
        "colour": 230,
        "tooltip": "注射指定体积的液体"
    },
    {
        "type": "pump_stop",
        "message0": "停止",
        "previousStatement": null,
        "nextStatement": null,
        "colour": 230,
        "tooltip": "停止注射泵"
    },
    {
        "type": "pump_delay",
        "message0": "延时 %1 秒",
        "args0": [
            {
                "type": "input_value",
                "name": "SECONDS",
                "check": "Number"
            }
        ],
        "previousStatement": null,
        "nextStatement": null,
        "colour": 210,
        "tooltip": "等待指定的秒数"
    }
]);

// 生成 Python 代码
Blockly.Python['pump_initialize'] = function(block) {
    var serial_config = Blockly.Python.valueToCode(block, 'SERIAL_CONFIG', Blockly.Python.ORDER_ATOMIC) || '{}';
    var device_address = Blockly.Python.valueToCode(block, 'DEVICE_ADDRESS', Blockly.Python.ORDER_ATOMIC) || '1';
    
    var code = `# 连接串口
if not serial_controller.is_connected:
    logger.info("正在连接串口...")
    try:
        serial_controller.connect(${serial_config})
    except Exception as e:
        logger.error(f"串口连接失败: {e}")
        raise

# 初始化注射泵
if serial_controller.is_connected:
    logger.info("正在初始化注射泵...")
    pump.pump_address = str(${device_address})
    pump.initialize()
else:
    logger.error("串口未连接，无法初始化注射泵")
    raise ConnectionError("串口未连接，无法初始化注射泵")
`;
    return code;
};

Blockly.Python['pump_set_volume_range'] = function(block) {
    var volume = Blockly.Python.valueToCode(block, 'VOLUME', Blockly.Python.ORDER_ATOMIC) || '0';
    return 'pump.set_volume_range(' + volume + ')\n';
};

Blockly.Python['pump_set_total_steps'] = function(block) {
    var steps = Blockly.Python.valueToCode(block, 'STEPS', Blockly.Python.ORDER_ATOMIC) || '0';
    return 'pump.set_total_steps(' + steps + ')\n';
};

Blockly.Python['pump_switch_input'] = function(block) {
    return 'pump.switch_to_input()\n';
};

Blockly.Python['pump_switch_output'] = function(block) {
    return 'pump.switch_to_output()\n';
};

Blockly.Python['pump_set_speed'] = function(block) {
    var speed = Blockly.Python.valueToCode(block, 'SPEED', Blockly.Python.ORDER_ATOMIC) || '0';
    return 'pump.set_speed(' + speed + ')\n';
};

Blockly.Python['pump_aspirate'] = function(block) {
    var volume = Blockly.Python.valueToCode(block, 'VOLUME', Blockly.Python.ORDER_ATOMIC) || '0';
    return 'pump.aspirate(' + volume + ')\n';
};

Blockly.Python['pump_dispense'] = function(block) {
    var volume = Blockly.Python.valueToCode(block, 'VOLUME', Blockly.Python.ORDER_ATOMIC) || '0';
    return 'pump.dispense(' + volume + ')\n';
};

Blockly.Python['pump_stop'] = function(block) {
    return 'pump.stop()\n';
};

Blockly.Python['pump_delay'] = function(block) {
    var seconds = Blockly.Python.valueToCode(block, 'SECONDS', Blockly.Python.ORDER_ATOMIC) || '0';
    return 'import time\ntime.sleep(' + seconds + ')\n';
};
