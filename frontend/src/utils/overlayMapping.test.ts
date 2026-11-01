/**
 * frontend/src/utils/overlayMapping.test.ts
 * Unit tests for video aspect ratio, resizing, fullscreen, and object-fit overlay mapping.
 */

import { describe, it, expect } from 'vitest'
import {
  computeRenderedVideoRect,
  mapNormalizedBoxToContainerPixels,
} from './overlayMapping'

describe('Overlay Mapping & Aspect Ratio Alignment', () => {
  it('correctly maps 16:9 video into 16:9 container with zero offset', () => {
    const videoDims = { width: 1920, height: 1080 }
    const containerDims = { width: 960, height: 540 }
    const rect = computeRenderedVideoRect(videoDims, containerDims, 'contain')

    expect(rect.offsetX).toBeCloseTo(0.0)
    expect(rect.offsetY).toBeCloseTo(0.0)
    expect(rect.renderedWidth).toBeCloseTo(960.0)
    expect(rect.renderedHeight).toBeCloseTo(540.0)
    expect(rect.scale).toBeCloseTo(0.5)

    const box = mapNormalizedBoxToContainerPixels({ x: 10, y: 20, w: 30, h: 40 }, rect)
    expect(box.left).toBeCloseTo(96.0)
    expect(box.top).toBeCloseTo(108.0)
    expect(box.width).toBeCloseTo(288.0)
    expect(box.height).toBeCloseTo(216.0)
  })

  it('correctly handles pillarboxing (black bars on left/right) in wide container', () => {
    // 16:9 video in ultra-wide 21:9 container (1920x800)
    const videoDims = { width: 1920, height: 1080 }
    const containerDims = { width: 1920, height: 800 }
    const rect = computeRenderedVideoRect(videoDims, containerDims, 'contain')

    // Expected rendered height = 800, width = 800 * (16/9) = 1422.22
    // Black bars left & right: (1920 - 1422.22)/2 = 248.89
    expect(rect.renderedHeight).toBeCloseTo(800.0)
    expect(rect.renderedWidth).toBeCloseTo(800 * (16 / 9), 1)
    expect(rect.offsetY).toBe(0)
    expect(rect.offsetX).toBeCloseTo((1920 - 800 * (16 / 9)) / 2, 1)

    // Bounding box at left=0% must start at offsetX, not at container left 0
    const box = mapNormalizedBoxToContainerPixels({ x: 0, y: 0, w: 50, h: 50 }, rect)
    expect(box.left).toBeCloseTo(rect.offsetX)
    expect(box.top).toBe(0)
  })

  it('correctly handles letterboxing (black bars on top/bottom) in tall container', () => {
    // 16:9 video in 4:3 container (800x600)
    const videoDims = { width: 1920, height: 1080 }
    const containerDims = { width: 800, height: 600 }
    const rect = computeRenderedVideoRect(videoDims, containerDims, 'contain')

    // Expected rendered width = 800, height = 800 / (16/9) = 450
    // Black bars top & bottom: (600 - 450) / 2 = 75
    expect(rect.renderedWidth).toBeCloseTo(800.0)
    expect(rect.renderedHeight).toBeCloseTo(450.0)
    expect(rect.offsetX).toBe(0)
    expect(rect.offsetY).toBeCloseTo(75.0)

    const box = mapNormalizedBoxToContainerPixels({ x: 10, y: 10, w: 20, h: 20 }, rect)
    expect(box.left).toBeCloseTo(80.0)
    expect(box.top).toBeCloseTo(75.0 + 45.0)
    expect(box.width).toBeCloseTo(160.0)
    expect(box.height).toBeCloseTo(90.0)
  })

  it('handles zero or negative dimensions safely without throwing', () => {
    const rect = computeRenderedVideoRect({ width: 0, height: 0 }, { width: 800, height: 600 })
    expect(rect.renderedWidth).toBe(0)
    expect(rect.renderedHeight).toBe(0)

    const box = mapNormalizedBoxToContainerPixels({ x: 10, y: 10, w: 20, h: 20 }, rect)
    expect(box.left).toBe(0)
    expect(box.top).toBe(0)
  })
})
