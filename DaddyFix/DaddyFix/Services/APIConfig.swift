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
        // Daytona signed preview (live providers). Re-deploy if expired / sandbox deleted.
        // Local LAN: return URL(string: "http://YOUR_MAC_IP:8000")!
        return URL(string: "https://8000-s7xyqoldo2lkspem.daytonaproxy01.net")!
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
