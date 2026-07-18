from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
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


class LiveFrameEvent(APIModel):
    type: Literal["frame"]
    image_base64: str = Field(min_length=1, max_length=20_000_000)
    device_hint: str | None = Field(default=None, max_length=500)


class LiveUtteranceEvent(APIModel):
    type: Literal["utterance"]
    text: str = Field(min_length=1, max_length=2_000)


class LiveInterruptEvent(APIModel):
    type: Literal["interrupt"]
    turn_id: str = Field(min_length=1, max_length=100)


LiveClientEvent = Annotated[
    LiveFrameEvent | LiveUtteranceEvent | LiveInterruptEvent,
    Field(discriminator="type"),
]
live_client_event_adapter: TypeAdapter[LiveClientEvent] = TypeAdapter(
    LiveClientEvent
)


class ARAnnotation(APIModel):
    type: Literal["highlight", "arrow", "circle", "text"]
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    z: float | None = None
    width: float | None = Field(default=None, ge=0, le=1)
    height: float | None = Field(default=None, ge=0, le=1)
    label: str = Field(min_length=1, max_length=500)
    color: str | None = None


class RepairStep(APIModel):
    step: int = Field(ge=1)
    instruction: str = Field(min_length=1, max_length=2_000)
    safety_note: str = Field(min_length=1, max_length=2_000)


class BuyablePart(APIModel):
    id: str
    name: str
    estimated_price: str
    x402_ready: bool


class AnalysisResult(APIModel):
    detected_item: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)
    issues: list[str]
    ar_annotations: list[ARAnnotation]
    repair_steps: list[RepairStep]
    buyable_parts: list[BuyablePart]


class VisionObservation(APIModel):
    detected_item: str
    confidence: float
    visible_issues: list[str]
    ar_annotations: list[ARAnnotation]
