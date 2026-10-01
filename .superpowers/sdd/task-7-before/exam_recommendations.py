from __future__ import annotations

from typing import Any


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
    exams = [{
        "name": "肝肾功能、血脂、空腹血糖和尿酸",
        "type": "抽血",
        "department": "内分泌科或检验科",
        "reason": "用于了解肥胖相关代谢风险及后续干预前的基础安全情况。",
        "priority": "routine",
        "precautions": "通常需空腹 8 小时以上，按就诊医院要求准备。",
    }]

    metabolic_markers = ("糖尿病", "血糖", "口渴", "多尿", "家族史")
    important_history = field_states.get("important_history", {})
    if important_history.get("status") in {"confirmed", "partial"} and any(marker in evidence_text for marker in metabolic_markers):
        exams.append({
            "name": "糖化血红蛋白",
            "type": "抽血",
            "department": "内分泌科或检验科",
            "reason": "反映近 2 至 3 个月平均血糖水平，用于进一步评估糖代谢风险。",
            "priority": "priority",
            "precautions": "一般不受单次进食直接影响，具体按医院要求。",
        })

    secondary_markers = ("甲状腺", "无明显原因", "短期迅速", "突然增加")
    if any(marker in evidence_text for marker in secondary_markers):
        exams.append({
            "name": "甲状腺功能",
            "type": "抽血",
            "department": "内分泌科",
            "reason": "体重在缺少明确生活方式诱因时明显变化，可由医生判断是否排查甲状腺功能异常。",
            "priority": "priority",
            "precautions": "正在使用甲状腺相关药物时，应提前告知医生。",
        })

    if len(exams) < 3 and field_states.get("height_weight", {}).get("status") in {"confirmed", "partial"}:
        exams.append({
            "name": "上腹部超声",
            "type": "影像",
            "department": "超声科",
            "reason": "用于初步观察脂肪肝及上腹部脏器情况，是否需要由医生结合风险决定。",
            "priority": "routine",
            "precautions": "通常需空腹 8 小时以上。",
        })

    return exams[:3]
