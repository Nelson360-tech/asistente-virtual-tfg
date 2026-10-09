import type { DonnaViseme } from '../services/donnaApi'

/** Weights (0..1) for the ARKit blendshapes of the avatar's face. */
export type MouthShape = Record<string, number>

/**
 * Mouth shape for each of the 15 Oculus visemes returned by the backend.
 * Names use the facecap.glb convention (_L / _R instead of Left / Right).
 * 'sil' (silence) is the neutral face, so it has no weights.
 */
export const VISEME_SHAPES: Record<string, MouthShape> = {
  sil: {},
  PP: { mouthClose: 0.35, mouthPress_L: 0.5, mouthPress_R: 0.5 },
  FF: { jawOpen: 0.08, mouthRollLower: 0.55, mouthUpperUp_L: 0.2, mouthUpperUp_R: 0.2 },
  TH: { jawOpen: 0.15, tongueOut: 0.35 },
  DD: { jawOpen: 0.22, mouthStretch_L: 0.12, mouthStretch_R: 0.12 },
  kk: { jawOpen: 0.25, mouthStretch_L: 0.1, mouthStretch_R: 0.1 },
  CH: { jawOpen: 0.12, mouthFunnel: 0.45, mouthPucker: 0.2 },
  SS: { jawOpen: 0.08, mouthStretch_L: 0.3, mouthStretch_R: 0.3, mouthSmile_L: 0.12, mouthSmile_R: 0.12 },
  nn: { jawOpen: 0.15, mouthClose: 0.05 },
  RR: { jawOpen: 0.2, mouthFunnel: 0.25 },
  aa: { jawOpen: 0.6, mouthLowerDown_L: 0.3, mouthLowerDown_R: 0.3 },
  E: { jawOpen: 0.35, mouthStretch_L: 0.3, mouthStretch_R: 0.3, mouthSmile_L: 0.15, mouthSmile_R: 0.15 },
  I: { jawOpen: 0.2, mouthSmile_L: 0.4, mouthSmile_R: 0.4, mouthStretch_L: 0.2, mouthStretch_R: 0.2 },
  O: { jawOpen: 0.45, mouthFunnel: 0.55 },
  U: { jawOpen: 0.15, mouthPucker: 0.7, mouthFunnel: 0.3 }
}

/** Every blendshape the mouth uses, so it can be reset to 0 when not needed. */
export const MOUTH_BLENDSHAPES = [
  ...new Set(Object.values(VISEME_SHAPES).flatMap(shape => Object.keys(shape)))
]

/**
 * Returns the viseme active at `time` (seconds since the audio started).
 * The list comes sorted by `start`, so a binary search is enough.
 * Outside every interval the mouth is at rest ('sil').
 */
export function visemeAt(visemes: DonnaViseme[], time: number): string {
  let low = 0
  let high = visemes.length - 1

  while (low <= high) {
    const middle = (low + high) >> 1
    const cue = visemes[middle]!
    if (time < cue.start) high = middle - 1
    else if (time >= cue.end) low = middle + 1
    else return cue.viseme
  }
  return 'sil'
}
