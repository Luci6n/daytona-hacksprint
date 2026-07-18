//
//  PaymentModal.swift
//  DaddyFix
//
//  Kenji — P1. Mimics the x402 flow: payment-required state, a pay
//  action, then success with a tx hash (AGENTS.md §7). Wire to a real
//  on-chain call later via x402Service.
//

import SwiftUI

private enum PaymentState {
    case paymentRequired
    case processing
    case success(txHash: String)
    case failed(String)
}

struct PaymentModal: View {
    let part: BuyablePart

    @Environment(\.dismiss) private var dismiss
    @State private var state: PaymentState = .paymentRequired
    private let service = x402Service()

    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                switch state {
                case .paymentRequired:
                    paymentRequiredView
                case .processing:
                    ProgressView("Processing payment…")
                case .success(let txHash):
                    successView(txHash: txHash)
                case .failed(let message):
                    failedView(message: message)
                }
            }
            .padding()
            .navigationTitle("Buy Replacement")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                }
            }
        }
    }

    private var paymentRequiredView: some View {
        VStack(alignment: .leading, spacing: 16) {
            Label("402 Payment Required", systemImage: "lock.fill")
                .font(.headline)
                .foregroundStyle(.orange)

            VStack(alignment: .leading, spacing: 4) {
                Text(part.name).font(.title3.weight(.semibold))
                Text("Estimated: \(part.estimatedPrice)").foregroundStyle(.secondary)
            }

            Button("Pay with x402") {
                pay()
            }
            .buttonStyle(.borderedProminent)
            .frame(maxWidth: .infinity)
        }
    }

    private func successView(txHash: String) -> some View {
        VStack(spacing: 12) {
            Image(systemName: "checkmark.seal.fill")
                .font(.system(size: 44))
                .foregroundStyle(.green)
            Text("Payment successful").font(.headline)
            Text(txHash)
                .font(.caption.monospaced())
                .foregroundStyle(.secondary)
                .lineLimit(1)
                .truncationMode(.middle)
        }
    }

    private func failedView(message: String) -> some View {
        VStack(spacing: 12) {
            Image(systemName: "xmark.octagon.fill")
                .font(.system(size: 44))
                .foregroundStyle(.red)
            Text("Payment failed").font(.headline)
            Text(message).font(.footnote).foregroundStyle(.secondary)
            Button("Try again") { state = .paymentRequired }
        }
    }

    private func pay() {
        state = .processing
        Task {
            switch await service.pay(for: part) {
            case .success(let txHash):
                state = .success(txHash: txHash)
            case .failure(let message):
                state = .failed(message)
            }
        }
    }
}

#Preview {
    PaymentModal(part: AnalysisResult.waterHeaterMock.buyableParts[0])
}
