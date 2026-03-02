"""
测试增强的异常处理系统

测试内容：
1. 错误码格式验证（XXX_### 格式）
2. 错误码重复检查
3. recovery_suggestion 功能
4. format_user_message 和 to_dict 方法
"""

import pytest
from core.exceptions import (
    ErrorCode,
    ErrorCodes,
    ErrorSeverity,
    FatalError,
    CriticalError,
    Error,
    Warning,
    IntelliSearchError,
)


class TestErrorCodeValidation:
    """测试错误码格式验证"""

    def test_valid_error_code_format(self):
        """测试有效的错误码格式"""
        # 正确的格式应该可以创建
        code = ErrorCode("TST_001", ErrorSeverity.ERROR, "测试错误")
        assert code.code == "TST_001"

    def test_invalid_error_code_format_no_underscore(self):
        """测试无效的错误码格式：缺少下划线"""
        with pytest.raises(ValueError, match="错误码格式错误"):
            ErrorCode("TST001", ErrorSeverity.ERROR, "测试错误")

    def test_invalid_error_code_format_wrong_prefix(self):
        """测试无效的错误码格式：前缀不是3个大写字母"""
        with pytest.raises(ValueError, match="错误码格式错误"):
            ErrorCode("TEST_001", ErrorSeverity.ERROR, "测试错误")

        with pytest.raises(ValueError, match="错误码格式错误"):
            ErrorCode("T1T_001", ErrorSeverity.ERROR, "测试错误")

        with pytest.raises(ValueError, match="错误码格式错误"):
            ErrorCode("tst_001", ErrorSeverity.ERROR, "测试错误")

    def test_invalid_error_code_format_wrong_number(self):
        """测试无效的错误码格式：数字部分不是3位数字"""
        with pytest.raises(ValueError, match="错误码格式错误"):
            ErrorCode("TST_01", ErrorSeverity.ERROR, "测试错误")

        with pytest.raises(ValueError, match="错误码格式错误"):
            ErrorCode("TST_0001", ErrorSeverity.ERROR, "测试错误")

        with pytest.raises(ValueError, match="错误码格式错误"):
            ErrorCode("TST_ABC", ErrorSeverity.ERROR, "测试错误")


class TestErrorCodeDuplicateDetection:
    """测试错误码重复检测"""

    def test_duplicate_error_code_detection(self):
        """测试重复错误码检测"""
        # 第一个错误码应该成功
        ErrorCode("DUP_001", ErrorSeverity.ERROR, "测试错误1")

        # 第二个相同错误码应该失败
        with pytest.raises(ValueError, match="错误码重复"):
            ErrorCode("DUP_001", ErrorSeverity.ERROR, "测试错误2")

    def test_different_error_codes_allowed(self):
        """测试不同的错误码可以共存"""
        code1 = ErrorCode("DUP_002", ErrorSeverity.ERROR, "测试错误1")
        code2 = ErrorCode("DUP_003", ErrorSeverity.ERROR, "测试错误2")
        assert code1.code == "DUP_002"
        assert code2.code == "DUP_003"


class TestRecoverySuggestion:
    """测试恢复建议功能"""

    def test_error_code_with_recovery_suggestion(self):
        """测试错误码包含恢复建议"""
        assert ErrorCodes.MCP_CONNECTION.recovery_suggestion is not None
        assert "检查" in ErrorCodes.MCP_CONNECTION.recovery_suggestion

    def test_raise_error_with_default_recovery(self):
        """测试使用默认恢复建议抛出异常"""
        with pytest.raises(CriticalError) as exc_info:
            ErrorCodes.MCP_CONNECTION.raise_error()

        assert exc_info.value.recovery_suggestion is not None
        assert "MCP 服务器" in exc_info.value.recovery_suggestion

    def test_raise_error_with_custom_recovery(self):
        """测试使用自定义恢复建议抛出异常"""
        custom_suggestion = "请重启服务器"
        with pytest.raises(CriticalError) as exc_info:
            ErrorCodes.MCP_CONNECTION.raise_error(recovery_suggestion=custom_suggestion)

        assert exc_info.value.recovery_suggestion == custom_suggestion

    def test_create_error_with_default_recovery(self):
        """测试创建异常对象使用默认恢复建议"""
        error = ErrorCodes.SEC_PERMISSION_DENIED.create_error()
        assert error.recovery_suggestion is not None
        assert "权限" in error.recovery_suggestion

    def test_create_error_with_custom_recovery(self):
        """测试创建异常对象使用自定义恢复建议"""
        custom_suggestion = "请联系管理员"
        error = ErrorCodes.SEC_PERMISSION_DENIED.create_error(
            recovery_suggestion=custom_suggestion
        )
        assert error.recovery_suggestion == custom_suggestion

    def test_all_error_codes_have_recovery_suggestions(self):
        """测试所有预定义错误码都有恢复建议"""
        for attr_name in dir(ErrorCodes):
            if attr_name.startswith("_"):
                continue

            error_code = getattr(ErrorCodes, attr_name)
            if isinstance(error_code, ErrorCode):
                assert (
                    error_code.recovery_suggestion is not None
                ), f"{attr_name} 缺少恢复建议"


