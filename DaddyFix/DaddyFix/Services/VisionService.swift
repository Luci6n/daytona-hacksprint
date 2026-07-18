//
//  VisionService.swift
//  DaddyFix
//
//  Brian — HTTP client for Lucian's backend (docs/backend-api.md).
//  POST /analyze  { symptom, deviceHint, imageBase64 }
//  GET  /health
//  No silent live→mock fallback (Lucian policy). Explicit mock helpers only.
//

import Foundation
import UIKit

enum VisionServiceError: LocalizedError {
    case invalidURL
    case badStatus(Int, String)
    case decodeFailed
    case emptyImage
    case healthFailed(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid API base URL"
        case .badStatus(let code, let body): return "API \(code): \(body)"
        case .decodeFailed: return "Could not decode AnalysisResult"
        case .emptyImage: return "Empty image data"
        case .healthFailed(let detail): return "Health check failed: \(detail)"
        }
    }
}

struct HealthResponse: Codable, Sendable {
    let status: String?
    let service: String?
    let environment: String?
    let demoMode: Bool?
    let providers: [String: Bool]?
}

/// Client for Lucian FastAPI (Daytona). No sponsor credentials on device.
actor VisionService {
    var baseURL: URL

    init(baseURL: URL = APIConfig.baseURL) {
        self.baseURL = baseURL
    }

    // MARK: - Health

    func health() async throws -> HealthResponse {
        let url = baseURL.appendingPathComponent("health")
        var request = URLRequest(url: url)
        Self.applyCommonHeaders(to: &request)
        let (data, response) = try await URLSession.shared.data(for: request)
        try Self.validate(response: response, data: data)
        return try JSONDecoder().decode(HealthResponse.self, from: data)
    }

    // MARK: - Analyze (Lucian contract)

    /// Local fixture only — explicit demo path, not a silent fallback for live errors.
    func localMock() -> AnalysisResult {
        .waterHeaterMock
    }

    func analyze(
        image: UIImage,
        symptom: String? = nil,
        deviceHint: String? = APIConfig.defaultDeviceHint, // nil = no false prior
        maxEdge: CGFloat = 1280,
        compression: CGFloat = 0.72
    ) async throws -> AnalysisResult {
        if APIConfig.forceLocalMock { return localMock() }

        let resized = image.daddyfixResized(maxEdge: maxEdge)
        guard let jpeg = resized.jpegData(compressionQuality: compression) else {
            throw VisionServiceError.emptyImage
        }
        return try await analyze(
            imageJPEG: jpeg,
            symptom: symptom,
            deviceHint: deviceHint
        )
    }

    func analyze(
        imageJPEG: Data,
        symptom: String? = nil,
        deviceHint: String? = APIConfig.defaultDeviceHint
    ) async throws -> AnalysisResult {
        if APIConfig.forceLocalMock { return localMock() }

        let url = baseURL.appendingPathComponent("analyze")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        Self.applyCommonHeaders(to: &request)
        request.timeoutInterval = APIConfig.analyzeTimeout

        // Lucian accepts data URL or raw base64; data URL recommended.
        let dataURL = "data:image/jpeg;base64," + imageJPEG.base64EncodedString()

        struct Payload: Encodable {
            let symptom: String?
            let deviceHint: String?
            let imageBase64: String
        }

        request.httpBody = try JSONEncoder().encode(
            Payload(
                symptom: symptom,
                deviceHint: deviceHint,
                imageBase64: dataURL
            )
        )

        let (data, response) = try await URLSession.shared.data(for: request)
        try Self.validate(response: response, data: data)
        return try Self.decodeAnalysis(data)
    }

    // MARK: - RTSP continuous (server-side sampling)

    struct RTSPStartResponse: Codable, Sendable {
        let ok: Bool?
        let sessionId: String
        let intervalSec: Double?
        let ffmpeg: Bool?
        let latestUrl: String?
    }

    func startRTSP(
        rtspUrl: String,
        intervalSec: Double = 2.0,
        symptom: String? = nil,
        deviceHint: String? = APIConfig.defaultDeviceHint
    ) async throws -> RTSPStartResponse {
        let url = baseURL.appendingPathComponent("rtsp/start")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30

        struct Body: Encodable {
            let rtspUrl: String
            let intervalSec: Double
            let symptom: String?
            let deviceHint: String?
        }
        request.httpBody = try JSONEncoder().encode(
            Body(
                rtspUrl: rtspUrl,
                intervalSec: intervalSec,
                symptom: symptom,
                deviceHint: deviceHint
            )
        )
        let (data, response) = try await URLSession.shared.data(for: request)
        try Self.validate(response: response, data: data)
        return try JSONDecoder().decode(RTSPStartResponse.self, from: data)
    }

    func fetchRTSPLatest(sessionId: String) async throws -> AnalysisResult {
        let url = baseURL
            .appendingPathComponent("rtsp")
            .appendingPathComponent(sessionId)
            .appendingPathComponent("latest")
        let (data, response) = try await URLSession.shared.data(from: url)
        try Self.validate(response: response, data: data)
        return try Self.decodeAnalysis(data)
    }

    func stopRTSP(sessionId: String) async throws {
        let url = baseURL
            .appendingPathComponent("rtsp")
            .appendingPathComponent(sessionId)
            .appendingPathComponent("stop")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        let (data, response) = try await URLSession.shared.data(for: request)
        try Self.validate(response: response, data: data)
    }

    // MARK: - Helpers

    /// ngrok free tier interstitial can break URLSession without this header.
    private static func applyCommonHeaders(to request: inout URLRequest) {
        request.setValue("1", forHTTPHeaderField: "ngrok-skip-browser-warning")
        request.setValue("DaddyFix-iOS", forHTTPHeaderField: "User-Agent")
    }

    private static func validate(response: URLResponse, data: Data) throws {
        guard let http = response as? HTTPURLResponse else { return }
        guard (200 ... 299).contains(http.statusCode) else {
            // Lucian: { "detail": "..." }
            if let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let detail = obj["detail"] as? String {
                throw VisionServiceError.badStatus(http.statusCode, detail)
            }
            let body = String(data: data, encoding: .utf8) ?? ""
            throw VisionServiceError.badStatus(http.statusCode, body)
        }
    }

    private static func decodeAnalysis(_ data: Data) throws -> AnalysisResult {
        do {
            return try JSONDecoder().decode(AnalysisResult.self, from: data)
        } catch {
            throw VisionServiceError.decodeFailed
        }
    }
}

// MARK: - Image resize

private extension UIImage {
    func daddyfixResized(maxEdge: CGFloat) -> UIImage {
        let w = size.width
        let h = size.height
        let longest = max(w, h)
        guard longest > maxEdge, longest > 0 else { return self }
        let scale = maxEdge / longest
        let newSize = CGSize(width: w * scale, height: h * scale)
        let renderer = UIGraphicsImageRenderer(size: newSize)
        return renderer.image { _ in
            draw(in: CGRect(origin: .zero, size: newSize))
        }
    }
}
