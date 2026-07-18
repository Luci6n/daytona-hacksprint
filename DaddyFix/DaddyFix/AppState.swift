//
//  AppState.swift
//  DaddyFix
//
//  Kenji — central state machine. Owns the one ARSessionManager /
//  RaycastManager for the whole app (see LUCIAN_INTEGRATION.md) and
//  drives idle → analyzing → showingAR → voiceGuidance.
//

import Foundation
import UIKit

@MainActor
final class AppState: ObservableObject {
    enum Phase: String {
        case idle
        case analyzing
        case showingAR
        case voiceGuidance
        case error
    }

    // Brian's AR layer — created once, shared everywhere.
    let sessionManager = ARSessionManager()
    let raycastManager = RaycastManager()

    // Kenji's services.
    let visionService = VisionService()
    let voiceManager = VoiceManager()

    @Published private(set) var phase: Phase = .idle
    @Published private(set) var analysis: AnalysisResult?
    @Published var selectedPartLabel: String?
    @Published var showMeshOverlay = false
    @Published var showRepairGuide = false
    @Published var showPayment = false
    @Published private(set) var statusMessage = "Point at the water heater to begin."
    @Published private(set) var lastError: String?

    /// Real capture path: send an actual photo to the backend.
    func analyze(image: UIImage) {
        phase = .analyzing
        statusMessage = "Sending image to Daddy agent…"
        lastError = nil

        Task {
            do {
                let result = try await visionService.analyze(image: image)
                apply(result)
            } catch {
                lastError = error.localizedDescription
                phase = .error
                statusMessage = "Analyze failed — try again or use mock"
            }
        }
    }

    /// Demo-safety path: no camera capture wired into the Scan button yet,
    /// so this hits the backend's mock endpoint (real connectivity check)
    /// and falls back to the local mock if the server is unreachable
    /// (AGENTS.md: "mock where needed for demo reliability").
    func scan() {
        guard phase != .analyzing else { return }
        phase = .analyzing
        statusMessage = "Analyzing…"
        lastError = nil

        Task {
            do {
                let result = try await visionService.fetchServerMock()
                apply(result)
            } catch {
                lastError = "Server mock unreachable, used local mock: \(error.localizedDescription)"
                apply(.waterHeaterMock)
            }
        }
    }

    func selectPart(_ label: String) {
        selectedPartLabel = label
        showRepairGuide = true
    }

    func reset() {
        raycastManager.clearAnnotations()
        voiceManager.stop()
        analysis = nil
        selectedPartLabel = nil
        lastError = nil
        phase = .idle
        statusMessage = "Point at the water heater to begin."
    }

    private func apply(_ result: AnalysisResult) {
        analysis = result
        raycastManager.placeAnnotations(result.arAnnotations)
        phase = .showingAR
        statusMessage = result.detectedItem

        if let firstStep = result.repairSteps.first {
            phase = .voiceGuidance
            voiceManager.speak(firstStep.instruction)
        }
    }
}
