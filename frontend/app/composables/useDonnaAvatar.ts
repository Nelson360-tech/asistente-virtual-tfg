import { inject, type InjectionKey, type Ref } from 'vue'
import type { DonnaViseme } from '../services/donnaApi'

/**
 * Datos que app.vue comparte con el componente del avatar 3D.
 * El avatar se monta dentro del contenedor `#donna-avatar` y puede
 * sincronizar los visemas con `audio.currentTime`.
 */
export interface DonnaAvatarState {
  /** Elemento <audio> que reproduce la respuesta de Donna. */
  audio: Ref<HTMLAudioElement | null>
  /** Visemas de la última respuesta (start/end en segundos). */
  visemes: Ref<DonnaViseme[]>
  /** true mientras se reproduce la respuesta. */
  speaking: Ref<boolean>
  /** true mientras el usuario está grabando. */
  listening: Ref<boolean>
  /** true mientras se espera la respuesta del backend. */
  processing: Ref<boolean>
}

export const donnaAvatarKey: InjectionKey<DonnaAvatarState> =
  Symbol('donna-avatar')

export function useDonnaAvatar(): DonnaAvatarState {
  const state = inject(donnaAvatarKey)
  if (!state) {
    throw new Error('useDonnaAvatar debe usarse dentro de app.vue')
  }
  return state
}
