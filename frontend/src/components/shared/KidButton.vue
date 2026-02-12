<script setup lang="ts">
defineProps<{
  variant?: 'primary' | 'secondary' | 'accent' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
}>()

defineEmits<{ click: [] }>()
</script>

<template>
  <button
    v-motion
    :initial="{ scale: 1 }"
    :hover="{ scale: 1.05 }"
    :tap="{ scale: 0.95 }"
    :class="[
      'btn btn-kid',
      `btn-${variant ?? 'primary'}`,
      size === 'sm' ? 'btn-sm text-base' : size === 'lg' ? 'btn-lg text-xl' : 'text-lg',
    ]"
    :disabled="disabled || loading"
    @click="$emit('click')"
  >
    <span v-if="loading" class="loading loading-spinner loading-sm mr-2" />
    <slot />
  </button>
</template>
