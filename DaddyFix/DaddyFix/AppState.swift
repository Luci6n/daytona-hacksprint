//
//  AppState.swift
//  DaddyFix
//
//  Integration hub — Brian owns until Kenji's Xcode is healthy.
//

import Foundation
import SwiftUI
import UIKit

@MainActor
@Observable
final class AppState {
    enum Phase: String {
        case idle
        case analyzing
        case showingAR
        case voiceGuidance
        case error
    }

    // Brian AR
    let sessionManager = ARSessionManager()
    let raycastManager = RaycastManager()

    // Kenji/Brian services
    let vision = VisionService()

    var phase: Phase = .idle
    var analysis: AnalysisResult?
    var selectedPartLabel: String?
    var showMeshOverlay = false
    var showPayment = false
    var statusMessage = "Point at the water heater, then Analyze"
    var lastError: String?

    func wireAnnotationSelection() {
        raycastManager.onAnnotationSelected = { [weak self] label in
            Task { @MainActor in
                self?.selectedPartLabel = label
                self?.phase = .voiceGuidance
                self?.statusMessage = "Selected \(label) — guide / buy UI next"
            }
        }
    }

    /// Demo path: mock or live Kimi via backend.
    func analyzeMockAndPlace() async {
        phase = .analyzing
        statusMessage = "Analyzing…"
        lastError = nil
        do {
            let result = try await vision.fetchServerMock()
            apply(result)
        } catch {
            // Offline / backend down → local mock still demos AR
            let result = vision.mockAnalyze()
            apply(result)
            lastError = "Server mock failed, used local mock: \(error.localizedDescription)"
            statusMessage = "Local mock placed (server unreachable)"
        }
    }

    func analyze(image: UIImage) async {
        phase = .analyzing
        statusMessage = "Sending image to Daddy agent (Kimi)…"
        lastError = nil
        do {
            let result = try await vision.analyze(image: image)
            apply(result)
        } catch {
            lastError = error.localizedDescription
            phase = .error
            statusMessage = "Analyze failed — try mock"
        }
    }

    func apply(_ result: AnalysisResult) {
        analysis = result
        raycastManager.placeAnnotations(result.arAnnotations)
        phase = .showingAR
        statusMessage = "\(result.detectedItem) — annotations placed"
        if result.repairSteps.first != nil {
            phase = .voiceGuidance
            // VoiceManager (Kenji/Brian) hooks here later
        }
    }

    func clear() {
        raycastManager.clearAnnotations()
        analysis = nil
        selectedPartLabel = nil
        phase = .idle
        statusMessage = "Cleared"
    }
}
