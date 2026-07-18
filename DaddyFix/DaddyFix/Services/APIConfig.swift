//
//  APIConfig.swift
//  DaddyFix
//
//  CLOUD-FIRST: the iPhone only talks to the Daytona-hosted public API.
//  Kimi / Oxylabs / Nosana keys NEVER live on the device.
//

import Foundation

enum APIConfig {
    /// Public base URL of the Daddy Agent FastAPI **inside Daytona** (no trailing slash).
    ///
    /// Production / demo:
    ///   https://<your-daytona-preview-or-proxy-host>
    ///
    /// Local laptop only (engineer testing before Daytona deploy):
    ///   http://<your-mac-lan-ip>:8000
    ///
    /// Override at runtime with env `DADDYFIX_API_BASE` if needed.
    static var baseURL: URL = {
        if let env = ProcessInfo.processInfo.environment["DADDYFIX_API_BASE"],
           let url = URL(string: env) {
            return url
        }
        // TODO(demo): paste Daytona public URL here before judges.
        // Example: return URL(string: "https://xxxx.daytona.app")!
        return URL(string: "http://127.0.0.1:8000")!
    }()

    /// Offline AR-only fallback (no cloud). Use only if network dies mid-demo.
    static var forceMock: Bool = false

    /// What the phone is allowed to do with the cloud:
    /// - POST {baseURL}/analyze          → full agent (Kimi + Oxylabs + optional Nosana)
    /// - GET  {baseURL}/analyze/mock     → stable hero JSON
    /// - GET  {baseURL}/health           → stack flags
}
