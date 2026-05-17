#!/usr/bin/env python3
"""
AI Enablement 阻力诊断脚本
功能：接收员工问答信息 → 诊断阻力类型 → 输出干预方案
"""

import argparse
import json
import sys
from typing import Dict, List, Any


# ============ 问答题库定义 ============
QUESTIONS = {
    "Q1": {
        "text": "你对新AI工具的第一感受？",
        "options": {"A": "完全不想了解，习惯旧方法", "B": "好奇但观望，怕麻烦", 
                   "C": "愿意了解，想试试", "D": "非常期待，想马上用"},
        "dimension": "惯性"
    },
    "Q2": {
        "text": "你觉得用AI最大的顾虑是？",
        "options": {"A": "太复杂，学不会", "B": "没时间，耽误业绩", 
                   "C": "记不住，用不好", "D": "没顾虑，愿意学"},
        "dimension": "惰性",
        "multi_select": True
    },
    "Q3": {
        "text": "你担心AI会带来什么影响？",
        "options": {"A": "替代自己，丢工作", "B": "操作出错，影响客户", 
                   "C": "被公司监控、考核", "D": "没担心，觉得是帮手"},
        "dimension": "情绪",
        "multi_select": True
    },
    "Q4": {
        "text": "如果公司要求你用AI，你的感受是？",
        "options": {"A": "反感，坚决不用", "B": "抵触，敷衍应付", 
                   "C": "中立，看效果再说", "D": "配合，愿意尝试"},
        "dimension": "抵触"
    },
    "Q5": {
        "text": "你认为AI工具对你的工作？",
        "options": {"A": "没用，不如人工", "B": "一般，可替代可不用", 
                   "C": "有用，能帮省时间", "D": "很有用，能提升业绩"},
        "dimension": "惯性"
    },
    "Q6": {
        "text": "你愿意花多久时间学习AI基础操作？",
        "options": {"A": "3分钟以内", "B": "10分钟以内", 
                   "C": "30分钟以内", "D": "不愿意花时间"},
        "dimension": "惰性"
    },
    "Q7": {
        "text": "你觉得试用AI的风险？",
        "options": {"A": "风险很大，怕出错", "B": "有一点风险，能接受", 
                   "C": "没风险，很安全", "D": "不清楚"},
        "dimension": "情绪"
    },
    "Q8": {
        "text": "你使用AI的前提是？",
        "options": {"A": "自愿选择，没人强迫", "B": "公司推荐，不强求", 
                   "C": "领导要求，不得不做", "D": "无所谓，听安排"},
        "dimension": "抵触"
    }
}

# ============ 触发规则定义 ============
TRIGGER_RULES = {
    "惯性": {
        "conditions": [
            ("Q1", ["A"]),
            ("Q5", ["A"]),
            ("Q4", ["A", "B"]),
            ("Q9", ["习惯旧的", "没用", "不如人工"])
        ],
        "threshold": 2,
        "description": "惯性阻力"
    },
    "惰性": {
        "conditions": [
            ("Q2", ["A", "B", "C"]),
            ("Q6", ["A", "D"]),
            ("Q9", ["复杂", "麻烦", "没时间"])
        ],
        "threshold": 2,
        "description": "惰性阻力"
    },
    "情绪": {
        "conditions": [
            ("Q3", ["A", "B", "C"]),
            ("Q7", ["A"]),
            ("Q9", ["替代", "监控", "出错"])
        ],
        "threshold": 2,
        "description": "情绪阻力"
    },
    "抵触": {
        "conditions": [
            ("Q4", ["A", "B"]),
            ("Q8", ["C"]),
            ("Q9", ["强迫", "管我", "不想被安排"])
        ],
        "threshold": 2,
        "description": "抵触阻力"
    }
}

# ============ 底层原理 ============
RESISTANCE_PRINCIPLES = {
    "惯性": "大脑偏好熟悉=安全，排斥陌生工具；保险行业经验崇拜。",
    "惰性": "人趋易避难，怕额外学习成本；业绩优先，怕耽误出单。",
    "情绪": "变革触发不确定性，引发生存焦虑、失控感、尊严威胁。",
    "抵触": "自主需求被剥夺，产生心理逆反；反感强推与管控。"
}

