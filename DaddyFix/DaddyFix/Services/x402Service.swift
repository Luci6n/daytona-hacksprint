//
//  x402Service.swift
//  DaddyFix
//
//  Kenji — P1. Stub that mimics the x402 flow (headers, payment required,
//  success with tx hash) for the demo. Real on-chain only if everything
//  else is solid (AGENTS.md §7).
//

import Foundation

enum PaymentOutcome {
    case success(txHash: String)
    case failure(String)
}

actor x402Service {
    /// Simulates the 402 Payment Required → pay → success round trip.
    /// Swap for a real x402 client call once the demo core is stable.
    func pay(for part: BuyablePart) async -> PaymentOutcome {
        try? await Task.sleep(for: .seconds(1.2))
        let fakeTxHash = "0x" + UUID().uuidString.replacingOccurrences(of: "-", with: "").lowercased()
        return .success(txHash: fakeTxHash)
    }
}
