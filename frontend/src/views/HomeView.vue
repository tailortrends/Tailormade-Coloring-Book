<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import KidButton from '@/components/shared/KidButton.vue'

const router = useRouter()
const auth = useAuthStore()

async function handleGetStarted() {
  if (!auth.isAuthenticated) {
    await auth.signInWithGoogle()
  }
  router.push('/create')
}
</script>

<template>
  <div class="flex flex-col items-center justify-center min-h-[80vh] px-4 py-12 text-center">
    <!-- Hero -->
    <div
      v-motion
      :initial="{ opacity: 0, y: 40 }"
      :enter="{ opacity: 1, y: 0, transition: { duration: 600 } }"
      class="flex flex-col items-center gap-6 max-w-2xl"
    >
      <div class="text-8xl">🎨</div>

      <h1 class="font-display text-5xl sm:text-6xl text-primary leading-tight">
        TailorMade<br />
        <span class="text-secondary">Coloring Book</span>
      </h1>

      <p class="font-body text-xl text-neutral/70 max-w-md">
        Turn your child's imagination into a personalized coloring book — in seconds.
        <br />
        <span class="text-accent font-bold">Describe a story. We draw it. They color it.</span>
      </p>

      <KidButton size="lg" @click="handleGetStarted">
        🚀 Create My Book
      </KidButton>
    </div>

    <!-- Feature cards -->
    <div
      v-motion
      :initial="{ opacity: 0, y: 20 }"
      :enter="{ opacity: 1, y: 0, transition: { delay: 300, duration: 500 } }"
      class="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-16 max-w-3xl w-full"
    >
      <div v-for="feature in features" :key="feature.icon" class="card-kid p-6 flex flex-col items-center gap-3">
        <span class="text-4xl">{{ feature.icon }}</span>
        <h3 class="font-display text-xl">{{ feature.title }}</h3>
        <p class="font-body text-sm text-neutral/60 text-center">{{ feature.desc }}</p>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
const features = [
  { icon: '✍️', title: 'Describe It', desc: 'Tell us about characters, a theme, or a story idea' },
  { icon: '🤖', title: 'AI Draws It', desc: 'Beautiful black & white line art, ready to color' },
  { icon: '🖨️', title: 'Print It', desc: 'Download a print-ready PDF — perfect for home or school' },
]
</script>
