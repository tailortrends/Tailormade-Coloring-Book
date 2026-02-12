<script setup lang="ts">
defineProps<{
  progress?: number
  message?: string
}>()
</script>

<template>
  <div
    v-motion
    :initial="{ opacity: 0 }"
    :enter="{ opacity: 1 }"
    class="fixed inset-0 z-50 flex flex-col items-center justify-center bg-base-100/90 backdrop-blur-sm"
  >
    <div class="card-kid p-10 flex flex-col items-center gap-6 max-w-sm w-full mx-4">
      <!-- Bouncing dots animation -->
      <div class="flex gap-3">
        <span
          v-for="i in 3"
          :key="i"
          class="w-5 h-5 rounded-full bg-primary"
          :style="`animation: bounce 1.2s ${(i - 1) * 0.2}s infinite`"
        />
      </div>

      <p class="font-display text-2xl text-center text-neutral">
        {{ message ?? 'Creating your coloring book…' }}
      </p>

      <div v-if="progress !== undefined" class="w-full">
        <progress
          class="progress progress-primary w-full h-4 rounded-full"
          :value="progress"
          max="100"
        />
        <p class="text-center text-sm text-neutral/60 mt-2 font-body">
          {{ Math.round(progress) }}% complete
        </p>
      </div>

      <p class="text-sm text-neutral/50 font-body text-center">
        ✨ AI magic takes about 30–60 seconds
      </p>
    </div>
  </div>
</template>

<style scoped>
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50%       { transform: translateY(-16px); }
}
</style>
