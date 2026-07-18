//
//  LiveSessionClient.swift
//  DaddyFix
//
//  Brian — Lucian WS /live/{sessionId}: frames every 1–2s + utterance + barge-in.
//  Contract: docs/backend-api.md
//

import Foundation
import UIKit

/// Server → client JSON envelopes (subset we care about).
private struct LiveEnvelope: Decodable {
    let type: String
    let sessionId: String?
    let turnId: String?
    let state: String?
    let contentType: String?
    let byteLength: Int?
    let code: String?
    let detail: String?
    let data: AnalysisResult?
}

@MainActor
final class LiveSessionClient: NSObject, ObservableObject {
    enum Status: String {
        case disconnected
        case connecting
        case ready
        case streaming
        case error
    }

    @Published private(set) var status: Status = .disconnected
    @Published private(set) var lastError: String?
    @Published private(set) var sessionId: String = ""
    @Published private(set) var lastAnalysis: AnalysisResult?
    @Published private(set) var framesSent: Int = 0
    @Published private(set) var currentTurnId: String?

    /// Seconds between JPEG frame uploads (1–2s target).
    var frameInterval: TimeInterval = 2.0

    /// When true, every frame is followed by an auto-utterance so the agent
    /// re-analyzes without the user speaking (continuous “what’s happening”).
    var autoAnalyze: Bool = true

    var autoAnalyzePrompt: String =
        "Look at this camera frame. Name the real device and the real problem "
        + "(e.g. wireless mouse with battery cover open / no batteries). "
        + "Highlight the empty battery compartment or broken part with arAnnotations. "
        + "Do NOT invent a water heater or ELCB."

    var deviceHint: String = APIConfig.defaultDeviceHint ?? ""

    /// Called when a new AnalysisResult arrives from the live agent.
    var onAnalysis: ((AnalysisResult) -> Void)?
    /// Binary WAV after `audio` metadata (same turn).
    var onAudioWAV: ((Data) -> Void)?
    var onStatus: ((String) -> Void)?

    private var webSocket: URLSessionWebSocketTask?
    private var session: URLSession!
    private var frameTimer: Timer?
    private var capture: (() -> UIImage?)?
    private var expectingAudioBytes: Int?
    private var pendingAudioTurnId: String?
    private var isSendingFrame = false

    override init() {
        super.init()
        session = URLSession(configuration: .default, delegate: nil, delegateQueue: nil)
    }

    // MARK: - Public control

    func start(
        sessionId: String = UUID().uuidString,
        capture: @escaping () -> UIImage?,
        frameInterval: TimeInterval = 2.0,
        autoAnalyze: Bool = true
    ) {
        stop()
        self.sessionId = sessionId
        self.capture = capture
        self.frameInterval = max(1.0, min(frameInterval, 5.0))
        self.autoAnalyze = autoAnalyze
        lastError = nil
        framesSent = 0
        status = .connecting

        let base = APIConfig.webSocketBaseURL
        // Ensure path: /live/{sessionId}
        let liveURL = base.appendingPathComponent("live").appendingPathComponent(sessionId)
        let task = session.webSocketTask(with: liveURL)
        webSocket = task
        task.resume()
        receiveLoop()
        // Server sends `ready` first; we still start frame timer after a short delay
        // so early frames aren't dropped before accept.
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { [weak self] in
            self?.beginFrameTimer()
            if self?.status == .connecting {
                self?.status = .streaming
            }
        }
    }

    func stop() {
        frameTimer?.invalidate()
        frameTimer = nil
        capture = nil
        expectingAudioBytes = nil
        webSocket?.cancel(with: .goingAway, reason: nil)
        webSocket = nil
        status = .disconnected
        currentTurnId = nil
    }

    /// User question / final speech transcript.
    func sendUtterance(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        sendJSON(["type": "utterance", "text": trimmed])
    }

    /// Barge-in: stop local audio first (caller), then notify server.
    func sendInterrupt() {
        guard let turnId = currentTurnId else { return }
        sendJSON(["type": "interrupt", "turnId": turnId])
    }

    // MARK: - Frame loop

