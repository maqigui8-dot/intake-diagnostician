from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence


RULE_VERSION = "adult-obesity-intake-v1"


@dataclass(frozen=True)
class FieldDefinition:
    key: str
    section: Literal["differentiation", "safety"]
    group: str
    weight: int
    priority: int
    hard_required: bool
    conditional: str | None
    max_attempts: int
    question: str
    retry_question: str
    source: str


NHC_GUIDE = "国家卫生健康委《肥胖症诊疗指南（2024年版）》"
TCM_INTAKE = "十问歌与中医问诊经验"
PRESCRIPTION_SAFETY = "医生开方前安全核查"


FIELD_DEFINITIONS: Sequence[FieldDefinition] = (
    FieldDefinition("main_goal", "differentiation", "肥胖情况与主要诉求", 4, 20, False, None, 2,
                    "这次您最希望改善的体重或身体方面的困扰是什么？",
                    "为了便于医生了解重点，您更希望改善体重、腰围，还是某种身体不适？", NHC_GUIDE),
    FieldDefinition("height_weight", "differentiation", "肥胖情况与主要诉求", 5, 12, False, None, 2,
                    "您目前的身高和体重大约是多少？",
                    "大概数值也可以，您记得身高和最近一次体重吗？", NHC_GUIDE),
    FieldDefinition("waist", "differentiation", "肥胖情况与主要诉求", 2, 35, False, None, 2,
                    "您最近量过腰围吗？大约是多少厘米？",
                    "如果没有准确量过，您可以说近期腰围是明显增加、变化不大，还是不清楚？", NHC_GUIDE),
    FieldDefinition("weight_change", "differentiation", "肥胖情况与主要诉求", 4, 18, False, None, 2,
                    "您的体重大约从什么时候开始变化，最近变化快不快？",
                    "您可以回想一下近三个月，体重是增加、下降，还是基本稳定？", NHC_GUIDE),
    FieldDefinition("onset_course", "differentiation", "起病经过与相关因素", 4, 22, False, None, 2,
                    "体重或相关不适大约持续多久了？",
                    "大致按几周、几个月或几年回答就可以，您觉得持续了多久？", NHC_GUIDE),
    FieldDefinition("related_factors", "differentiation", "起病经过与相关因素", 3, 30, False, None, 2,
                    "体重变化前后，饮食、活动、睡眠或生活状态有没有明显改变？",
                    "您觉得这次变化更像和吃得多、活动少、睡眠变化有关，还是暂时说不清？", NHC_GUIDE),
    FieldDefinition("previous_weight_management", "differentiation", "起病经过与相关因素", 3, 42, False, None, 2,
                    "您以前尝试过哪些控制体重的方法，效果怎么样？",
                    "例如调整饮食、运动或使用减重产品，您尝试过其中哪一种吗？", NHC_GUIDE),
    FieldDefinition("appetite_thirst", "differentiation", "中医症状资料", 6, 24, False, None, 2,
                    "您最近的食欲、饭量和口渴情况有什么变化？",
                    "您更接近容易饿、食欲不振、口渴想喝水，还是都不明显？", TCM_INTAKE),
    FieldDefinition("cold_heat_sweat", "differentiation", "中医症状资料", 5, 26, False, None, 2,
                    "您平时更怕冷还是怕热，出汗情况和平时相比怎么样？",
                    "您更接近怕冷、怕热、容易出汗，还是这些感觉都不明显？", TCM_INTAKE),
    FieldDefinition("stool_urine", "differentiation", "中医症状资料", 5, 25, False, None, 2,
                    "最近大便和小便有没有明显变化？",
                    "比如便秘、便稀、小便偏黄或夜尿增多，您有其中一种情况吗？", TCM_INTAKE),
    FieldDefinition("sleep_emotion", "differentiation", "中医症状资料", 5, 28, False, None, 2,
                    "您最近睡眠和情绪状态怎么样？",
                    "您最近更接近入睡困难、容易醒、压力较大，还是基本正常？", TCM_INTAKE),
    FieldDefinition("fatigue_activity", "differentiation", "中医症状资料", 5, 27, False, None, 2,
                    "您平时容易疲乏、气短或活动后不舒服吗？",
                    "日常走路或上楼时，您会比以前更容易累或气短吗？", TCM_INTAKE),
    FieldDefinition("edema_heaviness", "differentiation", "中医症状资料", 5, 29, False, None, 2,
                    "您有没有身体困重、四肢沉重或浮肿的感觉？",
                    "早晨脸肿、下午腿脚肿或身体发沉，这些情况有吗？", TCM_INTAKE),
    FieldDefinition("chest_abdomen", "differentiation", "中医症状资料", 4, 31, False, None, 2,
                    "胸口或腹部有没有闷、胀、痛等不舒服？",
                    "您更接近胸闷、饭后腹胀、腹痛，还是都没有？", TCM_INTAKE),
    FieldDefinition("tongue", "differentiation", "舌象", 5, 60, False, None, 2,
                    "方便的话，您可以上传一张自然光下的舌头照片；不方便也没关系。",
                    "舌照是可选信息，您现在方便提供吗？不方便可以直接说跳过。", TCM_INTAKE),
    FieldDefinition("diet_pattern", "differentiation", "生活方式与心理因素", 2, 38, False, None, 2,
                    "您平时三餐、夜宵和甜食油腻食物的习惯大致怎样？",
                    "您更常见的是三餐规律、夜宵较多，还是甜食油腻食物较多？", NHC_GUIDE),
    FieldDefinition("exercise", "differentiation", "生活方式与心理因素", 1, 45, False, None, 2,
                    "您平时每周大约有几次运动或较多活动？",
                    "大致回答很少、每周一两次或三次以上即可，您属于哪种？", NHC_GUIDE),
    FieldDefinition("sleep_schedule", "differentiation", "生活方式与心理因素", 1, 46, False, None, 2,
                    "您平时作息规律吗，会经常熬夜吗？",
                    "最近一周，您大多数时候会在晚上十二点以后睡吗？", NHC_GUIDE),
    FieldDefinition("stress_eating", "differentiation", "生活方式与心理因素", 1, 47, False, None, 2,
                    "压力或情绪变化时，您会不会比平时吃得更多？",
                    "心情紧张或低落时，您会明显增加零食或正餐量吗？", NHC_GUIDE),
    FieldDefinition("allergies", "safety", "过敏史", 6, 2, True, None, 2,
                    "为了后续用药安全，请问您有明确的药物、食物或其他过敏吗？",
                    "过敏史很重要，您能否确认一下：有明确过敏，还是目前没有发现？", PRESCRIPTION_SAFETY),
    FieldDefinition("medications", "safety", "当前用药与保健品", 6, 3, True, None, 2,
                    "您目前正在使用哪些药物、保健品或减重产品？",
                    "请您再确认一下，近期有没有每天或经常服用的药、保健品或减重产品？没有也可以直接说没有。", PRESCRIPTION_SAFETY),
    FieldDefinition("important_history", "safety", "既往疾病与继发性肥胖线索", 7, 4, True, None, 2,
                    "您以前是否被诊断过高血压、糖尿病、甲状腺、肝肾疾病或其他长期疾病？",
                    "为了排除需要特别注意的情况，请确认是否有医生诊断过的慢性病；没有也可以直接说没有。", PRESCRIPTION_SAFETY),
    FieldDefinition("metabolic_tests", "safety", "肝肾功能、代谢风险和近期检查", 5, 10, False, None, 2,
                    "近期做过血糖、血脂、肝肾功能或甲状腺等检查吗？结果有没有异常？",
                    "如果记不清具体数值，您只要说近期是否做过，以及医生有没有提示异常即可。", PRESCRIPTION_SAFETY),
    FieldDefinition("pregnancy", "safety", "妊娠与生育相关情况", 3, 5, False, "pregnancy_applicable", 2,
                    "为了后续用药安全，请问目前是否可能怀孕、正在备孕或哺乳？",
                    "这个问题只用于用药安全，请确认目前是可能怀孕、备孕、哺乳，还是都没有？", PRESCRIPTION_SAFETY),
    FieldDefinition("red_flags", "safety", "危险信号", 3, 1, True, None, 2,
                    "最近有没有胸痛、明显呼吸困难、晕厥、意识异常或其他突然加重的不适？",
                    "为了安全再确认一次：近期是否出现胸痛、喘不过气、晕倒或意识不清？没有也请直接说没有。", PRESCRIPTION_SAFETY),
)


_FIELDS_BY_KEY = {item.key: item for item in FIELD_DEFINITIONS}


def get_field_definition(key: str) -> FieldDefinition:
    try:
        return _FIELDS_BY_KEY[key]
    except KeyError as exc:
        raise KeyError(f"未知问诊字段: {key}") from exc


def get_applicable_fields(context: dict[str, object] | None = None) -> Sequence[FieldDefinition]:
    patient_context = context or {}
    result = []
    for item in FIELD_DEFINITIONS:
        if item.conditional == "pregnancy_applicable" and patient_context.get("pregnancy_applicable") is False:
            continue
        result.append(item)
    return tuple(result)
