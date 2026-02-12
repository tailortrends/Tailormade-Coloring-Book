import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getAuth,
  signInWithPopup,
  GoogleAuthProvider,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  type User,
} from 'firebase/auth'
import { firebaseApp } from '@/lib/firebase'

const auth = getAuth(firebaseApp)
const provider = new GoogleAuthProvider()

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(true)

  const isAuthenticated = computed(() => !!user.value)
  const displayName = computed(() => user.value?.displayName ?? 'Friend')
  const photoURL = computed(() => user.value?.photoURL ?? null)

  // Initialize auth state listener
  function init() {
    onAuthStateChanged(auth, (firebaseUser) => {
      user.value = firebaseUser
      loading.value = false
    })
  }

  async function signInWithGoogle() {
    await signInWithPopup(auth, provider)
  }

  async function signOut() {
    await firebaseSignOut(auth)
    user.value = null
  }

  async function getIdToken(): Promise<string | null> {
    if (!user.value) return null
    return user.value.getIdToken()
  }

  return {
    user,
    loading,
    isAuthenticated,
    displayName,
    photoURL,
    init,
    signInWithGoogle,
    signOut,
    getIdToken,
  }
})
