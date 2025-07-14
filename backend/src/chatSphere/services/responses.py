"""
统一的API响应格式和状态码定义
"""
from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel


class ResponseCode(Enum):
    """响应状态码枚举"""

    # 成功状态码 (20000-29999)
    SUCCESS = 20000
    CREATED = 20001
    UPDATED = 20002
    DELETED = 20003

    # 客户端错误 (40000-49999)
    BAD_REQUEST = 40000
    UNAUTHORIZED = 40001
    FORBIDDEN = 40003
    NOT_FOUND = 40004
    METHOD_NOT_ALLOWED = 40005
    CONFLICT = 40009
    VALIDATION_ERROR = 40022
    TOO_MANY_REQUESTS = 40029

    # 业务逻辑错误 (41000-41999)
    USER_NOT_FOUND = 41001
    USER_ALREADY_EXISTS = 41002
    INVALID_CREDENTIALS = 41003
    ACCOUNT_DISABLED = 41004
    EMAIL_ALREADY_EXISTS = 41005
    USERNAME_ALREADY_EXISTS = 41006
    WEAK_PASSWORD = 41007
    INVALID_TOKEN = 41008
    TOKEN_EXPIRED = 41009
    REFRESH_TOKEN_INVALID = 41010

    # 聊天相关错误 (42000-42999)
    ROOM_NOT_FOUND = 42001
    ROOM_ACCESS_DENIED = 42002
    MESSAGE_NOT_FOUND = 42003
    INVALID_MESSAGE_TYPE = 42004

    # 服务器错误 (50000-59999)
    INTERNAL_ERROR = 50000
    DATABASE_ERROR = 50001
    CACHE_ERROR = 50002
    EXTERNAL_SERVICE_ERROR = 50003


class ResponseMessage:
    """响应消息常量"""

    # 成功消息
    SUCCESS = "操作成功"
    CREATED = "创建成功"
    UPDATED = "更新成功"
    DELETED = "删除成功"

    # 认证相关
    LOGIN_SUCCESS = "登录成功"
    LOGOUT_SUCCESS = "退出登录成功"
    REGISTER_SUCCESS = "注册成功"
    TOKEN_REFRESHED = "Token刷新成功"

    # 错误消息
    BAD_REQUEST = "请求参数错误"
    UNAUTHORIZED = "未授权访问"
    FORBIDDEN = "禁止访问"
    NOT_FOUND = "资源不存在"
    INTERNAL_ERROR = "服务器内部错误"

    # 用户相关错误
    USER_NOT_FOUND = "用户不存在"
    USER_ALREADY_EXISTS = "用户已存在"
    INVALID_CREDENTIALS = "用户名或密码错误"
    EMAIL_ALREADY_EXISTS = "邮箱已被使用"
    USERNAME_ALREADY_EXISTS = "用户名已被使用"
    WEAK_PASSWORD = "密码强度不足"
    INVALID_TOKEN = "无效的Token"
    TOKEN_EXPIRED = "Token已过期"

    # 聊天相关
    ROOM_NOT_FOUND = "聊天室不存在"
    ROOM_ACCESS_DENIED = "无权限访问该聊天室"
    MESSAGE_SENT = "消息发送成功"


class ApiResponse(BaseModel):
    """统一API响应格式"""

    code: int
    message: str
    data: Optional[Any] = None

    @classmethod
    def success(
        cls,
        data: Any = None,
        message: str = ResponseMessage.SUCCESS,
        code: ResponseCode = ResponseCode.SUCCESS,
    ):
        """成功响应"""
        return cls(code=code.value, message=message, data=data)

    @classmethod
    def error(cls, message: str, code: ResponseCode, data: Any = None):
        """错误响应"""
        return cls(code=code.value, message=message, data=data)

    @classmethod
    def created(cls, data: Any = None, message: str = ResponseMessage.CREATED):
        """创建成功响应"""
        return cls.success(data=data, message=message, code=ResponseCode.CREATED)

    @classmethod
    def updated(cls, data: Any = None, message: str = ResponseMessage.UPDATED):
        """更新成功响应"""
        return cls.success(data=data, message=message, code=ResponseCode.UPDATED)

    @classmethod
    def deleted(cls, message: str = ResponseMessage.DELETED):
        """删除成功响应"""
        return cls.success(message=message, code=ResponseCode.DELETED)


class ValidationErrorResponse(BaseModel):
    """验证错误响应格式"""

    code: int = ResponseCode.VALIDATION_ERROR.value
    message: str = "数据验证失败"
    data: Dict[str, Any]


class ErrorDetail(BaseModel):
    """错误详情"""

    field: str
    message: str
    value: Any = None


def format_validation_errors(errors: list) -> ApiResponse:
    """格式化验证错误"""
    error_details = []
    for error in errors:
        error_details.append(
            {
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "value": error.get("input"),
            }
        )

    return ApiResponse.error(
        code=ResponseCode.VALIDATION_ERROR, message="数据验证失败", data={"errors": error_details}
    )


# HTTP状态码映射
HTTP_STATUS_MAP = {
    ResponseCode.SUCCESS: 200,
    ResponseCode.CREATED: 201,
    ResponseCode.UPDATED: 200,
    ResponseCode.DELETED: 200,
    ResponseCode.BAD_REQUEST: 400,
    ResponseCode.UNAUTHORIZED: 401,
    ResponseCode.FORBIDDEN: 403,
    ResponseCode.NOT_FOUND: 404,
    ResponseCode.METHOD_NOT_ALLOWED: 405,
    ResponseCode.CONFLICT: 409,
    ResponseCode.VALIDATION_ERROR: 422,
    ResponseCode.TOO_MANY_REQUESTS: 429,
    ResponseCode.USER_NOT_FOUND: 404,
    ResponseCode.USER_ALREADY_EXISTS: 409,
    ResponseCode.INVALID_CREDENTIALS: 401,
    ResponseCode.EMAIL_ALREADY_EXISTS: 409,
    ResponseCode.USERNAME_ALREADY_EXISTS: 409,
    ResponseCode.WEAK_PASSWORD: 400,
    ResponseCode.INVALID_TOKEN: 401,
    ResponseCode.TOKEN_EXPIRED: 401,
    ResponseCode.ROOM_NOT_FOUND: 404,
    ResponseCode.ROOM_ACCESS_DENIED: 403,
    ResponseCode.INTERNAL_ERROR: 500,
    ResponseCode.DATABASE_ERROR: 500,
    ResponseCode.CACHE_ERROR: 500,
    ResponseCode.EXTERNAL_SERVICE_ERROR: 503,
}
