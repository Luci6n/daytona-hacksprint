"""Vision layer: mock water-heater result OR Kimi (Moonshot) multimodal analyze."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from openai import OpenAI

from models import (
    ARAnnotation,
    AnalysisResult,
    BuyablePart,
    RepairStep,
)

DADDY_VISION_PROMPT = """You are DaddyFix — a calm, safety-first home repair assistant ("Daddy").

Analyze the photo of a home appliance/fixture (hero case: Rinnai tankless water heater).

Return ONLY valid JSON (no markdown fences) matching this schema exactly:
{
  "detectedItem": string,
  "confidence": number 0-1,
  "issues": string[],
  "arAnnotations": [
    {
      "type": "highlight" | "arrow" | "circle" | "text",
      "x": number 0-1,
      "y": number 0-1,
      "z": null,
      "width": number | null,
      "height": number | null,
      "label": string,
      "color": string | null
    }
  ],
  "repairSteps": [
    { "step": number, "instruction": string, "safetyNote": string | null }
  ],
  "buyableParts": [
    { "id": string, "name": string, "estimatedPrice": string, "x402Ready": boolean }
  ]
}

Rules:
- Coordinates x,y are NORMALIZED 0-1 with origin at TOP-LEFT of the image.
- For Rinnai / tankless water heaters, always include a highlight + arrow on the ELCB
  (Earth Leakage Circuit Breaker / leakage breaker / safety switch) if visible; if not
  sure, place a best-effort ELCB annotation on the electrical panel area.
- Always include strong safety language and "call a licensed professional if unsure".
- Prefer soft greens/teals for colors: "#22C55E", "#38BDF8".
- Keep 2-4 repair steps max. Be concise and trustworthy.
- If the image is not a repair scene, still return valid JSON with low confidence.
"""


def water_heater_mock() -> AnalysisResult:
    """Perfect hero-demo payload — same as iOS AnalysisResult.waterHeaterMock."""
    return AnalysisResult(
        detectedItem="Rinnai Tankless Water Heater",
        confidence=0.94,
        issues=["ELCB may have tripped", "No hot water reported"],
        arAnnotations=[
            ARAnnotation(
                type="highlight",
                x=0.42,
                y=0.58,
                z=None,
                width=0.18,
                height=0.12,
                label="ELCB",
                color="#22C55E",
            ),
            ARAnnotation(
                type="arrow",
                x=0.42,
                y=0.48,
                z=None,
                width=None,
                height=None,
                label="ELCB",
                color="#38BDF8",
            ),
            ARAnnotation(
                type="text",
                x=0.42,
                y=0.68,
                z=None,
                width=None,
                height=None,
                label="Earth Leakage Circuit Breaker",
                color="#F8FAFC",
            ),
        ],
        repairSteps=[
            RepairStep(
                step=1,
                instruction=(
                    "First safety step — locate the Earth Leakage Circuit Breaker. "
                    "I've highlighted it on the unit."
                ),
                safetyNote=(
                    "If you smell gas or see scorch marks, stop and call a licensed professional."
                ),
            ),
            RepairStep(
                step=2,
                instruction=(
                    "Check whether the ELCB switch is in the ON position. "
                    "If it is OFF or midway, carefully reset it once."
                ),
                safetyNote=(
                    "Do not force the breaker. Call a licensed electrician if it will not stay on."
                ),
            ),
        ],
        buyableParts=[
            BuyablePart(
                id="elcb-rinnai-compat",
                name="Compatible ELCB / Leakage Breaker",
                estimatedPrice="$48–$72",
                x402Ready=True,
            )
        ],
    )


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def analyze_with_kimi(image_base64: str, mime_type: str = "image/jpeg", hint: str | None = None) -> AnalysisResult:
    """Call Moonshot/Kimi OpenAI-compatible vision chat completions."""
    api_key = os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")
    if not api_key:
        raise RuntimeError("MOONSHOT_API_KEY not set")

    base_url = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1")
    model = os.getenv("KIMI_MODEL", "kimi-k2.7-code")

    client = OpenAI(api_key=api_key, base_url=base_url)

    # Some gateways use moonshotai/kimi-... ; native Moonshot often uses kimi-...
    # Allow either via KIMI_MODEL env.
    data_url = f"data:{mime_type};base64,{image_base64}"
    user_text = DADDY_VISION_PROMPT
    if hint:
        user_text += f"\n\nUser hint: {hint}"

    completion = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": "You output only compact valid JSON for DaddyFix AnalysisResult.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": user_text},
                ],
            },
        ],
    )

    raw = completion.choices[0].message.content or ""
    data = _extract_json(raw)
    return AnalysisResult.model_validate(data)


def analyze_image(
    image_base64: str | None,
    mime_type: str = "image/jpeg",
    hint: str | None = None,
    force_mock: bool = False,
) -> AnalysisResult:
    mode = (os.getenv("VISION_MODE") or "mock").lower()
    if force_mock or mode == "mock" or not image_base64:
        return water_heater_mock()

    try:
        return analyze_with_kimi(image_base64, mime_type=mime_type, hint=hint)
    except Exception as exc:  # noqa: BLE001 — demo reliability: fall back to mock
        print(f"[vision] Kimi failed, using mock: {exc}")
        result = water_heater_mock()
        # Tag so demo still works but logs show fallback
        result = result.model_copy(
            update={
                "issues": list(result.issues)
                + [f"(vision fallback mock — model error: {type(exc).__name__})"]
            }
        )
        return result
