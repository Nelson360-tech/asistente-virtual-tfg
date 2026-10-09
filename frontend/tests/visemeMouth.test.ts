// Tests for the viseme → mouth shape logic of the avatar. Run with: npm test
import { test, describe } from 'node:test'
import assert from 'node:assert/strict'

import { MOUTH_BLENDSHAPES, VISEME_SHAPES, visemeAt } from '../app/utils/visemeMouth.ts'

const OCULUS_VISEMES = ['sil', 'PP', 'FF', 'TH', 'DD', 'kk', 'CH', 'SS', 'nn', 'RR', 'aa', 'E', 'I', 'O', 'U']

describe('VISEME_SHAPES', () => {
  test('has a shape for each of the 15 Oculus visemes', () => {
    assert.deepEqual(Object.keys(VISEME_SHAPES).sort(), [...OCULUS_VISEMES].sort())
  })

  test('all weights are between 0 and 1', () => {
    for (const shape of Object.values(VISEME_SHAPES)) {
      for (const weight of Object.values(shape)) {
        assert.ok(weight >= 0 && weight <= 1)
      }
    }
  })

  test('MOUTH_BLENDSHAPES lists every blendshape used, once', () => {
    assert.equal(new Set(MOUTH_BLENDSHAPES).size, MOUTH_BLENDSHAPES.length)
    assert.ok(MOUTH_BLENDSHAPES.includes('jawOpen'))
  })
})

describe('visemeAt', () => {
  const cues = [
    { start: 0, end: 0.1, viseme: 'sil' },
    { start: 0.1, end: 0.25, viseme: 'O' },
    { start: 0.25, end: 0.4, viseme: 'aa' }
  ]

  test('returns the viseme active at that time', () => {
    assert.equal(visemeAt(cues, 0.15), 'O')
    assert.equal(visemeAt(cues, 0.3), 'aa')
  })

  test('the end of an interval belongs to the next one', () => {
    assert.equal(visemeAt(cues, 0.25), 'aa')
  })

  test('returns sil outside the cues or with no cues', () => {
    assert.equal(visemeAt(cues, 5), 'sil')
    assert.equal(visemeAt([], 0.2), 'sil')
  })
})
