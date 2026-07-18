//
//  VisionService.swift
//  DaddyFix
//
//  Thin HTTP client → Daytona Daddy Agent.
//  One-shot /analyze  +  live phone events  +  RTSP session poll.
//

import Foundation
import UIKit

enum VisionServiceError: LocalizedError {
    case invalidURL
    case badStatus(Int, String)
    case decodeFailed
    case emptyImage

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid API base URL"
        case .badStatus(let code, let body): return "API \(code): \(body)"
        case .decodeFailed: return "Could not decode AnalysisResult"
        case .emptyImage: return "Empty image data"
        }
    }
}

struct StreamStartResponse: Codable, Sendable {
    let ok: Bool
    let sessionId: String
    let source: String?
    let intervalSec: Double?
    let pollUrl: String?
    let eventUrl: String?
    let note: String?
}

/// Client for backend FastAPI (Daytona). Kimi / RTSP / Oxylabs run server-side.
actor VisionService {
    var baseURL: URL
    var forceMock: Bool

    init(baseURL: URL = APIConfig.baseURL, forceMock: Bool = APIConfig.forceMock) {
        self.baseURL = baseURL
        self.forceMock = forceMock
    }

    func mockAnalyze() -> AnalysisResult {
        AnalysisResult.waterHeaterMock
    }

    // MARK: - One-shot

    func fetchServerMock() async throws -> AnalysisResult {
        if forceMock { return mockAnalyze() }
        let url = baseURL.appendingPathComponent("analyze/mock")
        let (data, response) = try await URLSession.shared.data(from: url)
        try Self.validate(response: response, data: data)
        return try Self.decode(data)
    }

    func analyze(
        image: UIImage,
        hint: String? = "Rinnai water heater",
        compression: CGFloat = 0.72
    ) async throws -> AnalysisResult {
        if forceMock { return mockAnalyze() }
        guard let jpeg = image.jpegData(compressionQuality: compression) else {
            throw VisionServiceError.emptyImage
        }
        return try await analyze(imageData: jpeg, mimeType: "image/jpeg", hint: hint)
    }

    func analyze(
        imageData: Data,
        mimeType: String = "image/jpeg",
        hint: String? = nil
    ) async throws -> AnalysisResult {
        if forceMock { return mockAnalyze() }

        let url = baseURL.appendingPathComponent("analyze")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 90

        struct Payload: Encodable {
            let imageBase64: String
            let mimeType: String
            let hint: String?
        }

        request.httpBody = try JSONEncoder().encode(
            Payload(
                imageBase64: imageData.base64EncodedString(),
                mimeType: mimeType,
                hint: hint
            )
        )

        let (data, response) = try await URLSession.shared.data(for: request)
        try Self.validate(response: response, data: data)
        return try Self.decode(data)
    }

    // MARK: - Live: phone frame events (Brian capture → cloud agent)

    func startPhoneStream(hint: String? = "Watch for leaks and motion", sessionId: String? = nil) async throws -> StreamStartResponse {
        if forceMock {
            return StreamStartResponse(
                ok: true,
                sessionId: sessionId ?? UUID().uuidString,
                source: "phone",
                intervalSec: nil,
                pollUrl: nil,
                eventUrl: "/stream/phone/event",
                note: "forceMock"
            )
        }
        let url = baseURL.appendingPathComponent("stream/phone/start")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        struct Body: Encodable {
            let hint: String?
            let sessionId: String?
        }
        request.httpBody = try JSONEncoder().encode(Body(hint: hint, sessionId: sessionId))
        let (data, response) = try await URLSession.shared.data(for: request)
        try Self.validate(response: response, data: data)
        return try JSONDecoder().decode(StreamStartResponse.self, from: data)
    }

    func sendPhoneEvent(
        sessionId: String,
        image: UIImage,
        seq: Int,
        hint: String? = nil,
        compression: CGFloat = 0.55
    ) async throws -> AnalysisResult {
        if forceMock { return mockAnalyze() }
        guard let jpeg = image.jpegData(compressionQuality: compression) else {
            throw VisionServiceError.emptyImage
        }
        return try await sendPhoneEvent(
            sessionId: sessionId,
            imageData: jpeg,
            seq: seq,
            mimeType: "image/jpeg",
            hint: hint
        )
    }

    func sendPhoneEvent(
        sessionId: String,
        imageData: Data,
        seq: Int,
        mimeType: String = "image/jpeg",
        hint: String? = nil
    ) async throws -> AnalysisResult {
        if forceMock { return mockAnalyze() }

        let url = baseURL.appendingPathComponent("stream/phone/event")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 90

        struct Payload: Encodable {
            let sessionId: String
            let imageBase64: String
            let mimeType: String
            let seq: Int
            let hint: String?
        }
        request.httpBody = try JSONEncoder().encode(
            Payload(
                sessionId: sessionId,
                imageBase64: imageData.base64EncodedString(),
                mimeType: mimeType,
                seq: seq,
                hint: hint
            )
        )
        let (data, response) = try await URLSession.shared.data(for: request)
        try Self.validate(response: response, data: data)
        return try Self.decode(data)
    }

    // MARK: - Live: RTSP session (agent pulls IP camera; phone polls results)

    /// Tell Daytona to sample an RTSP URL continuously. Returns sessionId to poll.
    func startRTSPStream(
        rtspUrl: String,
        hint: String? = "Detect leaks, drips, flowing water over time",
        intervalSec: Double = 2.0,
        sessionId: String? = nil
    ) async throws -> StreamStartResponse {
        if forceMock {
            return StreamStartResponse(
                ok: true,
                sessionId: sessionId ?? UUID().uuidString,
                source: "rtsp",
                intervalSec: intervalSec,
                pollUrl: nil,
                eventUrl: nil,
                note: "forceMock — no real RTSP"
            )
        }
        let url = baseURL.appendingPathComponent("stream/rtsp/start")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        struct Body: Encodable {
            let rtspUrl: String
            let hint: String?
            let intervalSec: Double
            let sessionId: String?
        }
        request.httpBody = try JSONEncoder().encode(
            Body(rtspUrl: rtspUrl, hint: hint, intervalSec: intervalSec, sessionId: sessionId)
        )
        let (data, response) = try await URLSession.shared.data(for: request)
        try Self.validate(response: response, data: data)
        return try JSONDecoder().decode(StreamStartResponse.self, from: data)
    }

    func fetchLatest(sessionId: String) async throws -> AnalysisResult {
        if forceMock { return mockAnalyze() }
        let url = baseURL
            .appendingPathComponent("stream")
            .appendingPathComponent(sessionId)
            .appendingPathComponent("latest")
        let (data, response) = try await URLSession.shared.data(from: url)
        try Self.validate(response: response, data: data)
        return try Self.decode(data)
    }

    func stopStream(sessionId: String) async throws {
        if forceMock { return }
        let url = baseURL
            .appendingPathComponent("stream")
            .appendingPathComponent(sessionId)
            .appendingPathComponent("stop")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        let (data, response) = try await URLSession.shared.data(for: request)
        try Self.validate(response: response, data: data)
    }

    // MARK: - Helpers

    private static func validate(response: URLResponse, data: Data) throws {
        guard let http = response as? HTTPURLResponse else { return }
        guard (200 ... 299).contains(http.statusCode) else {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw VisionServiceError.badStatus(http.statusCode, body)
        }
    }

    private static func decode(_ data: Data) throws -> AnalysisResult {
        do {
            return try JSONDecoder().decode(AnalysisResult.self, from: data)
        } catch {
            throw VisionServiceError.decodeFailed
        }
    }
}
