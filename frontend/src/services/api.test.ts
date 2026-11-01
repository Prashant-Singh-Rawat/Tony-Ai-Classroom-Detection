// frontend/src/services/api.test.ts
import { describe, it, expect } from 'vitest'
import {
  DemoClassVisionApi,
  RealClassVisionApi,
  createClassVisionApi,
  api,
  API_CONFIG,
} from './api'
import { REPO_SNAPSHOT } from '../data/repoSnapshot'

describe('ClassVisionApi Service Layer & Truth Labeling', () => {
  it('instantiates the demo API by default', () => {
    expect(api).toBeInstanceOf(DemoClassVisionApi)
  })

  it('createClassVisionApi returns DemoClassVisionApi when demo flag is default/active', () => {
    const instance = createClassVisionApi()
    expect(instance).toBeInstanceOf(DemoClassVisionApi)
  })

  it('centralized API_CONFIG has defined endpoints and baseUrl', () => {
    expect(API_CONFIG.baseUrl).toBeDefined()
    expect(API_CONFIG.endpoints.dashboardSummary).toBe('/dashboard/summary')
    expect(API_CONFIG.endpoints.modelStatus).toBe('/model/status')
    expect(API_CONFIG.endpoints.settings).toBe('/settings')
  })

  describe('DemoClassVisionApi Implementation', () => {
    const demoApi = new DemoClassVisionApi()

    it('returns dashboard summary strictly flagged as isDemoData', async () => {
      const summary = await demoApi.getDashboardSummary()
      expect(summary.isDemoData).toBe(true)
      expect(summary.stats.totalPeopleDetected).toBeGreaterThan(0)
      expect(summary.activityTimeline.length).toBeGreaterThan(0)
    })

    it('returns sessions list with valid structure', async () => {
      const sessions = await demoApi.getSessions()
      expect(sessions.length).toBeGreaterThanOrEqual(1)
      expect(sessions[0].sessionId).toBeDefined()
      expect(sessions[0].privacyProtected).toBe(true)
    })

    it('returns canned RAG question response with groundings and demo flags', async () => {
      const res = await demoApi.askQuestion('What was covered regarding gradient descent?')
      expect(res.isDemoData).toBe(true)
      expect(res.isPlaceholder).toBe(true)
      expect(res.sources.length).toBeGreaterThan(0)
      expect(res.answer).toContain('Adam')
    })

    it('returns honest model quality report declaring NO_MODEL_TRAINED', async () => {
      const { modelQuality, reports } = await demoApi.getReports()
      expect(modelQuality.status).toBe('NO_MODEL_TRAINED')
      expect(modelQuality.modelCheckpoint).toContain('None')
      expect(modelQuality.evaluationDataset).toContain('None')
      expect(reports.length).toBeGreaterThan(0)
      expect(reports[0].isDemoData).toBe(true)
    })

    it('returns model status based on verified repo facts with 0 checkpoints and 60/60 tests', async () => {
      const modelStatus = await demoApi.getModelStatus()
      expect(modelStatus.modelCheckpointsCount).toBe(0)
      expect(modelStatus.activeCheckpoint).toBe('None')
      expect(modelStatus.trainingStatus).toBe('NOT_STARTED')
      expect(modelStatus.kaggleGestureDataset.totalImages).toBe(24000)
      expect(modelStatus.kaggleGestureDataset.trainImages).toBe(18000)
      expect(modelStatus.kaggleGestureDataset.testImages).toBe(6000)
      expect(modelStatus.kaggleGestureDataset.classes).toBe(20)
      expect(modelStatus.kaggleGestureDataset.semanticsVerified).toBe(false)
      expect(modelStatus.realClassroomDataset.collectedVideos).toBe(0)
      expect(modelStatus.evaluationMetrics.precision).toBe('Unavailable, no model trained')
      expect(modelStatus.evaluationMetrics.recall).toBe('Unavailable, no model trained')
      expect(modelStatus.evaluationMetrics.f1Score).toBe('Unavailable, no model trained')
      expect(modelStatus.evaluationMetrics.status).toBe('NOT CONNECTED')
      expect(modelStatus.verifiedTests.passed).toBe(60)
      expect(modelStatus.verifiedTests.total).toBe(60)
    })

    it('returns settings with strict offline guarantees and unconnected AI modules', async () => {
      const settings = await demoApi.getSettings()
      expect(settings.camera.hardwareConnected).toBe(false)
      expect(settings.privacy.faceBlurringActive).toBe(true)
      expect(settings.privacy.storeRawVideo).toBe(false)
      expect(settings.privacy.storageRoot).toContain('real_classroom')
      expect(settings.aiModules.visionInference).toContain('NOT CONNECTED')
      expect(settings.aiModules.whisperTranscription).toContain('NOT CONNECTED')
      expect(settings.system.offlineOnly).toBe(true)
    })

    it('returns system status with simulated stream and zero external telemetry', async () => {
      const status = await demoApi.getSystemStatus()
      expect(status.backendConnected).toBe(false)
      expect(status.useDemoData).toBe(true)
      expect(status.modelStatus).toContain('No model trained')
    })

    it('returns mock detection bounding boxes with personId and confidence', async () => {
      const boxes = await demoApi.getRealtimeDetections()
      expect(boxes.length).toBeGreaterThan(0)
      expect(boxes[0].confidence).toBeGreaterThan(0)
      expect(['hand_raised', 'hand_not_raised', 'ambiguous']).toContain(boxes[0].className)
    })

    it('returns pose estimation status with 17 COCO keypoints and posture classes', async () => {
      const status = await demoApi.getPoseStatus()
      expect(status.modelName).toBe('yolov8n-pose')
      expect(status.supportedKeypointsCount).toBe(17)
      expect(status.cocoKeypointOrder.length).toBe(17)
      expect(status.cocoKeypointOrder).toContain('left_shoulder')
      expect(status.cocoKeypointOrder).toContain('left_wrist')
      expect(status.postureClasses).toContain('BOTH_ARMS_RAISED')
      expect(status.postureClasses).toContain('LEFT_ARM_RAISED')
    })

    it('returns simulated human pose estimation with 17 keypoints and arm geometry', async () => {
      const dummyFile = new File(['dummy'], 'sample.jpg', { type: 'image/jpeg' })
      const res = await demoApi.estimatePose(dummyFile)
      expect(res.modelName).toBe('yolov8n-pose')
      expect(res.totalPersons).toBe(1)
      expect(res.persons[0].keypoints.length).toBe(17)
      expect(res.persons[0].geometry.leftArm.elbowAngleDeg).toBeGreaterThan(0)
      expect(res.persons[0].posture).toBe('LEFT_ARM_RAISED')
      expect(res.postureCounts['LEFT_ARM_RAISED']).toBe(1)
    })

    it('returns session activity analytics with unique anonymous tracks and timeline buckets', async () => {
      const analytics = await demoApi.getSessionActivityAnalytics('sess_01', 60)
      expect(analytics.sessionId).toBe('sess_01')
      expect(analytics.totalHandRaisingEvents).toBe(19)
      expect(analytics.uniqueAnonymousTracksObserved).toBe(12)
      expect(analytics.leftHandEvents).toBe(9)
      expect(analytics.rightHandEvents).toBe(8)
      expect(analytics.bothHandEvents).toBe(2)
      expect(analytics.averageEventDurationSeconds).toBeGreaterThan(0)
      expect(analytics.timeline.length).toBeGreaterThan(0)
      expect(analytics.trackSummaries.length).toBe(12)
      expect(analytics.trackSummaries[0].trackId).toBe('track_001')
    })

    it('returns cross-session comparison data with physical deltas', async () => {
      const comp = await demoApi.compareSessions('sess_01', 'sess_02')
      expect(comp.sessionA.sessionId).toBe('sess_01')
      expect(comp.sessionB.sessionId).toBe('sess_02')
      expect(comp.comparisons.length).toBeGreaterThan(0)
      expect(comp.comparisons[0].difference).toContain('+7')
    })

    it('returns analytics sessions list and CSV export string', async () => {
      const sessions = await demoApi.getAnalyticsSessions()
      expect(sessions.length).toBeGreaterThanOrEqual(3)
      expect(sessions[0].sessionId).toBe('sess_01')

      const csv = await demoApi.exportAnalyticsCsv('sess_01')
      expect(csv).toContain('CLASSVISION AI')
      expect(csv).toContain('sess_01')
    })
  })

  describe('RealClassVisionApi Placeholder Implementation', () => {
    const realApi = new RealClassVisionApi()

    it('throws descriptive error directing to demo data mode for getDashboardSummary', async () => {
      await expect(realApi.getDashboardSummary()).rejects.toThrow(
        'Set VITE_USE_DEMO_DATA=true.'
      )
    })

    it('throws descriptive error directing to demo data mode for getModelStatus', async () => {
      await expect(realApi.getModelStatus()).rejects.toThrow(
        'Set VITE_USE_DEMO_DATA=true.'
      )
    })

    it('throws descriptive error directing to demo data mode for getSettings', async () => {
      await expect(realApi.getSettings()).rejects.toThrow(
        'Set VITE_USE_DEMO_DATA=true.'
      )
    })
  })

  describe('RepoSnapshot Verification', () => {
    it('contains verified facts of Phase 0.8', () => {
      expect(REPO_SNAPSHOT.asOfPhase).toBe('Phase 0.8')
      expect(REPO_SNAPSHOT.kaggleDataset.totalImages).toBe(24000)
      expect(REPO_SNAPSHOT.realClassroomData.videos).toBe(0)
      expect(REPO_SNAPSHOT.modelCheckpoints.count).toBe(0)
      expect(REPO_SNAPSHOT.testSuite.passingTests).toBe(60)
    })
  })
})