# ============ 干预方案库 ============
INTERVENTION_PLANS = {
    "惯性": [
        {
            "title": "绑定旧习惯",
            "content": "将AI工具与员工熟悉的工作流程关联，如'就像你用XX工具一样简单'，降低认知门槛。"
        },
        {
            "title": "熟人背书",
            "content": "安排同岗位、同资历的'榜样员工'分享使用经验，用同行案例替代官方宣传。"
        },
        {
            "title": "极简功能破冰",
            "content": "从最简单、最直接的一个功能开始（如一键生成日报），让员工立即体验成功。"
        },
        {
            "title": "每日短演示",
            "content": "每天用2分钟演示一个实际工作场景，让员工持续接触而非一次性灌输。"
        }
    ],
    "惰性": [
        {
            "title": "零门槛承诺",
            "content": "明确承诺'3分钟学会核心功能'，并提供'学不会找我'的兜底支持。"
        },
        {
            "title": "减负绑定",
            "content": "将AI使用与现有工作流程绑定，如'每天节省30分钟处理重复工作'。"
        },
        {
            "title": "1v1极简教学",
            "content": "手把手带员工完成第一次操作，观察其困惑点并即时解答。"
        },
        {
            "title": "首用小奖励",
            "content": "设置'首次成功使用'奖励，降低学习成本感知。"
        }
    ],
    "情绪": [
        {
            "title": "恐惧拆解",
            "content": "针对具体担忧（如'替代工作'）提供数据和案例，说明AI是助手而非替代者。"
        },
        {
            "title": "低风险试用",
            "content": "提供'沙盒环境'，允许员工在不影响实际工作的情况下自由探索。"
        },
        {
            "title": "价值可视化",
            "content": "展示AI在同类岗位上的实际效果数据，用结果说话而非理论说服。"
        },
        {
            "title": "隐私承诺",
            "content": "明确说明数据使用范围，提供'仅用于优化体验'的书面承诺。"
        }
    ],
    "抵触": [
        {
            "title": "共识式提问",
            "content": "用提问引导思考：'如果有一个工具能让你每天多陪家人1小时，你愿意了解吗？'"
        },
        {
            "title": "归还选择权",
            "content": "将'必须用'转变为'我建议你可以试试'，允许员工按自己节奏推进。"
        },
        {
            "title": "共创感植入",
            "content": "邀请员工成为'AI体验官'，收集其反馈并实际改进，让其有参与感。"
        },
        {
            "title": "榜样引领",
            "content": "展示同岗位标杆员工的使用效果，用实际成果吸引而非要求。"
        }
    ]
}

# ============ 沟通话术库 ============
COMMUNICATION_SCRIPTS = {
    "惯性": [
        "我理解你用老方法已经很顺手了，其实这个AI工具就是帮你把熟悉的流程做得更快，就像从手动挡换成自动挡。",
        "XX（同事名字）之前也这么想，但用了之后发现每天能省半小时处理重复工作，你要不要试试看？"
    ],
    "惰性": [
        "你放心，我保证3分钟就能学会核心功能，学不会我一对一教你。",
        "这个工具不需要你专门花时间学，就是把你现在做的工作自动化，边做边学就行。"
    ],
    "情绪": [
        "完全理解你的担心，其实AI只是帮你处理重复工作，你的判断力和客户关系才是核心价值。",
        "公司不会用AI来考核你，它只是帮你减轻负担，让我们有更多时间做有价值的事。"
    ],
    "抵触": [
        "我不是来要求你用的，就是想听听你的想法，看怎么能让这个工具对你真正有用。",
        "你愿不愿意先当我的'体验官'，用一段时间告诉我哪里不好用，我们一起改进？"
    ]
}


def normalize_answer(answer: Any) -> List[str]:
    """规范化答案格式，支持单选和多选"""
    if isinstance(answer, str):
        return [answer]
    elif isinstance(answer, list):
        return answer
    return []


