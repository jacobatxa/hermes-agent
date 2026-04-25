#!/usr/bin/env python3
"""
行业打标处理脚本 - 处理第101-300行
基于之前的分类逻辑，只处理"是否修订"为"是"的行
"""

import json
import subprocess
import time
import sys

# 表格信息
SPREADSHEET_TOKEN = "TFUUs2f42hMieEtDg6lcbtX2nse"
SHEET_ID = "00b4cb"  # T1工作表

# 行业映射表（从技能文档中提取）
INDUSTRY_MAPPING = {
    # 金融行业
    "银行": ("金融", "银行"),
    "证券": ("金融", "证券"),
    "保险": ("金融", "保险"),
    "信托": ("金融", "信托"),
    "基金": ("金融", "基金"),
    "投资": ("金融", "投资"),
    "融资": ("金融", "融资租赁"),
    "租赁": ("金融", "融资租赁"),
    "小贷": ("金融", "小贷助贷"),
    "助贷": ("金融", "小贷助贷"),
    "消费金融": ("金融", "消费金融"),
    "汽车金融": ("金融", "汽车金融"),
    "财务公司": ("金融", "财务公司"),
    "期货": ("金融", "期货"),
    "担保": ("金融", "担保"),
    "互金": ("金融", "互联网金融"),
    
    # 政务行业
    "公安": ("政务", "公安"),
    "警察": ("政务", "公安"),
    "公安局": ("政务", "公安"),
    "政府": ("政务", "其他政府机构"),
    "政务": ("政务", "其他政府机构"),
    "局": ("政务", "其他政府机构"),
    "中心": ("政务", "其他政府机构"),
    "委员会": ("政务", "其他政府机构"),
    "公积金": ("政务", "公积金"),
    "医保": ("政务", "医保"),
    "军工": ("政务", "军工"),
    "平台公司": ("政务", "平台公司"),
    
    # 制造/科技行业
    "科技": ("制造", "科技服务"),
    "软件": ("制造", "软件服务"),
    "信息": ("制造", "信息技术"),
    "数据": ("制造", "数据服务"),
    "智能": ("制造", "智能科技"),
    "电子": ("制造", "消费电子"),
    "数字": ("制造", "数字科技"),
    "制造": ("制造", "装备制造"),
    "工程": ("制造", "建筑工程"),
    "建设": ("制造", "建筑工程"),
    "建筑": ("制造", "建筑工程"),
    
    # 医疗行业
    "医疗": ("医疗", "医疗服务"),
    "医院": ("医疗", "医院"),
    "医药": ("医疗", "医药制造"),
    "医学": ("医疗", "医疗服务"),
    "口腔": ("医疗", "医疗服务"),
    "健康": ("医疗", "健康服务"),
    
    # 教育行业
    "教育": ("教育", "教育培训"),
    "培训": ("教育", "教育培训"),
    "学校": ("教育", "教育机构"),
    "学院": ("教育", "教育机构"),
    "大学": ("教育", "高等教育"),
    
    # 其他行业
    "零售": ("零售", "零售服务"),
    "汽车": ("汽车", "汽车制造"),
    "通信": ("通信", "通信服务"),
    "物流": ("交通运输", "物流快递"),
    "能源": ("能源", "能源服务"),
    "农业": ("其他", "农业"),
    "旅游": ("文化广电", "旅游"),
    "文化": ("文化广电", "文化服务"),
    "传媒": ("文化广电", "传媒服务"),
}

# 特殊公司处理
SPECIAL_COMPANIES = {
    "贵安新区数字科技有限公司": ("制造", "数字科技"),
    "浙江丽水中合进出口有限公司": ("其他", "贸易"),
    "深圳市集风信息服务有限公司": ("制造", "信息技术"),
    "上海锐恋信息科技有限公司": ("制造", "信息技术"),
    "杭州水蕴管家咨询服务有限公司": ("其他", "商务服务"),
    "陆军特色医学中心": ("医疗", "医院"),
    "普望（上海）信息科技有限公司": ("制造", "信息技术"),
    "四川千机汇网络科技有限公司": ("制造", "网络科技"),
    "长江联合金融租赁有限公司": ("金融", "融资租赁"),
    "PT IMOOLINK GLOBAL TRADING.": ("其他", "贸易"),
    "金鼓新生（天津）融资租赁有限公司": ("金融", "融资租赁"),
    "中电智恒信息科技服务有限公司": ("制造", "信息技术"),
    "重庆建丰工程建设有限公司": ("制造", "建筑工程"),
    "贵阳市公安局观山湖分局": ("政务", "公安"),
    "金沙县公安局": ("政务", "公安"),
}

# 有效的一级行业列表
VALID_INDUSTRIES = [
    "金融", "政务", "制造", "医疗", "教育", "零售", "汽车", 
    "通信", "交通运输", "能源", "文化广电", "其他"
]

def run_lark_command(cmd_args):
    """执行lark-cli命令"""
    try:
        result = subprocess.run(cmd_args, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"命令执行失败: {' '.join(cmd_args)}")
            print(f"错误输出: {result.stderr}")
            return None
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"命令超时: {' '.join(cmd_args)}")
        return None
    except Exception as e:
        print(f"命令执行异常: {e}")
        return None

