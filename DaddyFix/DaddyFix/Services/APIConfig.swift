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
        // LIVE VISION path: Mac uvicorn + ngrok tunnel (Daytona sandbox has no egress
        // to ai&/Doubleword). Keep Mac terminal + ngrok running during demo.
        // Fallback Daytona DEMO: https://8000-u8mwnhxfpzuttscl.daytonaproxy01.net
        return URL(string: "https://coretta-biauricular-remy.ngrok-free.dev")!
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

    /// Leave empty so the model trusts the camera, not a fake water-heater prior.
    static let defaultDeviceHint: String? = nil
    static let analyzeTimeout: TimeInterval = 120
    static let speechTimeout: TimeInterval = 60
}
