import SwiftUI
import PhotosUI
import UniformTypeIdentifiers

struct MediaFlowView: View {
    enum Mode {
        case video
        case any
    }

    let mode: Mode
    let onDone: () -> Void

    @Environment(AppContainer.self) private var app
    @State private var controller: AnalysisFlowController?
    @State private var selection: PhotosPickerItem?
    @State private var pickedImage: UIImage?
    @State private var pickedImageURL: URL?
    @State private var pickedMovie: MovieFile?
    @State private var isLoading = false
    @State private var analyzeError: AnalysisFlowController.AnalysisError?

    private var title: String {
        switch mode {
        case .video: "Analyze a video"
        case .any: "Upload media"
        }
    }

    var body: some View {
        ZStack {
            BarklyColor.background
                .ignoresSafeArea()
            Group {
                if let controller {
                    content(for: controller)
                } else {
                    Color.clear
                }
            }
            .navigationTitle(title)
            .navigationBarTitleDisplayMode(.inline)
        }
        .task {
            guard controller == nil else { return }
            let flow = AnalysisFlowController(container: app)
            controller = flow
            await flow.begin(route: mode == .video ? .video : .upload)
        }
        .onChange(of: selection) { _, newValue in
            load(newValue)
        }
    }

    @ViewBuilder
    private func content(for controller: AnalysisFlowController) -> some View {
        switch controller.phase {
        case .idle:
            selectionContent
        case .processing:
            AnalysisProcessingView(caption: processingCaption)
        case .ready(let analysis):
            AnalysisResultView(
                analysis: analysis,
                dog: app.selectedDog,
                onDone: onDone
            )
        case .failed(let failure):
            ErrorStateView(failure: AppFailure(
                title: failure.title,
                message: failure.message,
                hint: failure.hint,
                recovery: mapRecovery(failure.recovery)
            )) {
                controller.resetToSelection()
            }
            .padding(BarklySpacing.lg)
        case .requestingPermission, .recording:
            Color.clear
        }
    }

    private var processingCaption: String {
        switch mode {
        case .video: "Reading the video's signals"
        case .any: pickedMovie != nil ? "Reading the video's signals" : "Reading the photo's signals"
        }
    }

    private func mapRecovery(_ recovery: AnalysisFlowController.AnalysisError.Recovery) -> AppFailure.Recovery? {
        switch recovery {
        case .retry: return .retry
        case .openSettings: return .openSettings
        case .none: return nil
        }
    }

