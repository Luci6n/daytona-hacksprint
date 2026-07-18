//
//  VoiceManager.swift
//  DaddyFix
//
//  Brian — play Lucian Nosana TTS WAV; fall back to AVSpeech if TTS fails.
//

import AVFoundation
import Foundation

@MainActor
final class VoiceManager: NSObject, ObservableObject {
    private let synthesizer = AVSpeechSynthesizer()
    private var audioPlayer: AVAudioPlayer?

    @Published private(set) var isSpeaking = false
    @Published private(set) var lastError: String?

    private let baseURL: URL
    private var sessionReady = false

    init(baseURL: URL = APIConfig.baseURL) {
        self.baseURL = baseURL
        super.init()
        synthesizer.delegate = self
        // Category only here — do NOT setActive on main in init (UI hitch warning).
        try? AVAudioSession.sharedInstance().setCategory(
            .playback,
            mode: .spokenAudio,
            options: [.duckOthers]
        )
    }

    /// Prefer cloud Daddy WAV; on failure use system speech (explicit degraded mode).
    func speakDaddy(_ text: String) async {
        stop()
        lastError = nil
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }

        await prepareAudioSession()

        if APIConfig.forceLocalMock {
            speakLocal(text)
            return
        }

        do {
            let wav = try await synthesizeWAV(text: text)
            try playWAV(wav)
        } catch {
            lastError = "TTS unavailable — using on-device voice. (\(error.localizedDescription))"
            speakLocal(text)
        }
    }

    func speakLocal(_ text: String) {
        stopPlayerOnly()
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate * 0.9
        utterance.pitchMultiplier = 0.92
        synthesizer.speak(utterance)
        isSpeaking = true
    }

    /// Barge-in: stop everything immediately (live mode).
    func stop() {
        synthesizer.stopSpeaking(at: .immediate)
        stopPlayerOnly()
        isSpeaking = false
    }

    // MARK: - Audio session (avoid main-thread setActive hitch)

    private func prepareAudioSession() async {
        if sessionReady { return }
        // Activate off the cooperative main path via async continuation + global queue.
        await withCheckedContinuation { (cont: CheckedContinuation<Void, Never>) in
            DispatchQueue.global(qos: .userInitiated).async {
                let session = AVAudioSession.sharedInstance()
                do {
                    try session.setCategory(
                        .playback,
                        mode: .spokenAudio,
                        options: [.duckOthers]
                    )
                    try session.setActive(true)
                } catch {
                    // Non-fatal — speech may still work
                }
                cont.resume()
            }
        }
        sessionReady = true
    }

    // MARK: - Network TTS

    private func synthesizeWAV(text: String) async throws -> Data {
        let url = baseURL.appendingPathComponent("speech/synthesize")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = APIConfig.speechTimeout

        struct Body: Encodable { let text: String }
        request.httpBody = try JSONEncoder().encode(Body(text: text))

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }
        guard (200 ... 299).contains(http.statusCode) else {
            let detail = String(data: data, encoding: .utf8) ?? ""
            throw NSError(
                domain: "VoiceManager",
                code: http.statusCode,
                userInfo: [NSLocalizedDescriptionKey: detail]
            )
        }
        guard !data.isEmpty else {
            throw NSError(
                domain: "VoiceManager",
                code: -1,
                userInfo: [NSLocalizedDescriptionKey: "Empty WAV body"]
            )
        }
        return data
    }

    private func playWAV(_ data: Data) throws {
        stopPlayerOnly()
        let player = try AVAudioPlayer(data: data)
        player.delegate = self
        player.prepareToPlay()
        audioPlayer = player
        isSpeaking = player.play()
    }

    private func stopPlayerOnly() {
        audioPlayer?.stop()
        audioPlayer = nil
    }
}

extension VoiceManager: AVSpeechSynthesizerDelegate {
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didStart utterance: AVSpeechUtterance) {
        Task { @MainActor in self.isSpeaking = true }
    }

    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        Task { @MainActor in self.isSpeaking = false }
    }

    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) {
        Task { @MainActor in self.isSpeaking = false }
    }
}

extension VoiceManager: AVAudioPlayerDelegate {
    nonisolated func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        Task { @MainActor in self.isSpeaking = false }
    }
}
