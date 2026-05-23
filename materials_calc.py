"""
永颐无机磨石 - 材料用量计算模块
基于施工方案配比精确计算所有材料用量
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ============================================================
# 数据模型
# ============================================================

@dataclass
class MaterialItem:
    """单项材料"""
    name: str          # 材料名称
    model: str         # 型号/规格
    ratio: float       # 配比（百分比，如 40 表示 40%）
    unit: str = "kg"   # 单位
    note: str = ""     # 备注

    def calc_amount(self, total_kg: float) -> float:
        """根据总重量计算该材料用量"""
        return round(total_kg * self.ratio / 100, 2)


@dataclass
class MaterialLayer:
    """一个结构层的材料清单"""
    name: str                    # 层名称
    thickness_mm: float          # 厚度(mm)
    density: float = 2200        # 密度(kg/m³)，默认砂浆密度
    materials: List[MaterialItem] = field(default_factory=list)
    extra_items: Dict[str, float] = field(default_factory=dict)  # 额外材料 {名称: 用量kg/m²}

    @property
    def volume_per_m2(self) -> float:
        """每平米体积 (m³)"""
        return self.thickness_mm / 1000

    @property
    def weight_per_m2(self) -> float:
        """每平米重量 (kg)"""
        return round(self.volume_per_m2 * self.density, 2)

    def calc_materials(self, area_m2: float) -> Dict[str, float]:
        """计算给定面积下所有材料用量"""
        total_kg = self.weight_per_m2 * area_m2
        result = {}
        for mat in self.materials:
            result[mat.name] = mat.calc_amount(total_kg)
        # 额外材料按面积计算
        for name, rate in self.extra_items.items():
            result[name] = round(rate * area_m2, 2)
        return result


# ============================================================
# 标准配比数据
# ============================================================

# 抗裂砂浆层 (50mm厚)
BASE_LAYER = MaterialLayer(
    name="抗裂砂浆基层",
    thickness_mm=50,
    density=2200,
    materials=[
        MaterialItem("硅酸盐水泥", "42.5", 40),
        MaterialItem("中号黄沙", "0.3-1.2mm", 30),
        MaterialItem("细黄沙", "40~70目", 25),
        MaterialItem("钢纤维", "剪切型", 1.5, note="分3次加入防结团"),
        MaterialItem("永颐抗裂砂浆", "YYKLSJ-05", 1.8),
        MaterialItem("苯丙乳液", "固含量50±1%", 3),
        MaterialItem("水", "洁净水", 19),  # 取中间值 18-20%
    ],
    extra_items={
        "基层界面剂": 0.3,  # kg/m²
    }
)

# 面层 (15mm厚)
SURFACE_LAYER = MaterialLayer(
    name="无机磨石面层",
    thickness_mm=15,
    density=2200,
    materials=[
        MaterialItem("无机磨石干混料", "YYA331", 84),   # 100% - 16%水
        MaterialItem("水(B组分)", "洁净水", 16),  # 水胶比12-16%，取16%
        MaterialItem("无机磨石专用骨料", "5-8mm", 0, note="按需加入，不计入干混比例"),
    ],
    extra_items={
        "面层界面剂": 0.4,  # kg/m²
    }
)

# 密封固化层
SEALING_ITEMS = {
    "水性锂基固化剂": 0.25,      # kg/m², 2遍
    "纳米二氧化硅罩面剂": 0.1,   # kg/m², 可选
}

# 打磨耗材
GRINDING_CONSUMABLES = {
    "60目金刚石磨片": 0.02,    # 片/m² (估算)
    "150目磨片": 0.02,
    "500目磨片": 0.02,
    "1000目磨片": 0.02,
    "3000目磨片": 0.02,
}


# ============================================================
# 计算引擎
# ============================================================

def calculate_all(area_m2: float, thickness_base: float = 50,
                  thickness_surface: float = 15,
                  include_sealing: bool = True,
                  include_grinding: bool = True) -> Dict:
    """
    计算所有材料用量

    参数:
        area_m2: 施工面积 (m²)
        thickness_base: 基层厚度 (mm)，默认50
        thickness_surface: 面层厚度 (mm)，默认15
        include_sealing: 是否包含密封固化材料
        include_grinding: 是否包含打磨耗材

    返回:
        包含所有材料用量的字典
    """
    # 更新厚度
    BASE_LAYER.thickness_mm = thickness_base
    SURFACE_LAYER.thickness_mm = thickness_surface

    result = {
        "area": area_m2,
        "summary": {},
        "layers": {},
        "total_weight_kg": 0,
    }

    # 1. 抗裂砂浆层
    base_materials = BASE_LAYER.calc_materials(area_m2)
    base_total = BASE_LAYER.weight_per_m2 * area_m2
    result["layers"]["base"] = {
        "name": BASE_LAYER.name,
        "thickness_mm": BASE_LAYER.thickness_mm,
        "weight_per_m2": BASE_LAYER.weight_per_m2,
        "total_weight": round(base_total, 2),
        "materials": base_materials,
    }
    result["total_weight_kg"] += base_total

    # 2. 面层
    surface_materials = SURFACE_LAYER.calc_materials(area_m2)
    surface_total = SURFACE_LAYER.weight_per_m2 * area_m2
    result["layers"]["surface"] = {
        "name": SURFACE_LAYER.name,
        "thickness_mm": SURFACE_LAYER.thickness_mm,
        "weight_per_m2": SURFACE_LAYER.weight_per_m2,
        "total_weight": round(surface_total, 2),
        "materials": surface_materials,
    }
    result["total_weight_kg"] += surface_total

    # 3. 密封固化
    if include_sealing:
        sealing = {}
        for name, rate in SEALING_ITEMS.items():
            sealing[name] = round(rate * area_m2, 2)
        result["layers"]["sealing"] = {
            "name": "密封固化层",
            "materials": sealing,
        }

    # 4. 打磨耗材
    if include_grinding:
        grinding = {}
        for name, rate in GRINDING_CONSUMABLES.items():
            grinding[name] = round(rate * area_m2, 2)
        result["layers"]["grinding"] = {
            "name": "打磨耗材",
            "materials": grinding,
        }

    # 汇总
    all_items = {}
    for layer_key, layer_data in result["layers"].items():
        if "materials" in layer_data:
            for mat_name, amount in layer_data["materials"].items():
                if mat_name not in all_items:
                    all_items[mat_name] = 0
                all_items[mat_name] += amount

    result["summary"] = all_items
    result["total_weight_kg"] = round(result["total_weight_kg"], 2)

    return result


def generate_schedule(start_date: str = "2024-01-01") -> List[Dict]:
    """
    生成施工进度计划

    参数:
        start_date: 开始日期，格式 YYYY-MM-DD

    返回:
        阶段列表，每阶段包含名称、天数、开始日期、结束日期
    """
    from datetime import datetime, timedelta

    current = datetime.strptime(start_date, "%Y-%m-%d")

    phases = [
        ("基层处理", 3),
        ("抗裂砂浆施工", 5),
        ("基层养护", 7),
        ("面层界面处理", 1),
        ("面层浇筑", 6),
        ("面层养护", 7),
        ("粗磨(60目)", 1),
        ("中磨(150→500目)", 1),
        ("精磨(1000→3000目)", 1),
        ("密封固化", 3),
    ]

    schedule = []
    for name, days in phases:
        end = current + timedelta(days=days - 1)
        schedule.append({
            "phase": name,
            "days": days,
            "start": current.strftime("%m-%d"),
            "end": end.strftime("%m-%d"),
            "start_full": current.strftime("%Y-%m-%d"),
            "end_full": end.strftime("%Y-%m-%d"),
        })
        current = end + timedelta(days=1)

    return schedule


# ============================================================
# 辅助功能
# ============================================================

def format_result(result: Dict) -> str:
    """格式化输出计算结果（用于CLI）"""
    lines = []
    lines.append(f"{'='*50}")
    lines.append(f"  永颐无机磨石 - 材料用量计算")
    lines.append(f"  施工面积: {result['area']} m²")
    lines.append(f"  总材料重量: {result['total_weight_kg']} kg")
    lines.append(f"{'='*50}")

    for layer_key, layer_data in result["layers"].items():
        lines.append(f"\n--- {layer_data['name']} ---")
        if "thickness_mm" in layer_data:
            lines.append(f"  厚度: {layer_data['thickness_mm']}mm")
            lines.append(f"  每平米重: {layer_data['weight_per_m2']} kg/m²")
        if "materials" in layer_data:
            for mat_name, amount in layer_data["materials"].items():
                lines.append(f"  {mat_name}: {amount} kg")

    lines.append(f"\n{'='*50}")
    lines.append(f"  材料汇总")
    lines.append(f"{'='*50}")
    for mat_name, amount in result["summary"].items():
        lines.append(f"  {mat_name}: {amount} kg")

    return "\n".join(lines)


# 命令行入口
if __name__ == "__main__":
    import sys
    area = float(sys.argv[1]) if len(sys.argv) > 1 else 100
    result = calculate_all(area)
    print(format_result(result))

    print("\n\n=== 施工进度计划 ===")
    schedule = generate_schedule()
    for phase in schedule:
        print(f"  {phase['phase']}: {phase['start']} → {phase['end']} ({phase['days']}天)")


# ============================================================
# 采购换算 - 将材料用量转换为实际采购单位
# ============================================================

# 材料包装规格 (单位: kg/袋 或 L/桶)
PACKAGING_SPECS = {
    "硅酸盐水泥": {"unit": "袋", "per_package": 50, "note": "50kg/袋"},
    "中号黄沙": {"unit": "袋", "per_package": 50, "note": "50kg/袋"},
    "细黄沙": {"unit": "袋", "per_package": 50, "note": "50kg/袋"},
    "钢纤维": {"unit": "袋", "per_package": 25, "note": "25kg/袋"},
    "永颐抗裂砂浆": {"unit": "袋", "per_package": 40, "note": "40kg/袋 (YYKLSJ-05)"},
    "苯丙乳液": {"unit": "桶", "per_package": 50, "note": "50kg/桶, 固含量50±1%"},
    "基层界面剂": {"unit": "桶", "per_package": 20, "note": "20kg/桶"},
    "面层界面剂": {"unit": "桶", "per_package": 20, "note": "20kg/桶"},
    "无机磨石干混料": {"unit": "袋", "per_package": 40, "note": "40kg/袋 (YYA331)"},
    "水性锂基固化剂": {"unit": "桶", "per_package": 25, "note": "25kg/桶"},
    "纳米二氧化硅罩面剂": {"unit": "桶", "per_package": 5, "note": "5kg/桶"},
}


def calc_purchase_list(summary: Dict[str, float]) -> List[Dict]:
    """
    将材料用量换算为实际采购清单

    参数:
        summary: calculate_all() 返回的 summary 字典

    返回:
        采购清单列表，每项含材料名、用量、包装规格、采购数量、备注
    """
    purchase_list = []
    for mat_name, total_kg in summary.items():
        if total_kg <= 0:
            continue
        spec = PACKAGING_SPECS.get(mat_name)
        if spec:
            packages = int(__import__('math').ceil(total_kg / spec["per_package"]))
            purchase_list.append({
                "name": mat_name,
                "total_kg": round(total_kg, 1),
                "unit": spec["unit"],
                "per_package": spec["per_package"],
                "packages": packages,
                "actual_kg": round(packages * spec["per_package"], 1),
                "waste_kg": round(packages * spec["per_package"] - total_kg, 1),
                "note": spec["note"],
            })
        else:
            purchase_list.append({
                "name": mat_name,
                "total_kg": round(total_kg, 1),
                "unit": "kg",
                "per_package": 1,
                "packages": round(total_kg, 1),
                "actual_kg": round(total_kg, 1),
                "waste_kg": 0,
                "note": "",
            })
    return purchase_list


def generate_daily_log(project_name: str = "默认项目",
                        area: float = 100,
                        date: str = "",
                        weather: str = "晴",
                        temperature: str = "20~25℃",
                        workers: int = 5,
                        work_content: str = "",
                        issues: str = "无",
                        materials_used: str = "") -> Dict:
    """
    生成施工日志模板

    参数:
        project_name: 项目名称
        area: 施工面积
        date: 日期
        weather: 天气
        temperature: 温度
        workers: 施工人数
        work_content: 工作内容
        issues: 问题记录
        materials_used: 材料使用

    返回:
        施工日志字典
    """
    from datetime import datetime
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    return {
        "project": project_name,
        "area": area,
        "date": date,
        "weather": weather,
        "temperature": temperature,
        "workers": workers,
        "work_content": work_content,
        "issues": issues,
        "materials_used": materials_used,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ============================================================
# 材料成本估算
# ============================================================

# 材料单价 (元/单位)
UNIT_PRICES = {
    "硅酸盐水泥": {"price": 28, "unit": "袋", "spec": "50kg/袋"},
    "中号黄沙": {"price": 8, "unit": "袋", "spec": "50kg/袋"},
    "细黄沙": {"price": 10, "unit": "袋", "spec": "50kg/袋"},
    "钢纤维": {"price": 180, "unit": "袋", "spec": "25kg/袋"},
    "永颐抗裂砂浆": {"price": 85, "unit": "袋", "spec": "40kg/袋 (YYKLSJ-05)"},
    "苯丙乳液": {"price": 320, "unit": "桶", "spec": "50kg/桶, 固含量50±1%"},
    "基层界面剂": {"price": 180, "unit": "桶", "spec": "20kg/桶"},
    "面层界面剂": {"price": 180, "unit": "桶", "spec": "20kg/桶"},
    "无机磨石干混料": {"price": 95, "unit": "袋", "spec": "40kg/袋 (YYA331)"},
    "水性锂基固化剂": {"price": 450, "unit": "桶", "spec": "25kg/桶"},
    "纳米二氧化硅罩面剂": {"price": 380, "unit": "桶", "spec": "5kg/桶"},
}

# 人工费估算 (元/m²)
LABOR_COST_PER_M2 = {
    "基层处理": 15,
    "抗裂砂浆施工": 35,
    "面层施工": 45,
    "打磨抛光": 30,
    "密封固化": 20,
}


def calc_cost(area: float, purchase_list: list) -> Dict:
    """
    计算材料成本和人工费用

    参数:
        area: 施工面积 (m²)
        purchase_list: calc_purchase_list() 返回的采购清单

    返回:
        成本明细
    """
    material_cost = 0
    material_details = []

    for item in purchase_list:
        if item["name"] in UNIT_PRICES:
            price_info = UNIT_PRICES[item["name"]]
            cost = item["packages"] * price_info["price"]
            material_cost += cost
            material_details.append({
                "name": item["name"],
                "packages": item["packages"],
                "unit": item["unit"],
                "unit_price": price_info["price"],
                "cost": cost,
            })

    # 人工费
    labor_total = sum(rate * area for rate in LABOR_COST_PER_M2.values())
    labor_details = [
        {"item": name, "rate": rate, "cost": round(rate * area, 2)}
        for name, rate in LABOR_COST_PER_M2.items()
    ]

    # 总计
    total = round(material_cost + labor_total, 2)

    return {
        "area": area,
        "material_cost": round(material_cost, 2),
        "material_details": material_details,
        "labor_cost": round(labor_total, 2),
        "labor_details": labor_details,
        "total_cost": total,
        "cost_per_m2": round(total / area, 2) if area > 0 else 0,
    }


# ============================================================
# 质量检测记录
# ============================================================

QUALITY_TESTS = [
    {
        "id": "qt-01",
        "name": "基层含水率",
        "phase": "基层处理",
        "standard": "≤8%",
        "method": "1m²塑料膜覆盖24h无水珠",
        "unit": "%",
    },
    {
        "id": "qt-02",
        "name": "基层7D抗压强度",
        "phase": "基层养护",
        "standard": "≥25MPa",
        "method": "取芯检测",
        "unit": "MPa",
    },
    {
        "id": "qt-03",
        "name": "面层3D抗压强度",
        "phase": "面层养护",
        "standard": "≥25MPa",
        "method": "取芯检测",
        "unit": "MPa",
    },
    {
        "id": "qt-04",
        "name": "28D抗压强度",
        "phase": "最终验收",
        "standard": "≥50MPa",
        "method": "取芯检测",
        "unit": "MPa",
    },
    {
        "id": "qt-05",
        "name": "光泽度（未罩面）",
        "phase": "密封固化",
        "standard": "≥40 GU",
        "method": "60°光泽度仪",
        "unit": "GU",
    },
    {
        "id": "qt-06",
        "name": "光泽度（罩面）",
        "phase": "密封固化",
        "standard": "≥70 GU",
        "method": "60°光泽度仪",
        "unit": "GU",
    },
    {
        "id": "qt-07",
        "name": "抗污性",
        "phase": "最终验收",
        "standard": "咖啡/酱油24h不渗透",
        "method": "GB/T 3810.14",
        "unit": "",
    },
    {
        "id": "qt-08",
        "name": "表面粗糙度",
        "phase": "精磨",
        "standard": "Ra≤0.2μm",
        "method": "粗糙度仪",
        "unit": "μm",
    },
    {
        "id": "qt-09",
        "name": "平整度",
        "phase": "抗裂砂浆施工",
        "standard": "≤2mm",
        "method": "2m靠尺",
        "unit": "mm",
    },
    {
        "id": "qt-10",
        "name": "伸缩缝宽度",
        "phase": "基层处理",
        "standard": "5mm",
        "method": "尺量",
        "unit": "mm",
    },
]


# ============================================================
# 检查清单模板数据
# ============================================================

CHECKLIST_ITEMS = [
    {
        "category": "施工前准备",
        "phase": "准备",
        "items": [
            {"id": "prep-01", "text": "硅酸盐水泥42.5 - 检测报告齐全", "checked": False},
            {"id": "prep-02", "text": "中号黄沙（0.3-1.2mm）含泥量合格", "checked": False},
            {"id": "prep-03", "text": "细黄沙（40~70目）含泥量合格", "checked": False},
            {"id": "prep-04", "text": "钢纤维（剪切型）规格符合要求", "checked": False},
            {"id": "prep-05", "text": "永颐抗裂砂浆 YYKLSJ-05 检测报告齐全", "checked": False},
            {"id": "prep-06", "text": "苯丙乳液（固含量50±1%）检测报告齐全", "checked": False},
            {"id": "prep-07", "text": "界面剂检测报告齐全", "checked": False},
            {"id": "prep-08", "text": "无机磨石专用骨料粒径符合要求", "checked": False},
            {"id": "prep-09", "text": "水性锂基固化剂检测报告齐全", "checked": False},
            {"id": "prep-10", "text": "纳米二氧化硅罩面剂检测报告齐全", "checked": False},
            {"id": "prep-11", "text": "永颐高精找平机器人校准完成", "checked": False},
            {"id": "prep-12", "text": "金刚石磨片全套（60/150/500/1000/3000目）准备齐全", "checked": False},
            {"id": "prep-13", "text": "环境温度 5~30℃，湿度 40~70%", "checked": False},
        ]
    },
    {
        "category": "基层处理",
        "phase": "基层",
        "items": [
            {"id": "base-01", "text": "清除浮灰、油污，修补裂缝", "checked": False},
            {"id": "base-02", "text": "≥1mm裂缝注浆处理", "checked": False},
            {"id": "base-03", "text": "洒水湿润基层（施工前2h）", "checked": False},
            {"id": "base-04", "text": "无明水状态确认", "checked": False},
            {"id": "base-05", "text": "界面剂涂刷（用量0.3kg/m²）", "checked": False},
            {"id": "base-06", "text": "弹线分格（间距≤8m×8m）", "checked": False},
            {"id": "base-07", "text": "预留伸缩缝（宽5mm，深20mm）", "checked": False},
            {"id": "base-08", "text": "基层含水率检测（≤8%）", "checked": False},
        ]
    },
    {
        "category": "抗裂砂浆施工",
        "phase": "基层",
        "items": [
            {"id": "mortar-01", "text": "干料混合：水泥+黄沙+钢纤维 干拌3min", "checked": False},
            {"id": "mortar-02", "text": "钢纤维分3次加入防止结团", "checked": False},
            {"id": "mortar-03", "text": "加入永颐抗裂砂浆 干拌2min", "checked": False},
            {"id": "mortar-04", "text": "缓慢加水+苯丙乳液 湿拌5min", "checked": False},
            {"id": "mortar-05", "text": "浆体扩展度检测 160-180mm", "checked": False},
            {"id": "mortar-06", "text": "机器人摊铺找平（误差≤2mm）", "checked": False},
            {"id": "mortar-07", "text": "边角刮杠刮平", "checked": False},
            {"id": "mortar-08", "text": "磨光机收光（初凝前完成）", "checked": False},
            {"id": "mortar-09", "text": "切缝处理（终凝后24h内）", "checked": False},
            {"id": "mortar-10", "text": "浇筑后2h覆盖PE膜养护", "checked": False},
        ]
    },
    {
        "category": "面层施工",
        "phase": "面层",
        "items": [
            {"id": "surf-01", "text": "基层抗压≥20MPa，含水率≤6%", "checked": False},
            {"id": "surf-02", "text": "滚涂界面剂2遍（间隔2h，用量0.4kg/m²）", "checked": False},
            {"id": "surf-03", "text": "界面剂完全固化（触干≤4h）", "checked": False},
            {"id": "surf-04", "text": "干混料+80%B组分水 搅拌2min", "checked": False},
            {"id": "surf-05", "text": "倒入剩余20%水 搅拌3min至泛光泽", "checked": False},
            {"id": "surf-06", "text": "加入无机磨石专用骨料 搅拌1min", "checked": False},
            {"id": "surf-07", "text": "面层摊铺（机器人，误差1~2mm）", "checked": False},
            {"id": "surf-08", "text": "层间间隔≤1h，避免冷接缝", "checked": False},
            {"id": "surf-09", "text": "初凝前镘刀收光2次消除气孔", "checked": False},
            {"id": "surf-10", "text": "浇筑后4h覆盖无纺布+PE膜养护", "checked": False},
        ]
    },
    {
        "category": "打磨抛光",
        "phase": "打磨",
        "items": [
            {"id": "grind-01", "text": "粗磨：60目金刚石磨片，去除浮浆", "checked": False},
            {"id": "grind-02", "text": "中磨：150目→500目，消除划痕", "checked": False},
            {"id": "grind-03", "text": "精磨：1000目→3000目，Ra≤0.2μm", "checked": False},
            {"id": "grind-04", "text": "打磨深度≤3mm，避免骨料脱落", "checked": False},
            {"id": "grind-05", "text": "边角区域手工精磨，防止机器啃边", "checked": False},
        ]
    },
    {
        "category": "密封固化",
        "phase": "固化",
        "items": [
            {"id": "seal-01", "text": "滚涂水性锂基固化剂第1遍", "checked": False},
            {"id": "seal-02", "text": "间隔4h滚涂第2遍（用量0.25kg/m²）", "checked": False},
            {"id": "seal-03", "text": "固化48h后高速抛光（1500rpm+白色垫片）", "checked": False},
            {"id": "seal-04", "text": "喷涂纳米二氧化硅罩面（可选，用量0.1kg/m²）", "checked": False},
        ]
    },
    {
        "category": "最终验收",
        "phase": "验收",
        "items": [
            {"id": "final-01", "text": "28D抗压强度≥50MPa", "checked": False},
            {"id": "final-02", "text": "光泽度≥40GU（未罩面）/ ≥70GU（罩面）", "checked": False},
            {"id": "final-03", "text": "抗污性：咖啡/酱油24h不渗透", "checked": False},
            {"id": "final-04", "text": "整体无裂缝、无起砂、无脱粒", "checked": False},
            {"id": "final-05", "text": "材料检测报告归档", "checked": False},
            {"id": "final-06", "text": "伸缩缝处理照片存档", "checked": False},
            {"id": "final-07", "text": "施工日志填写完整", "checked": False},
        ]
    }
]