    @ViewBuilder
    private var selectionContent: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: BarklySpacing.sectionGap) {
                header
                pickerCard
                if let pickedImage {
                    photoPreview(pickedImage)
                } else if let pickedMovie {
                    moviePreview(pickedMovie)
                }
                analyzeButton
            }
            .padding(.horizontal, BarklySpacing.pagePadding)
            .padding(.top, BarklySpacing.sm)
            .padding(.bottom, BarklySpacing.xl)
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: BarklySpacing.sm) {
            Text(title)
                .font(BarklyFont.heroTitle)
                .foregroundStyle(BarklyColor.primaryText)
            Text("Pick a clip to estimate. On this device, BARKLY works offline with your own media.")
                .font(BarklyFont.body)
                .foregroundStyle(BarklyColor.secondaryText)
        }
    }

    private var pickerCard: some View {
        PhotosPicker(selection: $selection, matching: matching) {
            HStack(spacing: BarklySpacing.md) {
                ZStack {
                    RoundedRectangle(cornerRadius: BarklyRadius.small, style: .continuous)
                        .fill(BarklyColor.cosmicOrangeSoft)
                        .frame(width: 46, height: 46)
                    Image(systemName: mode == .video ? "video.fill" : "photo.fill")
                        .font(.system(size: 19, weight: .semibold))
                        .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                }
                .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 2) {
                    Text(mode == .video ? "Choose a video" : "Choose a photo or video")
                        .font(BarklyFont.label)
                        .foregroundStyle(BarklyColor.primaryText)
                    Text("Browse your photo library")
                        .font(BarklyFont.caption)
                        .foregroundStyle(BarklyColor.secondaryText)
                }
                Spacer(minLength: 0)
                Image(systemName: "photo.on.rectangle.angled")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundStyle(BarklyColor.tertiaryText)
                    .accessibilityHidden(true)
            }
            .padding(BarklySpacing.md)
            .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                    .strokeBorder(BarklyColor.divider.opacity(0.6), lineWidth: 1)
            )
            .contentShape(RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
        }
        .buttonStyle(BarklyRowPressStyle())
        .accessibilityLabel(mode == .video ? "Choose a video" : "Choose a photo or video")
        .accessibilityHint("Opens your photo library")
    }

    private var matching: PHPickerFilter {
        switch mode {
        case .video: .videos
        case .any: .any(of: [.images, .videos])
        }
    }

    @ViewBuilder
    private func photoPreview(_ image: UIImage) -> some View {
        VStack(alignment: .leading, spacing: BarklySpacing.md) {
            Text("Selected photo")
                .font(BarklyFont.sectionHeader)
                .foregroundStyle(BarklyColor.primaryText)
            Image(uiImage: image)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(maxWidth: .infinity)
                .clipShape(RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                        .strokeBorder(BarklyColor.divider, lineWidth: 1)
                )
                .accessibilityLabel("Selected photo preview")
        }
    }

    @ViewBuilder
    private func moviePreview(_ movie: MovieFile) -> some View {
        VStack(alignment: .leading, spacing: BarklySpacing.md) {
            Text("Selected video")
                .font(BarklyFont.sectionHeader)
                .foregroundStyle(BarklyColor.primaryText)
            HStack(spacing: BarklySpacing.md) {
                ZStack {
                    RoundedRectangle(cornerRadius: BarklyRadius.small, style: .continuous)
                        .fill(BarklyColor.surface)
                        .frame(width: 64, height: 64)
                    Image(systemName: "play.fill")
                        .font(.system(size: 20, weight: .semibold))
                        .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                }
                .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 2) {
                    Text(movie.url.lastPathComponent)
                        .font(BarklyFont.label)
                        .foregroundStyle(BarklyColor.primaryText)
                        .lineLimit(1)
                    Text("Video ready to analyze")
                        .font(BarklyFont.caption)
                        .foregroundStyle(BarklyColor.secondaryText)
                }
                Spacer(minLength: 0)
            }
            .padding(BarklySpacing.md)
            .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                    .strokeBorder(BarklyColor.divider.opacity(0.6), lineWidth: 1)
            )
        }
    }

    @ViewBuilder
    private var analyzeButton: some View {
        if pickedImage != nil || pickedMovie != nil {
            BarklyButton(title: "Analyze", icon: "waveform") {
                analyze()
            }
            .transition(.opacity)
        }
    }

    private func analyze() {
        guard let controller else { return }
        let inputType: AnalysisInputType
        let mediaURLs: [URL]
        if let pickedMovie {
            inputType = .video
            mediaURLs = [pickedMovie.url]
        } else if pickedImage != nil {
            inputType = .photo
            mediaURLs = pickedImageURL.map { [$0] } ?? []
        } else {
            inputType = mode == .video ? .video : .photo
            mediaURLs = []
        }
        Haptics.medium()
        Task {
            await controller.submit(inputType: inputType, mediaURLs: mediaURLs)
        }
    }

    private func stash(image: UIImage) -> URL? {
        guard let data = image.jpegData(compressionQuality: 0.92) else { return nil }
        let url = URL.temporaryDirectory
            .appendingPathComponent("barkly-photo-\(UUID().uuidString)")
            .appendingPathExtension("jpg")
        do {
            try data.write(to: url)
            return url
        } catch {
            return nil
        }
    }

    private func load(_ item: PhotosPickerItem?) {
        guard let item else { return }
        isLoading = true
        Task {
            defer { isLoading = false }
            if let movie: MovieFile = try? await item.loadTransferable(type: MovieFile.self) {
                pickedMovie = movie
                pickedImage = nil
                pickedImageURL = nil
                return
            }
            if let data = try? await item.loadTransferable(type: Data.self),
               let image = UIImage(data: data) {
                pickedImage = image
                pickedMovie = nil
                pickedImageURL = stash(image: image)
            }
        }
    }
}

struct MovieFile: Transferable {
    let url: URL

    static var transferRepresentation: some TransferRepresentation {
        FileRepresentation(contentType: .movie) { movie in
            SentTransferredFile(movie.url)
        } importing: { received in
            let destination = URL.temporaryDirectory
                .appendingPathComponent(UUID().uuidString)
                .appendingPathExtension(received.file.pathExtension.isEmpty ? "mov" : received.file.pathExtension)
            do {
                try FileManager.default.copyItem(at: received.file, to: destination)
                return MovieFile(url: destination)
            } catch {
                throw CancellationError()
            }
        }
    }
}

#Preview("Idle") {
    NavigationStack {
        MediaFlowView(mode: .any, onDone: {})
    }
    .environment(AppContainer())
}