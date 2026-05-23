"""
永颐无机磨石 - 计算模块单元测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from materials_calc import (
    calculate_all, generate_schedule, calc_purchase_list,
    calc_cost, format_result, QUALITY_TESTS, CHECKLIST_ITEMS,
    PACKAGING_SPECS, UNIT_PRICES
)
import math


class TestMaterialCalculation:
    """材料计算测试"""

    def test_calculate_basic(self):
        """基础计算测试"""
        result = calculate_all(100)
        assert result['area'] == 100
        assert result['total_weight_kg'] > 0
        assert '硅酸盐水泥' in result['summary']
        assert 'base' in result['layers']
        assert 'surface' in result['layers']

    def test_calculate_accuracy(self):
        """计算精度验证：100m², 50mm基层, 15mm面层"""
        result = calculate_all(100)
        # 基层: 100m² * 0.05m * 2200kg/m³ = 11000kg
        # 水泥: 11000 * 40% = 4400kg
        assert abs(result['summary']['硅酸盐水泥'] - 4400) < 1
        # 中黄沙: 11000 * 30% = 3300kg
        assert abs(result['summary']['中号黄沙'] - 3300) < 1
        # 钢纤维: 11000 * 1.5% = 165kg
        assert abs(result['summary']['钢纤维'] - 165) < 0.5

    def test_calculate_different_area(self):
        """不同面积计算测试"""
        for area in [50, 200, 500, 1000]:
            result = calculate_all(area)
            assert result['area'] == area
            assert result['total_weight_kg'] > 0

    def test_calculate_different_thickness(self):
        """不同厚度计算测试"""
        result = calculate_all(100, thickness_base=30, thickness_surface=10)
        assert result['layers']['base']['thickness_mm'] == 30
        assert result['layers']['surface']['thickness_mm'] == 10

    def test_format_result(self):
        """格式化输出测试"""
        result = calculate_all(100)
        output = format_result(result)
        assert '永颐无机磨石' in output
        assert '100 m²' in output


class TestPurchaseList:
    """采购清单测试"""

    def test_purchase_list_generation(self):
        """采购清单生成测试"""
        result = calculate_all(100)
        purchase = calc_purchase_list(result['summary'])
        assert len(purchase) > 0
        for item in purchase:
            assert item['packages'] > 0
            assert item['total_kg'] > 0

    def test_purchase_packaging(self):
        """包装规格验证"""
        result = calculate_all(100)
        purchase = calc_purchase_list(result['summary'])
        for item in purchase:
            if item['name'] in PACKAGING_SPECS:
                spec = PACKAGING_SPECS[item['name']]
                expected_packages = math.ceil(item['total_kg'] / spec['per_package'])
                assert item['packages'] == expected_packages

    def test_all_materials_have_specs(self):
        """所有材料都有包装规格"""
        result = calculate_all(100)
        purchase = calc_purchase_list(result['summary'])
        for item in purchase:
            if item['total_kg'] > 0:
                assert item['per_package'] > 0


class TestCostEstimation:
    """成本估算测试"""

    def test_cost_calculation(self):
        """成本计算测试"""
        result = calculate_all(100)
        purchase = calc_purchase_list(result['summary'])
        cost = calc_cost(100, purchase)
        assert cost['total_cost'] > 0
        assert cost['material_cost'] > 0
        assert cost['labor_cost'] > 0
        assert cost['cost_per_m2'] > 0

    def test_cost_breakdown(self):
        """成本构成验证"""
        result = calculate_all(100)
        purchase = calc_purchase_list(result['summary'])
        cost = calc_cost(100, purchase)
        # 材料费 + 人工费 = 总成本
        assert abs(cost['material_cost'] + cost['labor_cost'] - cost['total_cost']) < 0.01
        # 有材料明细
        assert len(cost['material_details']) > 0
        # 有人工明细
        assert len(cost['labor_details']) > 0

    def test_unit_prices_exist(self):
        """所有材料单价存在"""
        for name in PACKAGING_SPECS:
            if name in UNIT_PRICES:
                assert UNIT_PRICES[name]['price'] > 0


class TestSchedule:
    """进度计划测试"""

    def test_schedule_length(self):
        """进度计划阶段数"""
        schedule = generate_schedule()
        assert len(schedule) == 10

    def test_schedule_ordering(self):
        """进度计划顺序正确"""
        schedule = generate_schedule()
        for i in range(len(schedule) - 1):
            assert schedule[i]['end'] <= schedule[i+1]['start'] or \
                   schedule[i]['end'] == schedule[i+1]['start']

    def test_schedule_with_start_date(self):
        """自定义开始日期"""
        schedule = generate_schedule("2024-06-01")
        assert schedule[0]['start'] == "06-01"

    def test_schedule_days_total(self):
        """总工期约22天"""
        schedule = generate_schedule()
        total_days = sum(p['days'] for p in schedule)
        assert total_days >= 20  # 至少20天


class TestQualityTests:
    """质量检测测试"""

    def test_quality_tests_count(self):
        """质量检测项数量"""
        assert len(QUALITY_TESTS) == 10

    def test_quality_tests_structure(self):
        """检测项结构完整"""
        for test in QUALITY_TESTS:
            assert 'id' in test
            assert 'name' in test
            assert 'standard' in test
            assert 'phase' in test
            assert 'method' in test


class TestChecklist:
    """检查清单测试"""

    def test_checklist_count(self):
        """检查清单项数量"""
        total = sum(len(cat['items']) for cat in CHECKLIST_ITEMS)
        assert total == 57

    def test_checklist_categories(self):
        """检查清单分类"""
        assert len(CHECKLIST_ITEMS) == 7
        categories = [cat['category'] for cat in CHECKLIST_ITEMS]
        assert '施工前准备' in categories
        assert '基层处理' in categories
        assert '最终验收' in categories

    def test_checklist_item_structure(self):
        """检查项结构完整"""
        for cat in CHECKLIST_ITEMS:
            for item in cat['items']:
                assert 'id' in item
                assert 'text' in item
                assert 'checked' in item


class TestPackagingSpecs:
    """包装规格测试"""

    def test_specs_count(self):
        """包装规格数量"""
        assert len(PACKAGING_SPECS) >= 10

    def test_specs_structure(self):
        """规格结构完整"""
        for name, spec in PACKAGING_SPECS.items():
            assert 'unit' in spec
            assert 'per_package' in spec
            assert spec['per_package'] > 0
            assert 'note' in spec
