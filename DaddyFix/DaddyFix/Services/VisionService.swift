//
//  VisionService.swift
//  DaddyFix
//
//  Thin HTTP client → backend /analyze (Kimi vision on server).
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

/// Client for backend FastAPI (Daytona-hosted in demo). Kimi runs server-side.
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

    /// GET /analyze/mock — connectivity + contract check.
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
