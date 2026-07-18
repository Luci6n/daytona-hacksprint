//
//  AnalysisResult.swift
//  DaddyFix
//
//  Shared data contract (Lucian Python JSON; Brian Swift + AR consume arAnnotations).
//  Agree changes with the team before modifying field names.
//

import Foundation

struct AnalysisResult: Codable, Sendable {
    let detectedItem: String
    let confidence: Double
    let issues: [String]
    let arAnnotations: [ARAnnotation]
    let repairSteps: [RepairStep]
    let buyableParts: [BuyablePart]
    /// Live / RTSP stream metadata (optional — one-shot may omit)
    let sessionId: String?
    let seq: Int?
    /// "snapshot" | "live" | "rtsp"
    let eventType: String?

    init(
        detectedItem: String,
        confidence: Double,
        issues: [String],
        arAnnotations: [ARAnnotation],
        repairSteps: [RepairStep],
        buyableParts: [BuyablePart],
        sessionId: String? = nil,
        seq: Int? = nil,
        eventType: String? = nil
    ) {
        self.detectedItem = detectedItem
        self.confidence = confidence
        self.issues = issues
        self.arAnnotations = arAnnotations
        self.repairSteps = repairSteps
        self.buyableParts = buyableParts
        self.sessionId = sessionId
        self.seq = seq
        self.eventType = eventType
    }
}

struct ARAnnotation: Codable, Identifiable, Sendable {
    var id: String { "\(type)-\(label)-\(x)-\(y)" }

    /// "highlight", "arrow", "circle", "text"
    let type: String
    /// Normalized image coordinates 0...1 (origin top-left of captured frame).
    let x: Double
    let y: Double
    /// Optional depth / world Z hint from backend (meters). Prefer LiDAR raycast when nil.
    let z: Double?
    let width: Double?
    let height: Double?
    let label: String
    /// Hex color e.g. "#22C55E" or named "green"
    let color: String?
}

struct RepairStep: Codable, Identifiable, Sendable {
    var id: Int { step }
    let step: Int
    let instruction: String
    let safetyNote: String?
}

struct BuyablePart: Codable, Identifiable, Sendable {
    let id: String
    let name: String
    let estimatedPrice: String
    let x402Ready: Bool
}

// MARK: - Demo fixture (Brian: local AR testing without backend)

extension AnalysisResult {
    /// Water heater hero demo — ELCB highlight for LiDAR annotation placement.
    static let waterHeaterMock = AnalysisResult(
        detectedItem: "Rinnai Tankless Water Heater",
        confidence: 0.94,
        issues: [
            "ELCB may have tripped",
            "No hot water reported"
        ],
        arAnnotations: [
            ARAnnotation(
                type: "highlight",
                x: 0.42,
                y: 0.58,
                z: nil,
                width: 0.18,
                height: 0.12,
                label: "ELCB",
                color: "#22C55E"
            ),
            ARAnnotation(
                type: "arrow",
                x: 0.42,
                y: 0.48,
                z: nil,
                width: nil,
                height: nil,
                label: "ELCB",
                color: "#38BDF8"
            ),
            ARAnnotation(
                type: "text",
                x: 0.42,
                y: 0.68,
                z: nil,
                width: nil,
                height: nil,
                label: "Earth Leakage Circuit Breaker",
                color: "#F8FAFC"
            )
        ],
        repairSteps: [
            RepairStep(
                step: 1,
                instruction: "First safety step — locate the Earth Leakage Circuit Breaker. I've highlighted it on the unit.",
                safetyNote: "If you smell gas or see scorch marks, stop and call a licensed professional."
            ),
            RepairStep(
                step: 2,
                instruction: "Check whether the ELCB switch is in the ON position. If it is OFF or midway, carefully reset it once.",
                safetyNote: "Do not force the breaker. Call a licensed electrician if it will not stay on."
            )
        ],
        buyableParts: [
            BuyablePart(
                id: "elcb-rinnai-compat",
                name: "Compatible ELCB / Leakage Breaker",
                estimatedPrice: "$48–$72",
                x402Ready: true
            )
        ]
    )
}
