from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


_ONE_DECIMAL = Decimal("0.1")
_SUPPORTED_SEXES = {"male", "female"}
_WAIST_THRESHOLDS_CM = {"male": Decimal("90"), "female": Decimal("85")}
_WAIST_HIP_RATIO_THRESHOLDS = {"male": Decimal("0.90"), "female": Decimal("0.85")}


def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    height = _as_decimal(height_cm, "身高")
    weight = _as_decimal(weight_kg, "体重")
    if height <= 0:
        raise ValueError("身高需为大于0的厘米数")
    if weight <= 0:
        raise ValueError("体重需为大于0的千克数")
    return float((weight / (height / Decimal("100")) ** 2).quantize(_ONE_DECIMAL, rounding=ROUND_HALF_UP))


def classify_adult_bmi(bmi: float) -> str:
    value = _as_decimal(bmi, "BMI")
    if value < Decimal("18.5"):
        return "体重过低"
    if value < Decimal("24"):
        return "体重正常"
    if value < Decimal("28"):
        return "超重"
    if value < Decimal("32.5"):
        return "轻度肥胖范围"
    if value < Decimal("37.5"):
        return "中度肥胖范围"
    if value < Decimal("50"):
        return "重度肥胖范围"
    return "极重度肥胖范围"


def evaluate_central_obesity(sex: str, waist_cm: float | None, hip_cm: float | None) -> dict[str, object]:
    normalized_sex = _validate_sex(sex)
    waist = _optional_positive_measurement(waist_cm, "腰围")
    hip = _optional_positive_measurement(hip_cm, "臀围")
    waist_threshold = _WAIST_THRESHOLDS_CM[normalized_sex]
    ratio_threshold = _WAIST_HIP_RATIO_THRESHOLDS[normalized_sex]
    ratio = None
    raw_ratio = None
    if waist is not None and hip is not None:
        raw_ratio = waist / hip
        ratio = raw_ratio.quantize(_ONE_DECIMAL, rounding=ROUND_HALF_UP)
    return {
        "waist_cm": float(waist) if waist is not None else None,
        "hip_cm": float(hip) if hip is not None else None,
        "waist_threshold_cm": float(waist_threshold),
        "waist_reached": waist >= waist_threshold if waist is not None else None,
        "waist_hip_ratio": float(ratio) if ratio is not None else None,
        "waist_hip_ratio_threshold": float(ratio_threshold),
        "waist_hip_ratio_reached": raw_ratio >= ratio_threshold if raw_ratio is not None else None,
    }


def validate_baseline(payload: dict[str, object]) -> dict[str, object]:
    age = _validate_age(payload.get("age"))
    sex = _validate_sex(payload.get("sex"))
    height = _bounded_measurement(payload.get("height_cm"), "身高", Decimal("100"), Decimal("250"), "厘米")
    weight = _bounded_measurement(payload.get("weight_kg"), "体重", Decimal("20"), Decimal("500"), "千克")
    measured_at = _validate_measured_at(payload.get("measured_at"))
    central_obesity = evaluate_central_obesity(sex, payload.get("waist_cm"), payload.get("hip_cm"))
    bmi = calculate_bmi(float(height), float(weight))
    result: dict[str, object] = {
        "age": age,
        "sex": sex,
        "height_cm": float(height),
        "weight_kg": float(weight),
        "waist_cm": central_obesity["waist_cm"],
        "hip_cm": central_obesity["hip_cm"],
        "measured_at": measured_at,
        "bmi": bmi,
        "bmi_grade": classify_adult_bmi(bmi),
        "central_obesity": central_obesity,
    }
    if bmi >= 28:
        result["diagnosis_copy"] = "当前BMI达到成人肥胖范围，最终结果需由医生结合测量和检查确认。"
    return result


def _validate_age(value: object) -> int:
    age = _as_decimal(value, "年龄")
    if age != age.to_integral_value():
        raise ValueError("年龄请填写整数")
    if age < 18:
        raise ValueError("仅支持18岁及以上成年人，请转入儿童青少年评估流程。")
    if age > 120:
        raise ValueError("年龄需在18至120岁之间，请核对后重新填写。")
    return int(age)


def _validate_sex(value: object) -> str:
    sex = str(value or "").strip().lower()
    if sex not in _SUPPORTED_SEXES:
        raise ValueError("生理性别仅支持男或女，请重新选择。")
    return sex


def _bounded_measurement(value: object, label: str, lower: Decimal, upper: Decimal, unit: str) -> Decimal:
    measurement = _as_decimal(value, label)
    if not lower <= measurement <= upper:
        raise ValueError(f"{label}需在{lower}至{upper}{unit}之间，请核对后重新填写。")
    return measurement.quantize(_ONE_DECIMAL, rounding=ROUND_HALF_UP)


def _optional_positive_measurement(value: object, label: str) -> Decimal | None:
    if value is None or value == "":
        return None
    measurement = _as_decimal(value, label)
    if measurement <= 0:
        raise ValueError(f"{label}需为大于0的厘米数，请核对后重新填写。")
    return measurement.quantize(_ONE_DECIMAL, rounding=ROUND_HALF_UP)


def _validate_measured_at(value: object) -> str:
    measured_at = str(value or "").strip()
    if not measured_at:
        raise ValueError("请补充最近一次测量时间，以便医生判断数据新鲜度。")
    return measured_at


def _as_decimal(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"请填写有效的{label}数值。")
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"请填写有效的{label}数值。") from None
    if not decimal_value.is_finite():
        raise ValueError(f"请填写有效的{label}数值。")
    return decimal_value
