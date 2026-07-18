//
//  ContentView.swift
//  DaddyFix
//
//  Brian — Scan (one-shot) + Live (1–2s WS frames) + optional RTSP.
//

import SwiftUI

struct ContentView: View {
    @StateObject private var app = AppState()
    @State private var rtspURL: String = ""
    @State private var showRTSPField = false

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
            app.bindSelection()
            app.checkHealth()
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
            StatusChipView(
                sessionManager: app.sessionManager,
                phase: app.phase,
                backendHealthy: app.backendHealthy,
                liveStatus: app.liveSession.status.rawValue,
                framesSent: app.liveSession.framesSent
            )
            Spacer()
            Toggle(isOn: $app.showMeshOverlay) {
                Text("LiDAR").font(.caption.weight(.semibold))
            }
            .toggleStyle(.button)
            .padding(8)
            .background(.ultraThinMaterial, in: Capsule())
        }
    }

    private var bottomBar: some View {
        VStack(spacing: 10) {
            if let label = app.selectedPartLabel {
                Text("Selected: \(label)").font(.headline)
            }
            if let item = app.analysis?.detectedItem {
                Text(item).font(.subheadline.weight(.semibold))
            }
            Text(app.statusMessage)
                .font(.footnote)
                .multilineTextAlignment(.center)
            if let lastError = app.lastError ?? app.liveSession.lastError {
                Text(lastError)
                    .font(.caption2)
                    .foregroundStyle(.orange)
                    .multilineTextAlignment(.center)
            }

            TextField("Symptom / question", text: $app.symptomText)
                .textFieldStyle(.roundedBorder)
                .font(.footnote)

            Toggle("Live auto-analyze each frame", isOn: $app.liveAutoAnalyze)
                .font(.caption)
                .disabled(app.phase == .live)

            // One-shot
            HStack(spacing: 8) {
                Button("Scan") { app.scan() }
                    .buttonStyle(.borderedProminent)
                    .disabled(app.phase == .analyzing || app.phase == .live)

                Button("Local mock") { app.applyLocalMock() }
                    .buttonStyle(.bordered)

                Button("Reset") { app.reset() }
                    .buttonStyle(.bordered)
            }

            // Live phone stream
            HStack(spacing: 8) {
                if app.phase == .live && app.rtspSessionId == nil {
                    Button("Stop Live") { app.stopLive() }
                        .buttonStyle(.borderedProminent)
                    Button("Barge-in") { app.bargeIn() }
                        .buttonStyle(.bordered)
                    Button("Ask") { app.askLive() }
                        .buttonStyle(.bordered)
                } else if app.rtspSessionId == nil {
                    Button("Live (1–2s frames)") { app.startLive() }
                        .buttonStyle(.borderedProminent)
                }
            }

            // RTSP
            Button(showRTSPField ? "Hide RTSP" : "RTSP camera…") {
                showRTSPField.toggle()
            }
            .font(.caption)

            if showRTSPField {
                TextField("rtsp://user:pass@cam:554/stream", text: $rtspURL)
                    .textFieldStyle(.roundedBorder)
                    .font(.caption2)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                HStack {
                    Button("Start RTSP") {
                        app.startRTSP(rtspUrl: rtspURL.trimmingCharacters(in: .whitespacesAndNewlines))
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(rtspURL.count < 10)
                    if app.rtspSessionId != nil {
                        Button("Stop RTSP") { app.stopRTSP() }
                            .buttonStyle(.bordered)
                    }
                }
            }
        }
        .padding()
        .frame(maxWidth: .infinity)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16))
    }
}

private struct StatusChipView: View {
    @ObservedObject var sessionManager: ARSessionManager
    var phase: AppState.Phase
    var backendHealthy: Bool?
    var liveStatus: String
    var framesSent: Int

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(statusColor)
                .frame(width: 8, height: 8)
            VStack(alignment: .leading, spacing: 2) {
                Text(sessionManager.trackingStatus.rawValue)
                    .font(.caption.weight(.semibold))
                Text(sessionManager.isLiDARAvailable ? "LiDAR ready" : "No LiDAR")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Text("phase: \(phase.rawValue)")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Text(backendLabel)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                if phase == .live {
                    Text("live: \(liveStatus) · frames \(framesSent)")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(.ultraThinMaterial, in: Capsule())
    }

    private var backendLabel: String {
        switch backendHealthy {
        case true: return "API: ok"
        case false: return "API: down"
        case nil: return "API: …"
        }
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
