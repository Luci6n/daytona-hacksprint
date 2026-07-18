//
//  ContentView.swift
//  DaddyFix
//
//  Kenji — real app shell. Replaces Brian's ARDebugHostView placeholder:
//  embeds ARViewContainer full-bleed, adds Scan/Reset chrome, and wires
//  taps → RepairGuideView / PaymentModal (see LUCIAN_INTEGRATION.md).
//

import SwiftUI

struct ContentView: View {
    @StateObject private var app = AppState()

    var body: some View {
        ZStack {
            ARViewContainer(
                sessionManager: app.sessionManager,
                raycastManager: app.raycastManager,
                showMeshOverlay: app.showMeshOverlay,
                autoPlaceMockAnnotations: false
            )
            .ignoresSafeArea()

            VStack {
                topBar
                Spacer()
                bottomBar
            }
            .padding()
        }
        .onAppear {
            app.raycastManager.onAnnotationSelected = { label in
                app.selectPart(label)
            }
        }
        .sheet(isPresented: $app.showRepairGuide) {
            if let analysis = app.analysis {
                RepairGuideView(
                    analysis: analysis,
                    selectedLabel: app.selectedPartLabel,
                    onBuyTapped: {
                        app.showRepairGuide = false
                        app.showPayment = true
                    }
                )
            }
        }
        .sheet(isPresented: $app.showPayment) {
            if let part = app.analysis?.buyableParts.first {
                PaymentModal(part: part)
            }
        }
    }

    private var topBar: some View {
        HStack {
            StatusChipView(sessionManager: app.sessionManager, phase: app.phase)
            Spacer()
            Toggle(isOn: $app.showMeshOverlay) {
                Text("LiDAR mesh").font(.caption.weight(.semibold))
            }
            .toggleStyle(.button)
            .padding(8)
            .background(.ultraThinMaterial, in: Capsule())
        }
    }

    private var bottomBar: some View {
        VStack(spacing: 10) {
            if let label = app.selectedPartLabel {
                Text("Selected: \(label)")
                    .font(.headline)
            }
            if let item = app.analysis?.detectedItem {
                Text(item)
                    .font(.subheadline.weight(.semibold))
            }
            Text(app.statusMessage)
                .font(.footnote)
                .multilineTextAlignment(.center)
            if let lastError = app.lastError {
                Text(lastError)
                    .font(.caption2)
                    .foregroundStyle(.orange)
                    .multilineTextAlignment(.center)
            }

            HStack(spacing: 12) {
                Button("Scan") {
                    app.scan()
                }
                .buttonStyle(.borderedProminent)

                Button("Reset") {
                    app.reset()
                }
                .buttonStyle(.bordered)
            }
        }
        .padding()
        .frame(maxWidth: .infinity)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16))
    }
}

/// Small subview that observes ARSessionManager directly — AppState being
/// an ObservableObject doesn't re-publish when a nested ObservableObject's
/// @Published properties change, so the live status chip needs its own
/// @ObservedObject to update. `phase` is passed in as a value since it's
/// read fresh from AppState on every ContentView re-render.
private struct StatusChipView: View {
    @ObservedObject var sessionManager: ARSessionManager
    var phase: AppState.Phase

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(statusColor)
                .frame(width: 8, height: 8)
            VStack(alignment: .leading, spacing: 2) {
                Text(sessionManager.trackingStatus.rawValue)
                    .font(.caption.weight(.semibold))
                Text(sessionManager.isLiDARAvailable ? "LiDAR ready" : "No LiDAR — planes only")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Text("phase: \(phase.rawValue)")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(.ultraThinMaterial, in: Capsule())
    }

    private var statusColor: Color {
        switch sessionManager.trackingStatus {
        case .normal: return .green
        case .initializing, .relocalizing: return .yellow
        case .limited: return .orange
        case .notAvailable: return .red
        }
    }
}

#Preview {
    ContentView()
}