    private func beginFrameTimer() {
        frameTimer?.invalidate()
        let timer = Timer.scheduledTimer(withTimeInterval: frameInterval, repeats: true) { [weak self] _ in
            Task { @MainActor in
                await self?.sendOneFrame()
            }
        }
        RunLoop.main.add(timer, forMode: .common)
        frameTimer = timer
        // Immediate first frame
        Task { await sendOneFrame() }
    }

    private func sendOneFrame() async {
        guard !isSendingFrame, webSocket != nil else { return }
        guard let image = capture?() else { return }
        isSendingFrame = true
        defer { isSendingFrame = false }

        let resized = image.liveResized(maxEdge: 1280)
        guard let jpeg = resized.jpegData(compressionQuality: 0.55) else { return }
        let dataURL = "data:image/jpeg;base64," + jpeg.base64EncodedString()

        sendJSON([
            "type": "frame",
            "imageBase64": dataURL,
            "deviceHint": deviceHint,
        ])
        framesSent += 1
        status = .streaming

        // Continuous analysis: re-run agent on latest frame without waiting for speech.
        if autoAnalyze {
            sendJSON([
                "type": "utterance",
                "text": autoAnalyzePrompt,
            ])
        }
    }

    // MARK: - WebSocket IO

    private func sendJSON(_ object: [String: Any]) {
        guard let webSocket,
              let data = try? JSONSerialization.data(withJSONObject: object),
              let text = String(data: data, encoding: .utf8)
        else { return }
        webSocket.send(.string(text)) { [weak self] error in
            if let error {
                Task { @MainActor in
                    self?.lastError = error.localizedDescription
                    self?.status = .error
                }
            }
        }
    }

    private func receiveLoop() {
        webSocket?.receive { [weak self] result in
            guard let self else { return }
            switch result {
            case .failure(let error):
                Task { @MainActor in
                    self.lastError = error.localizedDescription
                    self.status = .error
                    self.frameTimer?.invalidate()
                }
            case .success(let message):
                Task { @MainActor in
                    self.handle(message)
                    if self.webSocket != nil {
                        self.receiveLoop()
                    }
                }
            }
        }
    }

    private func handle(_ message: URLSessionWebSocketTask.Message) {
        switch message {
        case .string(let text):
            handleJSONText(text)
        case .data(let data):
            // Binary WAV after audio metadata
            if let expected = expectingAudioBytes {
                if data.count >= expected || !data.isEmpty {
                    onAudioWAV?(data)
                }
                expectingAudioBytes = nil
                pendingAudioTurnId = nil
            }
        @unknown default:
            break
        }
    }

    private func handleJSONText(_ text: String) {
        guard let data = text.data(using: .utf8) else { return }
        do {
            let env = try JSONDecoder().decode(LiveEnvelope.self, from: data)
            switch env.type {
            case "ready":
                status = .ready
                onStatus?("Live ready")
            case "frameAccepted":
                break
            case "status":
                if let turn = env.turnId { currentTurnId = turn }
                if let state = env.state { onStatus?(state) }
            case "analysis":
                if let turn = env.turnId { currentTurnId = turn }
                if let result = env.data {
                    lastAnalysis = result
                    onAnalysis?(result)
                }
            case "audio":
                if let turn = env.turnId { currentTurnId = turn }
                expectingAudioBytes = env.byteLength
                pendingAudioTurnId = env.turnId
            case "interrupted":
                onStatus?("interrupted")
            case "error":
                lastError = env.detail ?? env.code ?? "live error"
                status = .error
                onStatus?(lastError ?? "error")
            default:
                break
            }
        } catch {
            // Non-critical parse noise
            lastError = "Live parse: \(error.localizedDescription)"
        }
    }
}

private extension UIImage {
    func liveResized(maxEdge: CGFloat) -> UIImage {
        let longest = max(size.width, size.height)
        guard longest > maxEdge, longest > 0 else { return self }
        let scale = maxEdge / longest
        let newSize = CGSize(width: size.width * scale, height: size.height * scale)
        let renderer = UIGraphicsImageRenderer(size: newSize)
        return renderer.image { _ in draw(in: CGRect(origin: .zero, size: newSize)) }
    }
}