class TestUserMessageFormatting:
    """测试用户友好的消息格式化"""

    def test_format_user_message_without_recovery(self):
        """测试没有恢复建议时的消息格式化"""
        error = Error(error_code="ERR_001", message="测试错误")
        message = error.format_user_message()
        assert "[ERR_001]" in message
        assert "测试错误" in message
        assert "💡 建议" not in message

    def test_format_user_message_with_recovery(self):
        """测试有恢复建议时的消息格式化"""
        error = ErrorCodes.MCP_CONNECTION.create_error()
        message = error.format_user_message()
        assert "[MCP_001]" in message
        assert "MCP 连接失败" in message
        assert "💡 建议" in message
        assert "MCP 服务器" in message

    def test_format_user_message_with_context(self):
        """测试有上下文信息时的消息格式化"""
        error = Error(
            error_code="ERR_001",
            message="测试错误",
            context={"server": "localhost", "port": 8080},
        )
        message = error.format_user_message()
        assert "详情:" in message
        assert "server=localhost" in message
        assert "port=8080" in message

    def test_format_user_message_with_recovery_and_context(self):
        """测试同时有恢复建议和上下文信息时的消息格式化"""
        # 使用 ERROR 级别的错误码，因为只有 ERROR 级别才显示详情
        error = ErrorCodes.MCP_EXECUTION.create_error(context={"tool": "search_file"})
        message = error.format_user_message()
        assert "[MCP_003]" in message
        assert "MCP 工具执行失败" in message
        assert "详情:" in message
        assert "tool=search_file" in message
        assert "💡 建议" in message


class TestToDictSerialization:
    """测试字典序列化"""

    def test_to_dict_without_recovery(self):
        """测试没有恢复建议时的序列化"""
        error = Error(error_code="ERR_001", message="测试错误")
        data = error.to_dict()
        assert data["error_code"] == "ERR_001"
        assert data["message"] == "测试错误"
        assert data["severity"] == "ERROR"
        assert data["recovery_suggestion"] is None

    def test_to_dict_with_recovery(self):
        """测试有恢复建议时的序列化"""
        error = ErrorCodes.MCP_CONNECTION.create_error()
        data = error.to_dict()
        assert data["error_code"] == "MCP_001"
        assert data["recovery_suggestion"] is not None
        assert "MCP 服务器" in data["recovery_suggestion"]

    def test_to_dict_with_all_fields(self):
        """测试包含所有字段的序列化"""
        error = ErrorCodes.SEC_PERMISSION_DENIED.create_error(
            message="自定义消息",
            context={"resource": "敏感文件"},
            cause=ValueError("原始错误"),
            recovery_suggestion="自定义建议",
        )
        data = error.to_dict()
        assert data["error_code"] == "SEC_001"
        assert data["message"] == "自定义消息"
        assert data["severity"] == "WARNING"
        assert data["context"] == {"resource": "敏感文件"}
        assert data["cause"] == "原始错误"  # cause 被转换为字符串
        assert data["recovery_suggestion"] == "自定义建议"


class TestAllErrorCodes:
    """测试所有预定义错误码"""

    def test_all_error_codes_valid_format(self):
        """测试所有预定义错误码格式有效"""
        for attr_name in dir(ErrorCodes):
            if attr_name.startswith("_"):
                continue

            error_code = getattr(ErrorCodes, attr_name)
            if isinstance(error_code, ErrorCode):
                # 验证格式
                import re

                assert re.match(
                    r"^[A-Z]{3}_\d{3}$", error_code.code
                ), f"{attr_name} 的错误码格式不正确: {error_code.code}"

    def test_all_error_codes_have_severity(self):
        """测试所有预定义错误码都有严重级别"""
        for attr_name in dir(ErrorCodes):
            if attr_name.startswith("_"):
                continue

            error_code = getattr(ErrorCodes, attr_name)
            if isinstance(error_code, ErrorCode):
                assert isinstance(
                    error_code.severity, ErrorSeverity
                ), f"{attr_name} 没有有效的严重级别"

    def test_all_error_codes_have_message(self):
        """测试所有预定义错误码都有默认消息"""
        for attr_name in dir(ErrorCodes):
            if attr_name.startswith("_"):
                continue

            error_code = getattr(ErrorCodes, attr_name)
            if isinstance(error_code, ErrorCode):
                assert error_code.default_message, f"{attr_name} 缺少默认消息"
