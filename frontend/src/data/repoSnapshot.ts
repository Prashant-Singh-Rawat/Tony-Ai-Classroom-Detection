// frontend/src/data/repoSnapshot.ts
// REAL (snapshot of Phase 0.8, updated manually)
// This file stores verified, deterministic facts about the local repository.
// Any metric or attribute NOT in this snapshot is classified as NOT CONNECTED or DEMO DATA.

export interface RepoSnapshot {
  label: 'REAL (snapshot of Phase 0.8, updated manually)'
  asOfPhase: 'Phase 0.8'
  lastVerifiedDate: '2026-10-01'
  kaggleDataset: {
    totalImages: 24000
    trainImages: 18000
    testImages: 6000
    numClasses: 20
    classSemanticsVerified: false
    classSemanticsNote: 'Isolated hand gesture benchmark; does not represent classroom hand-raise detection'
    integrityConfirmed: true
    sha256Verified: true
  }
  realClassroomData: {
    videos: 0
    frames: 0
    annotations: 0
    note: 'Collection starts post 12 October 2026 upon college reopening'
  }
  modelCheckpoints: {
    count: 0
    activeWeights: 'None'
    note: 'Zero trained weights; training prohibited until dataset review'
  }
  testSuite: {
    totalTests: 60
    passingTests: 60
    status: 'ALL_PASSING'
  }
  unconnectedModules: {
    liveInference: 'NOT CONNECTED (No real camera/backend)'
    whisperTranscription: 'NOT CONNECTED (Backend pipeline pending)'
    blackboardOcr: 'NOT CONNECTED (EasyOCR pipeline pending)'
    ragAssistant: 'NOT CONNECTED (Dense vector store pending)'
    evaluationMetrics: 'NOT CONNECTED (Unavailable, no model trained)'
  }
}

export const REPO_SNAPSHOT: RepoSnapshot = {
  label: 'REAL (snapshot of Phase 0.8, updated manually)',
  asOfPhase: 'Phase 0.8',
  lastVerifiedDate: '2026-10-01',
  kaggleDataset: {
    totalImages: 24000,
    trainImages: 18000,
    testImages: 6000,
    numClasses: 20,
    classSemanticsVerified: false,
    classSemanticsNote:
      'Isolated hand gesture benchmark; does not represent classroom hand-raise detection',
    integrityConfirmed: true,
    sha256Verified: true,
  },
  realClassroomData: {
    videos: 0,
    frames: 0,
    annotations: 0,
    note: 'Collection starts post 12 October 2026 upon college reopening',
  },
  modelCheckpoints: {
    count: 0,
    activeWeights: 'None',
    note: 'Zero trained weights; training prohibited until dataset review',
  },
  testSuite: {
    totalTests: 60,
    passingTests: 60,
    status: 'ALL_PASSING',
  },
  unconnectedModules: {
    liveInference: 'NOT CONNECTED (No real camera/backend)',
    whisperTranscription: 'NOT CONNECTED (Backend pipeline pending)',
    blackboardOcr: 'NOT CONNECTED (EasyOCR pipeline pending)',
    ragAssistant: 'NOT CONNECTED (Dense vector store pending)',
    evaluationMetrics: 'NOT CONNECTED (Unavailable, no model trained)',
  },
}
