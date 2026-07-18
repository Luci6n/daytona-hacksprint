from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class AnalyzeRequest(APIModel):
    symptom: str | None = None
    device_hint: str | None = None
    image_base64: str | None = None


class SpeechRequest(APIModel):
    text: str = Field(min_length=1, max_length=2_000)


class ARAnnotation(APIModel):
    type: str
    x: float
    y: float
    z: float | None = None
    width: float | None = None
    height: float | None = None
    label: str
    color: str | None = None


class RepairStep(APIModel):
    step: int
    instruction: str
    safety_note: str | None = None


class BuyablePart(APIModel):
    id: str
    name: str
    estimated_price: str
    x402_ready: bool


class AnalysisResult(APIModel):
    detected_item: str
    confidence: float
    issues: list[str]
    ar_annotations: list[ARAnnotation]
    repair_steps: list[RepairStep]
    buyable_parts: list[BuyablePart]


class VisionObservation(APIModel):
    detected_item: str
    confidence: float
    visible_issues: list[str]
    ar_annotations: list[ARAnnotation]
