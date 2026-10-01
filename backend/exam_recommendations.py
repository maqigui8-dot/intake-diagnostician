from __future__ import annotations

from typing import Any

from obesity_intake_schema import RULE_VERSION


EXAM_SOURCE = "国家卫生健康委《肥胖症诊疗指南（2024年版）》"


def _exam(
    name: str,
    exam_type: str,
    department: str,
    reason: str,
    trigger: str,
    priority: str,
    precautions: str,
) -> dict[str, str]:
    return {
        "name": name,
        "type": exam_type,
        "department": department,
        "reason": reason,
        "trigger": trigger,
        "priority": priority,
        "source": EXAM_SOURCE,
        "rule_version": RULE_VERSION,
        "precautions": precautions,
    }


def build_recommended_exams(
    field_states: dict[str, dict[str, Any]],
    *,
    red_flags: list[str] | None = None,
) -> list[dict[str, str]]:
    if red_flags:
        return []

    evidence_text = " ".join(
        str(evidence)
        for field in field_states.values()
        for evidence in field.get("evidence") or []
    )
    exams = [
        _exam(
            "肝肾功能、血脂、空腹血糖和尿酸",
            "抽血",
            "内分泌科或检验科",
            "用于了解肥胖相关代谢风险及后续干预前的基础安全情况。",
            "基础常规筛查（完成基础测量的成年肥胖就诊者）",
            "routine",
            "通常需空腹 8 小时以上，按就诊医院要求准备。",
        )
    ]

    metabolic_markers = ("糖尿病", "血糖", "口渴", "多尿", "家族史")
    important_history = field_states.get("important_history", {})
    if important_history.get("status") in {"confirmed", "partial"} and any(marker in evidence_text for marker in metabolic_markers):
        exams.append(_exam(
            "糖化血红蛋白",
            "抽血",
            "内分泌科或检验科",
            "反映近 2 至 3 个月平均血糖水平，用于进一步评估糖代谢风险。",
            "既往疾病史（important_history）提示糖尿病、血糖或家族史相关证据",
            "priority",
            "一般不受单次进食直接影响，具体按医院要求。",
        ))

    secondary_markers = ("甲状腺", "无明显原因", "短期迅速", "突然增加")
    if any(marker in evidence_text for marker in secondary_markers):
        exams.append(_exam(
            "甲状腺功能",
            "抽血",
            "内分泌科",
            "体重在缺少明确生活方式诱因时明显变化，可由医生判断是否排查甲状腺功能异常。",
            "体重变化缺乏明确诱因或出现甲状腺相关证据",
            "priority",
            "正在使用甲状腺相关药物时，应提前告知医生。",
        ))

    if len(exams) < 3 and field_states.get("height_weight", {}).get("status") in {"confirmed", "partial"}:
        exams.append(_exam(
            "上腹部超声",
            "影像",
            "超声科",
            "用于初步观察脂肪肝及上腹部脏器情况，是否需要由医生结合风险决定。",
            "身高体重已确认，补充上腹部脏器影像观察",
            "routine",
            "通常需空腹 8 小时以上。",
        ))

    return exams[:3]
