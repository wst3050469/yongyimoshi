"""
永颐无机磨石 - 请求验证模块
提供统一的输入验证和错误处理
"""

from typing import Any, Dict, List, Optional, Tuple, Callable
from functools import wraps
from flask import jsonify, request


class ValidationError(Exception):
    """验证错误"""
    def __init__(self, message: str, field: str = "", code: int = 400):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(self.message)


def validate_required(data: Dict, fields: List[str]) -> Optional[str]:
    """验证必填字段"""
    for field in fields:
        if field not in data or data[field] is None:
            return f"缺少必填字段: {field}"
        if isinstance(data[field], str) and not data[field].strip():
            return f"字段不能为空: {field}"
    return None


def validate_number(value: Any, field: str,
                    min_val: float = None, max_val: float = None) -> Optional[str]:
    """验证数值"""
    try:
        v = float(value)
        if min_val is not None and v < min_val:
            return f"{field} 不能小于 {min_val}"
        if max_val is not None and v > max_val:
            return f"{field} 不能大于 {max_val}"
    except (TypeError, ValueError):
        return f"{field} 必须是有效数字"
    return None


def validate_string(value: Any, field: str,
                    max_length: int = None) -> Optional[str]:
    """验证字符串"""
    if not isinstance(value, str):
        return f"{field} 必须是字符串"
    if max_length and len(value) > max_length:
        return f"{field} 长度不能超过 {max_length} 字符"
    return None


def validate_date(date_str: str, field: str) -> Optional[str]:
    """验证日期格式 YYYY-MM-DD"""
    import re
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return f"{field} 格式无效 (应为 YYYY-MM-DD)"
    return None


# 施工阶段枚举
VALID_PHASES = [
    "基层处理", "抗裂砂浆施工", "面层施工",
    "打磨抛光", "密封固化", "最终验收"
]

# 材料名称枚举
from materials_calc import PACKAGING_SPECS
VALID_MATERIALS = list(PACKAGING_SPECS.keys())


def api_error(message: str, code: int = 400, details: Dict = None):
    """统一错误响应"""
    response = {"error": message, "status": "error"}
    if details:
        response["details"] = details
    return jsonify(response), code


def api_success(data: Any = None, message: str = ""):
    """统一成功响应"""
    response = {"status": "ok"}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return jsonify(response)


# 领域特定验证
def validate_project_data(data: Dict) -> List[str]:
    """验证项目数据"""
    errors = []
    if 'name' in data:
        err = validate_string(data['name'], '项目名称', max_length=100)
        if err: errors.append(err)
    if 'area' in data:
        err = validate_number(data['area'], '面积', min_val=1, max_val=100000)
        if err: errors.append(err)
    if 'base_thickness' in data:
        err = validate_number(data['base_thickness'], '基层厚度', min_val=10, max_val=200)
        if err: errors.append(err)
    if 'surface_thickness' in data:
        err = validate_number(data['surface_thickness'], '面层厚度', min_val=5, max_val=50)
        if err: errors.append(err)
    return errors


def validate_inventory_data(data: Dict) -> List[str]:
    """验证库存数据"""
    errors = []
    if 'material_name' in data:
        if data['material_name'] not in VALID_MATERIALS:
            errors.append(f"材料名称无效: {data['material_name']}")
    else:
        errors.append("缺少材料名称")
    if 'quantity_kg' in data:
        err = validate_number(data['quantity_kg'], '数量', min_val=0.1)
        if err: errors.append(err)
    return errors
