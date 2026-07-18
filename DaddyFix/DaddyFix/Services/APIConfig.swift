//
//  APIConfig.swift
//  DaddyFix
//
//  CLOUD-FIRST: iPhone only talks to Lucian's Daytona-hosted API.
//  Sponsor keys NEVER live on the device.
//

import Foundation

enum APIConfig {
    /// Lucian backend base URL (no trailing slash).
    /// Demo: paste public Daytona HTTPS URL here.
    /// Local: Mac LAN IP when testing on device (127.0.0.1 only works in Simulator).
    static var baseURL: URL = {
        if let env = ProcessInfo.processInfo.environment["DADDYFIX_API_BASE"],
           let url = URL(string: env) {
            return url
        }
        // TODO(demo): replace with Daytona public URL before judges.
        return URL(string: "http://127.0.0.1:8000")!
    }()

    /// WebSocket base derived from HTTP(S) base.
    static var webSocketBaseURL: URL {
        var components = URLComponents(url: baseURL, resolvingAgainstBaseURL: false)!
        if components.scheme == "https" {
            components.scheme = "wss"
        } else {
            components.scheme = "ws"
        }
        return components.url ?? baseURL
    }

    /// Offline / emergency only. Prefer server DEMO_MODE when available.
    static var forceLocalMock: Bool = false

    static let defaultDeviceHint = "Rinnai tankless water heater"
    static let analyzeTimeout: TimeInterval = 120
    static let speechTimeout: TimeInterval = 60
}
