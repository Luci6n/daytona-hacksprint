from backend.models import AnalysisResult, ARAnnotation, BuyablePart, RepairStep


def water_heater_result() -> AnalysisResult:
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
