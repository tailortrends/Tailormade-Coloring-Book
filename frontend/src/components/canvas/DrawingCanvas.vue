<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useElementSize } from '@vueuse/core'
import { useCanvas } from '@/composables/useCanvas'

const props = defineProps<{
  imageUrl: string
}>()

const { activeColor, brushSize, PALETTE, setColor, setBrushSize, undo, exportAsPNG } = useCanvas()

const containerRef = ref<HTMLElement | null>(null)
const { width: containerWidth } = useElementSize(containerRef)

// Canvas dimensions maintain US Letter aspect ratio
const canvasWidth = ref(600)
const canvasHeight = ref(776) // 600 * (11/8.5)

watch(containerWidth, (w) => {
  if (w > 0) {
    canvasWidth.value = Math.min(w, 700)
    canvasHeight.value = Math.round(canvasWidth.value * (11 / 8.5))
  }
})

// Konva config
const stageConfig = ref({ width: canvasWidth, height: canvasHeight })
const backgroundConfig = ref({ x: 0, y: 0, width: canvasWidth, height: canvasHeight })

// Brush line drawing
const lines = ref<Array<{ points: number[]; color: string; size: number }>>([])
const isPainting = ref(false)
const currentLine = ref<number[]>([])

function handleMouseDown(e: any) {
  isPainting.value = true
  const pos = e.target.getStage().getPointerPosition()
  currentLine.value = [pos.x, pos.y]
}

function handleMouseMove(e: any) {
  if (!isPainting.value) return
  const pos = e.target.getStage().getPointerPosition()
  currentLine.value = [...currentLine.value, pos.x, pos.y]
}

function handleMouseUp() {
  if (!isPainting.value) return
  isPainting.value = false
  lines.value.push({
    points: [...currentLine.value],
    color: activeColor.value,
    size: brushSize.value,
  })
  currentLine.value = []
}

function getLineConfig(line: (typeof lines.value)[0]) {
  return {
    points: line.points,
    stroke: line.color,
    strokeWidth: line.size,
    tension: 0.5,
    lineCap: 'round' as const,
    lineJoin: 'round' as const,
    globalCompositeOperation: 'multiply' as const,
  }
}

function handleUndo() {
  lines.value.pop()
}

defineExpose({ exportAsPNG })
</script>

<template>
  <div ref="containerRef" class="canvas-wrapper w-full">
    <!-- Konva Stage -->
    <v-stage
      :config="{ width: canvasWidth, height: canvasHeight }"
      @mousedown="handleMouseDown"
      @mousemove="handleMouseMove"
      @mouseup="handleMouseUp"
      @touchstart="handleMouseDown"
      @touchmove="handleMouseMove"
      @touchend="handleMouseUp"
    >
      <v-layer>
        <!-- Coloring page image as background -->
        <v-image
          v-if="imageUrl"
          :config="{
            x: 0, y: 0,
            width: canvasWidth, height: canvasHeight,
            image: undefined,
          }"
        />
        <!-- Drawn lines -->
        <v-line
          v-for="(line, i) in lines"
          :key="i"
          :config="getLineConfig(line)"
        />
        <!-- Active line being drawn -->
        <v-line
          v-if="currentLine.length > 1"
          :config="{
            points: currentLine,
            stroke: activeColor,
            strokeWidth: brushSize,
            tension: 0.5,
            lineCap: 'round',
            lineJoin: 'round',
            globalCompositeOperation: 'multiply',
          }"
        />
      </v-layer>
    </v-stage>
  </div>

  <!-- Toolbar -->
  <div class="mt-4 flex flex-col gap-4">
    <!-- Color palette -->
    <div class="flex flex-wrap gap-3 justify-center">
      <button
        v-for="color in PALETTE"
        :key="color"
        class="w-10 h-10 rounded-full border-4 transition-transform hover:scale-110 active:scale-95 min-h-0 min-w-0"
        :style="{
          backgroundColor: color,
          borderColor: activeColor === color ? '#333' : 'transparent',
          transform: activeColor === color ? 'scale(1.2)' : undefined,
        }"
        @click="setColor(color)"
      />
    </div>

    <!-- Brush size + undo -->
    <div class="flex items-center gap-4 justify-center">
      <span class="font-body text-sm text-neutral/60">Brush:</span>
      <input
        type="range"
        min="4"
        max="60"
        :value="brushSize"
        class="range range-primary w-32"
        @input="setBrushSize(+($event.target as HTMLInputElement).value)"
      />
      <button
        class="btn btn-ghost btn-sm rounded-full text-lg"
        title="Undo"
        @click="handleUndo"
      >
        ↩️
      </button>
    </div>
  </div>
</template>
