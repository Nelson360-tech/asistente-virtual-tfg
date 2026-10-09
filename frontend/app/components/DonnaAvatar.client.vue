<script setup lang="ts">
/**
 * 3D avatar of Donna with lip sync.
 *
 * Loads a face with the 52 ARKit blendshapes (facecap.glb, from the Three.js
 * examples) and, while the answer audio is playing, moves the mouth with the
 * viseme that matches `audio.currentTime`.
 * The `.client` suffix makes Nuxt render it only in the browser (WebGL).
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader.js'
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'
import { useDonnaAvatar } from '../composables/useDonnaAvatar'
import { MOUTH_BLENDSHAPES, VISEME_SHAPES, visemeAt } from '../utils/visemeMouth'

const MODEL_URL = '/models/facecap.glb'
const TRANSCODER_PATH = '/basis/'
// How fast the mouth reaches the target shape (higher = snappier).
const MOUTH_SPEED = 18

const { audio, visemes, speaking } = useDonnaAvatar()

const container = ref<HTMLDivElement | null>(null)
const loading = ref(true)
const loadError = ref('')

let renderer: THREE.WebGLRenderer | null = null
let resizeObserver: ResizeObserver | null = null
let frameId = 0

onMounted(async () => {
  const el = container.value
  if (!el) return

  // Renderer, scene and camera
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  el.appendChild(renderer.domElement)

  const scene = new THREE.Scene()
  const environment = new THREE.PMREMGenerator(renderer)
  scene.environment = environment.fromScene(new RoomEnvironment(), 0.04).texture

  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 20)
  camera.position.set(0, 0.15, 5.4)

  function resize() {
    if (!renderer || !el) return
    const { clientWidth: width, clientHeight: height } = el
    if (!width || !height) return
    renderer.setSize(width, height)
    camera.aspect = width / height
    camera.updateProjectionMatrix()
  }
  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(el)
  resize()

  // Model (compressed with meshopt and KTX2 textures)
  const ktx2Loader = new KTX2Loader()
    .setTranscoderPath(TRANSCODER_PATH)
    .detectSupport(renderer)
  const loader = new GLTFLoader()
    .setKTX2Loader(ktx2Loader)
    .setMeshoptDecoder(MeshoptDecoder)

  let face: THREE.Mesh | null = null
  let model: THREE.Object3D | null = null
  try {
    const gltf = await loader.loadAsync(MODEL_URL)
    model = gltf.scene
    scene.add(model)
    // The face is the mesh that has the ARKit blendshapes.
    model.traverse(object => {
      const mesh = object as THREE.Mesh
      if (mesh.morphTargetDictionary?.jawOpen !== undefined) face = mesh
    })
    if (!face) throw new Error('The model has no ARKit blendshapes')
  } catch (err) {
    console.error(err)
    loadError.value = 'No se pudo cargar el avatar.'
    loading.value = false
    return
  }
  loading.value = false

  const dictionary = (face as THREE.Mesh).morphTargetDictionary!
  const influences = (face as THREE.Mesh).morphTargetInfluences!

  function setWeight(name: string, target: number, blend: number) {
    const index = dictionary[name]
    if (index === undefined) return
    influences[index]! += (target - influences[index]!) * blend
  }

  // Animation loop
  const clock = new THREE.Clock()
  let nextBlink = 2
  let blinkUntil = 0

  function animate() {
    frameId = requestAnimationFrame(animate)
    const delta = Math.min(clock.getDelta(), 0.1)
    const now = clock.elapsedTime
    // Frame-rate independent smoothing between the current and target shape
    const blend = 1 - Math.exp(-MOUTH_SPEED * delta)

    // 1. Mouth: viseme at the current audio time
    const playing = speaking.value && audio.value && !audio.value.paused
    const viseme = playing ? visemeAt(visemes.value, audio.value!.currentTime) : 'sil'
    const shape = VISEME_SHAPES[viseme] ?? {}
    for (const name of MOUTH_BLENDSHAPES) {
      setWeight(name, shape[name] ?? 0, blend)
    }

    // 2. Blink every few seconds so the face looks alive
    if (now > nextBlink) {
      blinkUntil = now + 0.12
      nextBlink = now + 2.5 + Math.random() * 3
    }
    const eyesClosed = now < blinkUntil ? 1 : 0
    setWeight('eyeBlink_L', eyesClosed, 0.6)
    setWeight('eyeBlink_R', eyesClosed, 0.6)

    // 3. Gentle head movement
    if (model) {
      model.rotation.y = Math.sin(now * 0.5) * 0.08
      model.rotation.x = Math.sin(now * 0.33) * 0.03
    }

    renderer!.render(scene, camera)
  }
  animate()
})

onBeforeUnmount(() => {
  cancelAnimationFrame(frameId)
  resizeObserver?.disconnect()
  renderer?.dispose()
  renderer?.domElement.remove()
  renderer = null
})
</script>

<template>
  <div ref="container" class="donna-avatar-canvas">
    <p v-if="loading" class="avatar-status">Cargando avatar…</p>
    <p v-else-if="loadError" class="avatar-status">{{ loadError }}</p>
  </div>
</template>

<style scoped>
.donna-avatar-canvas {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 320px;
}

.donna-avatar-canvas :deep(canvas) {
  display: block;
}

.avatar-status {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  margin: 0;
  font-size: 13px;
  color: var(--muted);
}
</style>
