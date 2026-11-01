/**
 * frontend/src/utils/overlayMapping.ts
 * Computes exact displayed video content rectangle inside a container
 * considering aspect ratio, dimensions, and object-fit (contain/cover/fill).
 * Ensures bounding boxes and skeletons align exactly without letterbox/pillarbox offset.
 */

export interface VideoDimensions {
  width: number
  height: number
}

export interface ContainerDimensions {
  width: number
  height: number
}

export interface RenderedVideoRect {
  offsetX: number
  offsetY: number
  renderedWidth: number
  renderedHeight: number
  scale: number
}

export type ObjectFitMode = 'contain' | 'cover' | 'fill'

/**
 * Computes the exact rectangle where the video pixels are displayed inside the container.
 */
export function computeRenderedVideoRect(
  videoDims: VideoDimensions,
  containerDims: ContainerDimensions,
  fit: ObjectFitMode = 'contain'
): RenderedVideoRect {
  const { width: vw, height: vh } = videoDims
  const { width: cw, height: ch } = containerDims

  if (vw <= 0 || vh <= 0 || cw <= 0 || ch <= 0) {
    return { offsetX: 0, offsetY: 0, renderedWidth: 0, renderedHeight: 0, scale: 1.0 }
  }

  if (fit === 'fill') {
    return { offsetX: 0, offsetY: 0, renderedWidth: cw, renderedHeight: ch, scale: cw / vw }
  }

  const videoAspect = vw / vh
  const containerAspect = cw / ch

  if (fit === 'contain') {
    if (containerAspect > videoAspect) {
      // Pillarboxed (black bars left and right)
      const renderedHeight = ch
      const renderedWidth = ch * videoAspect
      const offsetX = (cw - renderedWidth) / 2
      const offsetY = 0
      const scale = ch / vh
      return { offsetX, offsetY, renderedWidth, renderedHeight, scale }
    } else {
      // Letterboxed (black bars top and bottom)
      const renderedWidth = cw
      const renderedHeight = cw / videoAspect
      const offsetX = 0
      const offsetY = (ch - renderedHeight) / 2
      const scale = cw / vw
      return { offsetX, offsetY, renderedWidth, renderedHeight, scale }
    }
  }

  // fit === 'cover'
  if (containerAspect > videoAspect) {
    const renderedWidth = cw
    const renderedHeight = cw / videoAspect
    const offsetX = 0
    const offsetY = (ch - renderedHeight) / 2
    const scale = cw / vw
    return { offsetX, offsetY, renderedWidth, renderedHeight, scale }
  } else {
    const renderedHeight = ch
    const renderedWidth = ch * videoAspect
    const offsetX = (cw - renderedWidth) / 2
    const offsetY = 0
    const scale = ch / vh
    return { offsetX, offsetY, renderedWidth, renderedHeight, scale }
  }
}

/**
 * Maps a normalized percentage bounding box (x, y, w, h in [0-100]%)
 * to CSS pixel coordinates and dimensions relative to container.
 */
export function mapNormalizedBoxToContainerPixels(
  boxPct: { x: number; y: number; w: number; h: number },
  rect: RenderedVideoRect
): { left: number; top: number; width: number; height: number } {
  return {
    left: rect.offsetX + (boxPct.x / 100) * rect.renderedWidth,
    top: rect.offsetY + (boxPct.y / 100) * rect.renderedHeight,
    width: (boxPct.w / 100) * rect.renderedWidth,
    height: (boxPct.h / 100) * rect.renderedHeight,
  }
}
