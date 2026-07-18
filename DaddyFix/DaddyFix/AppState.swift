//
//  AppState.swift
//  DaddyFix
//
//  Brian — one-shot Scan + live WS (1–2s frames) + Lucian agent.
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
        case live
        case error
    }

    let sessionManager = ARSessionManager()
    let raycastManager = RaycastManager()
    let visionService = VisionService()
    let voiceManager = VoiceManager()
    let liveSession = LiveSessionClient()

    @Published private(set) var phase: Phase = .idle
    @Published private(set) var analysis: AnalysisResult?
    @Published var selectedPartLabel: String?
    @Published var showMeshOverlay = false
    @Published var showRepairGuide = false
    @Published var showPayment = false
    @Published private(set) var statusMessage = "Point at the water heater, then Scan or Live."
    @Published private(set) var lastError: String?
    @Published var symptomText: String = "No hot water"
    @Published private(set) var backendHealthy: Bool?
    @Published var liveAutoAnalyze: Bool = true

    /// RTSP session id when using server-side sampling (optional).
    @Published private(set) var rtspSessionId: String?

    func bindSelection() {
        raycastManager.onAnnotationSelected = { [weak self] label in
            self?.selectPart(label)
        }

        liveSession.onAnalysis = { [weak self] result in
            Task { @MainActor in
                await self?.apply(result, fromLive: true)
            }
        }
        liveSession.onAudioWAV = { [weak self] data in
            Task { @MainActor in
                self?.voiceManager.stop()
                LiveAudioHolder.play(data)
            }
        }
        liveSession.onStatus = { [weak self] state in
            Task { @MainActor in
                self?.statusMessage = "Live: \(state)"
            }
        }
    }

    func checkHealth() {
        Task {
            do {
                let h = try await visionService.health()
                backendHealthy = (h.status == "ok")
            } catch {
                backendHealthy = false
            }
        }
    }

    // MARK: - One-shot

    func scan() {
        guard phase != .analyzing else { return }
        stopLive(silent: true)
        phase = .analyzing
        statusMessage = "Capturing frame…"
        lastError = nil
        voiceManager.stop()

        guard let image = sessionManager.captureFrameImage() else {
            lastError = "No AR frame yet — wait for tracking, then Scan."
            phase = .error
            statusMessage = "Waiting for camera frame"
            return
        }

        statusMessage = "Sending to Daddy agent…"
        let symptom = symptomText.trimmingCharacters(in: .whitespacesAndNewlines)

        Task {
            do {
                let result = try await visionService.analyze(
                    image: image,
                    symptom: symptom.isEmpty ? nil : symptom,
                    deviceHint: APIConfig.defaultDeviceHint
                )
                await apply(result, fromLive: false)
            } catch {
                lastError = error.localizedDescription
                phase = .error
                statusMessage = "Analyze failed — check API URL or use Local mock"
            }
        }
    }

    func applyLocalMock() {
        lastError = nil
        stopLive(silent: true)
        Task { await apply(.waterHeaterMock, fromLive: false) }
    }

    // MARK: - Live WS (phone → 1–2s frames)

    func startLive() {
        lastError = nil
        voiceManager.stop()
        liveSession.deviceHint = APIConfig.defaultDeviceHint
        liveSession.autoAnalyze = liveAutoAnalyze
        liveSession.frameInterval = 2.0

        liveSession.start(
            sessionId: "ios-\(UUID().uuidString.prefix(8))",
            capture: { [weak self] in
                self?.sessionManager.captureFrameImage()
            },
            frameInterval: 2.0,
            autoAnalyze: liveAutoAnalyze
        )
        phase = .live
        statusMessage = "Live streaming frames every 2s…"
    }

    func stopLive(silent: Bool = false) {
        liveSession.stop()
        if !silent {
            phase = analysis == nil ? .idle : .showingAR
            statusMessage = analysis == nil ? "Live stopped." : "Live stopped — pins kept."
        }
    }

    /// User question while live (or start utterance without auto-analyze).
    func askLive(_ text: String? = nil) {
        let q = (text ?? symptomText).trimmingCharacters(in: .whitespacesAndNewlines)
        guard !q.isEmpty else { return }
        if liveSession.status == .disconnected {
            liveAutoAnalyze = false
            startLive()
        }
        // Fresh keyframe then utterance
        Task {
            try? await Task.sleep(nanoseconds: 200_000_000)
            liveSession.sendUtterance(q)
            statusMessage = "Asked: \(q)"
        }
    }

    func bargeIn() {
        voiceManager.stop()
        LiveAudioHolder.stop()
        liveSession.sendInterrupt()
        statusMessage = "Interrupted"
    }

    // MARK: - RTSP (server samples cam; phone polls)

    func startRTSP(rtspUrl: String) {
        lastError = nil
        statusMessage = "Starting RTSP sampling…"
        Task {
            do {
                let started = try await visionService.startRTSP(
                    rtspUrl: rtspUrl,
                    intervalSec: 2.0,
                    deviceHint: APIConfig.defaultDeviceHint
                )
                rtspSessionId = started.sessionId
                phase = .live
                statusMessage = "RTSP session \(started.sessionId.prefix(8))… polling"
                pollRTSPLoop(sessionId: started.sessionId)
            } catch {
                lastError = error.localizedDescription
                phase = .error
                statusMessage = "RTSP start failed"
            }
        }
    }

    func stopRTSP() {
        guard let id = rtspSessionId else { return }
        Task {
            try? await visionService.stopRTSP(sessionId: id)
            rtspSessionId = nil
            phase = analysis == nil ? .idle : .showingAR
            statusMessage = "RTSP stopped"
        }
    }

    private func pollRTSPLoop(sessionId: String) {
        Task {
            var lastSeq = -1
            while rtspSessionId == sessionId {
                do {
                    let result = try await visionService.fetchRTSPLatest(sessionId: sessionId)
                    // Always re-apply; seq not on AnalysisResult from Lucian
                    await apply(result, fromLive: true)
                    _ = lastSeq
                    lastSeq += 1
                } catch {
                    // 404 until first frame — ignore briefly
                }
                try? await Task.sleep(nanoseconds: 2_000_000_000)
            }
        }
    }

    // MARK: - Shared

    func selectPart(_ label: String) {
        selectedPartLabel = label
        showRepairGuide = true
        if phase != .live { phase = .voiceGuidance }
    }

    func reset() {
        stopLive(silent: true)
        stopRTSP()
        raycastManager.clearAnnotations()
        voiceManager.stop()
        analysis = nil
        selectedPartLabel = nil
        lastError = nil
        showRepairGuide = false
        showPayment = false
        phase = .idle
        statusMessage = "Point at the water heater, then Scan or Live."
    }

    private func apply(_ result: AnalysisResult, fromLive: Bool) async {
        analysis = result
        raycastManager.placeAnnotations(result.arAnnotations)
        if !fromLive || phase != .live {
            phase = fromLive ? .live : .showingAR
        }
        statusMessage = result.detectedItem

        // One-shot: always speak. Live: speak only if not auto-spamming every 2s
        // (autoAnalyze already gets server TTS via WS audio). For one-shot use TTS API.
        if !fromLive, let first = result.repairSteps.first {
            phase = .voiceGuidance
            var line = first.instruction
            if let safety = first.safetyNote, !safety.isEmpty {
                line += " " + safety
            }
            await voiceManager.speakDaddy(line)
            if let ve = voiceManager.lastError {
                lastError = ve
            }
        }
    }

    }

import AVFoundation

/// Holds AVAudioPlayer for live WS WAV so it isn't deallocated.
@MainActor
enum LiveAudioHolder {
    static var player: AVAudioPlayer?

    static func play(_ data: Data) {
        player?.stop()
        player = try? AVAudioPlayer(data: data)
        player?.prepareToPlay()
        player?.play()
    }

    static func stop() {
        player?.stop()
        player = nil
    }
}
