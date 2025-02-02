// 旋转阀控制块定义

// 初始化旋转阀
Blockly.Blocks['init_valve'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("初始化旋转阀");
        this.appendValueInput("SERIAL_CONFIG")
            .setCheck("SerialConfig")
            .appendField("串口设置");
        this.appendValueInput("DEVICE_ADDRESS")
            .setCheck("Number")
            .appendField("设备地址");
        this.setInputsInline(false);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(230);
        this.setTooltip("初始化12通旋转阀，需要串口设置和设备地址");
        this.setHelpUrl("");
    }
};

Blockly.Python['init_valve'] = function(block) {
    var serial_config = Blockly.Python.valueToCode(block, 'SERIAL_CONFIG', Blockly.Python.ORDER_ATOMIC);
    var device_address = Blockly.Python.valueToCode(block, 'DEVICE_ADDRESS', Blockly.Python.ORDER_ATOMIC);
    
    // 生成初始化代码
    var code = '';
    code += 'serial_controller = SerialController()\n';
    code += `if serial_controller.connect(${serial_config}):\n`;
    code += '    valve = ValveController(serial_controller)\n';
    code += `    valve.initialize(${device_address})\n`;
    
    return code;
};

// 旋转到指定孔位
Blockly.Blocks['rotate_valve'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("旋转阀转到孔位");
        this.appendValueInput("POSITION")
            .setCheck("Number");
        this.setInputsInline(true);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(230);
        this.setTooltip("控制旋转阀转到指定孔位 (1-12)");
        this.setHelpUrl("");
    }
};

Blockly.Python['rotate_valve'] = function(block) {
    var position = Blockly.Python.valueToCode(block, 'POSITION', Blockly.Python.ORDER_ATOMIC);
    var code = `valve.rotate_to_position(${position})\n`;
    return code;
};

// 获取当前孔位
Blockly.Blocks['get_valve_position'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("获取旋转阀当前孔位");
        this.setOutput(true, "Number");
        this.setColour(230);
        this.setTooltip("获取旋转阀当前所在孔位");
        this.setHelpUrl("");
    }
};

Blockly.Python['get_valve_position'] = function(block) {
    var code = 'valve.get_current_position()';
    return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};

// 获取断电前孔位
Blockly.Blocks['get_valve_last_position'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("获取旋转阀断电前孔位");
        this.setOutput(true, "Number");
        this.setColour(230);
        this.setTooltip("获取旋转阀断电前的孔位");
        this.setHelpUrl("");
    }
};

Blockly.Python['get_valve_last_position'] = function(block) {
    var code = 'valve.get_last_position()';
    return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};
