# BARKLY Mock Data Audit (Phase 4.1)

Verifies that every screen a user can reach in the shipping app is backed by the
live backend + real models, and that mock/seed data is confined to places that
can never be reached in production.

## Where mock data exists

| Layer | Location | Used by |
| --- | --- | --- |
| Repository doubles | `Barkly/Data/Mock/` (`MockDogRepository`, `MockHistoryRepository`, `MockAnalysisRepository`, `MockInsightsRepository`, `MockAudioRecorder`, `MockSeeds`) | `AppDependencies.demo` only |
| Permission double | `MockPermissionService` in `Barkly/Domain/Repositories/MediaPermissionService.swift` | `AppDependencies.demo` only |
| Dependency assembly | `AppContainer(dependencies:)` + `AppDependencies.demo` | XCTest previews and the `#Preview` macros |
| Preview fixtures | `MockSeeds.max/owner/demoAnalyses()` referenced by `DogDetailView` `#Preview`, `AnalysisResultView` `#Preview` | SwiftUI preview canvas (never shipped) |
| Unit tests | `BarklyTests/*` | XCTest only |

## Live-path guarantee

The production view root uses `AppDependencies.live`:

- `AppContainer()` → `AppDependencies.live` in `AppContainer.swift`.
- RootView gating (`RootView.swift`) shows `AuthView` first whenever
  `usesBackend && !isAuthenticated`, so a user cannot pass through onboarding or
  reach any dog/analysis screen with demo dependencies.

Audited references:

- `Mock*` usage in `Barkly/` appears only inside `AppDependencies.demo`,
  unit tests, previews, or the `Data/Mock/` folder itself. No production
  `View`, `AppContainer` command, or networking path references a mock.
- The single preview fixture outside `Data/Mock/` is
  `DogDetailView`'s `#Preview(dog: MockSeeds.max)` — compile-time only.

## What changed in 4.1 to remove mock-era behavior

| Area | Change |
| --- | --- |
| Add dog | New `AddDogView` creates through `APIDogRepository`; the server-returned dog becomes the selected dog (no local-only persistence). |
| Edit dog | `DogDetailView` removed the mock-era copy "Profile changes stay on this device for now"; edits now PATCH the server and adopt the confirmed response. |
| History | `HistoryView` loads real paged `GET /api/v1/history` data with refresh + incremental pagination; completed rows navigate to results, everything else shows a status row. No seeded analyses anywhere in the live path. |
| Insights | `DerivedInsightsRepository` aggregates live history; `MockInsightsRepository` was reduced to a thin wrapper over the same aggregation so demo and live cannot disagree; insufficient-data state added. |
| Feedback | `AnalysisResultView` surfaces submit failures instead of silently reporting success. |

## Conclusion

There is no path from a shipped screen to mock data. Demo/preview data is
reachable only through `AppDependencies.demo`, which RootView never uses.