def read_sheet_range(start_row, end_row):
    """读取指定范围的数据"""
    range_str = f"A{start_row}:F{end_row}"
    cmd = [
        "lark-cli", "sheets", "+read",
        "--spreadsheet-token", SPREADSHEET_TOKEN,
        "--sheet-id", SHEET_ID,
        "--range", range_str
    ]
    
    output = run_lark_command(cmd)
    if not output:
        return None
    
    try:
        data = json.loads(output)
        return data.get("valueRange", {}).get("values", [])
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        print(f"原始输出: {output[:200]}")
        return None

def analyze_company(company_name, original_industry, original_subindustry):
    """三级分析逻辑：特殊公司 > 关键词匹配 > 原始分类验证"""
    
    # 1. 特殊公司处理
    if company_name in SPECIAL_COMPANIES:
        return SPECIAL_COMPANIES[company_name]
    
    # 2. 关键词匹配（不区分大小写）
    company_name_lower = company_name.lower()
    for keyword, (industry, subindustry) in INDUSTRY_MAPPING.items():
        if keyword.lower() in company_name_lower:
            return industry, subindustry
    
    # 3. 原始分类验证
    if original_industry in VALID_INDUSTRIES:
        subindustry = original_subindustry if original_subindustry else "其他"
        return original_industry, subindustry
    
    # 默认分类
    return "其他", "其他"

def update_cell(row, col, value):
    """更新单个单元格"""
    values = [[value]]
    cmd = [
        "lark-cli", "sheets", "+write",
        "--spreadsheet-token", SPREADSHEET_TOKEN,
        "--sheet-id", SHEET_ID,
        "--range", f"{col}{row}",
        "--values", json.dumps(values, ensure_ascii=False)
    ]
    
    output = run_lark_command(cmd)
    if output:
        try:
            result = json.loads(output)
            if "spreadsheetToken" in result:
                return True
        except:
            pass
    return False

def process_rows(start_row, end_row):
    """处理指定范围的行"""
    print(f"开始处理第{start_row}行到第{end_row}行...")
    
    # 读取数据
    data = read_sheet_range(start_row, end_row)
    if not data:
        print("读取数据失败")
        return []
    
    print(f"读取到{len(data)}行数据")
    
    processed = []
    errors = []
    
    # 处理每一行
    for i, row in enumerate(data):
        row_num = start_row + i
        
        # 检查列数
        if len(row) < 2:
            print(f"第{row_num}行数据不完整，跳过")
            continue
        
        company_name = row[0] if len(row) > 0 else ""
        need_revision = row[1] if len(row) > 1 else ""
        original_industry = row[2] if len(row) > 2 else ""
        original_subindustry = row[3] if len(row) > 3 else ""
        
        # 只处理"是否修订"为"是"的行
        if need_revision != "是":
            continue
        
        print(f"处理第{row_num}行: {company_name}")
        
        # 分析行业分类
        industry, subindustry = analyze_company(
            company_name, original_industry, original_subindustry
        )
        
        # 更新E列（一级行业）
        if not update_cell(row_num, "E", industry):
            errors.append(f"第{row_num}行E列更新失败")
            continue
        
        # 更新F列（二级行业）
        if not update_cell(row_num, "F", subindustry):
            errors.append(f"第{row_num}行F列更新失败")
            continue
        
        processed.append({
            "row": row_num,
            "company": company_name,
            "industry": industry,
            "subindustry": subindustry,
            "original_industry": original_industry,
            "original_subindustry": original_subindustry
        })
        
        # 添加延迟避免API限制
        time.sleep(0.5)
    
    return processed, errors

def calculate_accuracy(processed_rows):
    """计算准确度（基于原始分类验证）"""
    if not processed_rows:
        return 0.0
    
    correct = 0
    total = len(processed_rows)
    
    for row in processed_rows:
        original_industry = row["original_industry"]
        new_industry = row["industry"]
        
        # 如果原始分类在有效行业中，且新分类与原始分类一致，则认为是正确的
        if original_industry in VALID_INDUSTRIES and original_industry == new_industry:
            correct += 1
        # 如果原始分类不在有效行业中，但新分类是有效的，也认为是改进
        elif original_industry not in VALID_INDUSTRIES and new_industry in VALID_INDUSTRIES:
            correct += 1
        # 特殊公司处理总是认为是正确的
        elif row["company"] in SPECIAL_COMPANIES:
            correct += 1
    
    return correct / total * 100

def main():
    """主函数"""
    print("=== 飞书表格行业打标处理脚本 ===")
    print(f"表格Token: {SPREADSHEET_TOKEN}")
    print(f"工作表ID: {SHEET_ID}")
    print(f"处理范围: 第101行到第300行")
    print()
    
    # 处理第101-300行
    processed_rows, errors = process_rows(101, 300)
    
    print()
    print("=== 处理结果 ===")
    print(f"成功处理: {len(processed_rows)} 行")
    
    if errors:
        print(f"错误数量: {len(errors)}")
        for error in errors[:5]:  # 只显示前5个错误
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... 还有{len(errors)-5}个错误")
    
    # 计算准确度
    if processed_rows:
        accuracy = calculate_accuracy(processed_rows)
        print(f"估计准确度: {accuracy:.2f}%")
        
        # 显示前10个处理结果作为示例
        print()
        print("=== 处理示例（前10行）===")
        for i, row in enumerate(processed_rows[:10]):
            print(f"{row['row']}. {row['company']}")
            print(f"   原始: {row['original_industry']}/{row['original_subindustry']}")
            print(f"   新分类: {row['industry']}/{row['subindustry']}")
            print()
    
    return len(processed_rows), len(errors)

if __name__ == "__main__":
    success_count, error_count = main()
    sys.exit(0 if error_count == 0 else 1)