def check_q9_keywords(text: str, keywords: List[str]) -> bool:
    """检查Q9开放式问题是否包含关键词"""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def evaluate_resistance(resistance_type: str, closed_q: Dict, open_q: Dict) -> Dict:
    """
    评估单个阻力类型的触发情况
    返回：{"triggered": bool, "level": str, "signals": [], "matched_conditions": []}
    """
    rule = TRIGGER_RULES[resistance_type]
    matched_count = 0
    signals = []
    matched_conditions = []

    for condition in rule["conditions"]:
        q_name = condition[0]
        expected_values = condition[1]

        if q_name == "Q9":
            # 开放式问题关键词匹配
            q9_text = open_q.get("Q9", "")
            if check_q9_keywords(q9_text, expected_values):
                matched_count += 1
                signals.append(f"Q9包含关键词: {expected_values}")
                matched_conditions.append(("Q9", expected_values))
        else:
            # 封闭式问题匹配
            answer = closed_q.get(q_name, [])
            normalized = normalize_answer(answer)
            
            if normalized:
                if any(ans in expected_values for ans in normalized):
                    matched_count += 1
                    q_info = QUESTIONS.get(q_name, {})
                    option_texts = [q_info.get("options", {}).get(ans, ans) for ans in normalized]
                    signals.append(f"{q_name}: {option_texts}")
                    matched_conditions.append((q_name, normalized))

    triggered = matched_count >= rule["threshold"]
    
    # 计算阻力等级
    if triggered:
        if matched_count >= 3:
            level = "高"
        elif matched_count >= 2:
            level = "中"
        else:
            level = "低"
    else:
        level = "无"

    return {
        "triggered": triggered,
        "level": level,
        "signals": signals,
        "matched_count": matched_count,
        "threshold": rule["threshold"],
        "matched_conditions": matched_conditions
    }


def get_intervention_plan(resistance_type: str, level: str) -> List[Dict]:
    """根据阻力类型和等级返回干预方案"""
    if level == "无":
        return []
    
    all_plans = INTERVENTION_PLANS.get(resistance_type, [])
    
    # 根据等级选择方案数量
    if level == "高":
        count = 4
    elif level == "中":
        count = 3
    else:
        count = 2
    
    return all_plans[:count]


def get_communication_scripts(resistance_type: str, level: str) -> List[str]:
    """根据阻力类型和等级返回沟通话术"""
    if level == "无":
        return []
    
    all_scripts = COMMUNICATION_SCRIPTS.get(resistance_type, [])
    
    # 根据等级选择话术数量
    if level == "高":
        count = 3
    else:
        count = 2
    
    return all_scripts[:count]


def diagnose(input_data: Dict) -> Dict:
    """
    核心诊断函数
    输入：员工问答信息
    输出：完整诊断报告
    """
    employee = input_data.get("employee", {})
    closed_q = input_data.get("closed_questions", {})
    open_q = input_data.get("open_questions", {})

    # 评估所有阻力类型
    resistance_results = {}
    detected_types = []
    
    for res_type in ["惯性", "惰性", "情绪", "抵触"]:
        result = evaluate_resistance(res_type, closed_q, open_q)
        resistance_results[res_type] = {
            "detected": result["triggered"],
            "level": result["level"],
            "signals": result["signals"],
            "diagnosis_basis": result["matched_conditions"]
        }
        if result["triggered"]:
            detected_types.append(res_type)

    # 按等级排序
    type_order = {"高": 0, "中": 1, "低": 2}
    detected_types.sort(key=lambda x: type_order.get(resistance_results[x]["level"], 3))

    # 生成干预方案
    intervention_plans = {}
    for res_type in detected_types:
        level = resistance_results[res_type]["level"]
        intervention_plans[res_type] = get_intervention_plan(res_type, level)

    # 生成沟通话术
    communication_scripts = {}
    for res_type in detected_types:
        level = resistance_results[res_type]["level"]
        communication_scripts[res_type] = get_communication_scripts(res_type, level)

    # 构建诊断依据摘要
    diagnosis_basis = []
    for res_type in detected_types:
        result = resistance_results[res_type]
        basis_item = {
            "type": res_type,
            "level": result["level"],
            "triggers": result["signals"]
        }
        # 添加Q9/Q10的原始内容作为参考
        if open_q.get("Q9"):
            basis_item["Q9_original"] = open_q.get("Q9")
        if open_q.get("Q10"):
            basis_item["Q10_original"] = open_q.get("Q10")
        diagnosis_basis.append(basis_item)

    # 构建完整报告
    report = {
        "employee_info": {
            "position": employee.get("position", "未填写"),
            "years": employee.get("years", "未填写")
        },
        "resistance_summary": {
            "detected_types": detected_types,
            "total_count": len(detected_types),
            "priority_order": detected_types
        },
        "resistance_details": resistance_results,
        "diagnosis_basis": diagnosis_basis,
        "resistance_principles": {t: RESISTANCE_PRINCIPLES[t] for t in detected_types},
        "intervention_plans": intervention_plans,
        "communication_scripts": communication_scripts,
        "recommendations": {
            "priority": f"优先干预{'/'.join(detected_types[:2] if len(detected_types) >= 2 else detected_types)}",
            "approach": "按优先级顺序执行干预方案，1v1沟通时直接使用提供的沟通话术"
        }
    }

    return report


