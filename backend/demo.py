from backend.models import AnalysisResult, ARAnnotation, BuyablePart, RepairStep


def water_heater_result() -> AnalysisResult:
    """Deterministic hero fixture — only when DEMO_MODE=true or explicit demo."""
    return AnalysisResult(
        detected_item="Rinnai Tankless Water Heater",
        confidence=0.94,
        issues=["ELCB may have tripped", "No hot water reported"],
        ar_annotations=[
            ARAnnotation(
                type="highlight",
                x=0.42,
                y=0.58,
                width=0.18,
                height=0.12,
                label="ELCB",
                color="#22C55E",
            ),
            ARAnnotation(
                type="arrow",
                x=0.42,
                y=0.48,
                label="ELCB",
                color="#38BDF8",
            ),
            ARAnnotation(
                type="text",
                x=0.42,
                y=0.68,
                label="Earth Leakage Circuit Breaker",
                color="#F8FAFC",
            ),
        ],
        repair_steps=[
            RepairStep(
                step=1,
                instruction=(
                    "First safety step — locate the Earth Leakage Circuit Breaker. "
                    "I've highlighted it on the unit."
                ),
                safety_note=(
                    "If you smell gas or see scorch marks, stop and call a "
                    "licensed professional."
                ),
            ),
            RepairStep(
                step=2,
                instruction=(
                    "Check whether the ELCB switch is in the ON position. If it is "
                    "OFF or midway, carefully reset it once."
                ),
                safety_note=(
                    "Do not force the breaker. Call a licensed electrician if it "
                    "will not stay on."
                ),
            ),
        ],
        buyable_parts=[
            BuyablePart(
                id="elcb-rinnai-compat",
                name="Compatible ELCB / Leakage Breaker",
                estimated_price="$48–$72",
                x402_ready=True,
            )
        ],
    )


def generic_unavailable_result(
    *,
    device_hint: str | None,
    symptom: str | None,
    reason: str,
) -> AnalysisResult:
    """
    When live providers fail: do NOT invent a water heater.
    Return an honest low-confidence result so AR does not show wrong ELCB pins.
    """
    label = (device_hint or "device in view").strip() or "device in view"
    issue = (symptom or "Could not complete live visual analysis").strip()
    return AnalysisResult(
        detected_item=label[:500],
        confidence=0.15,
        issues=[
            issue,
            f"Live analysis incomplete: {reason}",
            "Point the camera at the problem and try Scan again.",
        ],
        ar_annotations=[
            # Center-screen soft target — not a fake ELCB.
            ARAnnotation(
                type="circle",
                x=0.5,
                y=0.5,
                width=0.2,
                height=0.2,
                label="Recheck",
                color="#F59E0B",
            ),
            ARAnnotation(
                type="text",
                x=0.5,
                y=0.62,
                label="Analysis incomplete",
                color="#F8FAFC",
            ),
        ],
        repair_steps=[
            RepairStep(
                step=1,
                instruction=(
                    "I could not fully see or reason about this scene with live "
                    "providers. Hold the phone steady, fill the frame with the "
                    f"{label}, and Scan again."
                ),
                safety_note=(
                    "If anything looks unsafe (sparks, smoke, battery swelling, "
                    "gas smell), stop and call a licensed professional."
                ),
            )
        ],
        buyable_parts=[],
    )