def generate_markdown_report(report: Dict) -> str:
    """将JSON报告转换为Markdown格式"""
    lines = []
    lines.append("# AI阻力诊断与干预报告")
    lines.append("")
    lines.append("## 一、员工基础信息")
    lines.append(f"- 岗位：{report['employee_info']['position']}")
    lines.append(f"- 入职年限：{report['employee_info']['years']}年")
    lines.append("")
    
    lines.append("## 二、核心阻力类型")
    detected = report['resistance_summary']['detected_types']
    if detected:
        for rtype in detected:
            level = report['resistance_details'][rtype]['level']
            lines.append(f"- **{rtype}**（{level}）")
    else:
        lines.append("- 无明显阻力信号")
    lines.append("")
    
    lines.append("## 三、诊断依据")
    for basis in report['diagnosis_basis']:
        lines.append(f"### {basis['type']}（{basis['level']}）")
        for signal in basis['triggers']:
            lines.append(f"- {signal}")
        if basis.get('Q9_original'):
            lines.append(f"- Q9原话：{basis['Q9_original']}")
        if basis.get('Q10_original'):
            lines.append(f"- Q10原话：{basis['Q10_original']}")
        lines.append("")
    
    lines.append("## 四、底层原理")
    for rtype, principle in report['resistance_principles'].items():
        lines.append(f"- **{rtype}**：{principle}")
    lines.append("")
    
    lines.append("## 五、精准干预方案")
    for rtype, plans in report['intervention_plans'].items():
        lines.append(f"### （{rtype}适配方案）")
        for i, plan in enumerate(plans, 1):
            lines.append(f"{i}. **{plan['title']}**：{plan['content']}")
        lines.append("")
    
    lines.append("## 六、沟通话术")
    for rtype, scripts in report['communication_scripts'].items():
        lines.append(f"### {rtype}沟通")
        for i, script in enumerate(scripts, 1):
            lines.append(f"{i}. {script}")
        lines.append("")
    
    lines.append("## 七、执行建议")
    lines.append(f"- {report['recommendations']['priority']}")
    lines.append(f"- {report['recommendations']['approach']}")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="AI Enablement 阻力诊断工具")
    parser.add_argument("--input", "-i", required=True, help="JSON格式的员工问答数据")
    parser.add_argument("--format", "-f", choices=["json", "markdown"], default="json",
                        help="输出格式：json（默认）或 markdown")
    
    args = parser.parse_args()
    
    try:
        input_data = json.loads(args.input)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "status": "error",
            "message": f"JSON解析失败: {str(e)}",
            "hint": "请确保输入是有效的JSON格式字符串"
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    
    # 执行诊断
    report = diagnose(input_data)
    
    # 输出结果
    if args.format == "markdown":
        output = generate_markdown_report(report)
    else:
        output = json.dumps(report, ensure_ascii=False, indent=2)
    
    print(output)


if __name__ == "__main__":
    main()
