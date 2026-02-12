import { ref, markRaw } from 'vue'
import type Konva from 'konva'

export type BrushColor = string

export function useCanvas() {
  // markRaw prevents Vue from making Konva instances reactive (perf critical)
  const stageRef = ref<Konva.Stage | null>(null)
  const layerRef = ref<Konva.Layer | null>(null)

  const activeColor = ref<BrushColor>('#FF6B9D')
  const brushSize = ref(24)
  const isDrawing = ref(false)
  const history = ref<string[]>([]) // base64 snapshots for undo

  const PALETTE: BrushColor[] = [
    '#FF6B9D', '#FF8E53', '#FFE66D', '#68D391',
    '#4ECDC4', '#7EC8E3', '#A78BFA', '#F687B3',
    '#FBD38D', '#9AE6B4', '#000000', '#FFFFFF',
  ]

  function setStage(stage: Konva.Stage, layer: Konva.Layer) {
    stageRef.value = markRaw(stage)
    layerRef.value = markRaw(layer)
  }

  function setColor(color: BrushColor) {
    activeColor.value = color
  }

  function setBrushSize(size: number) {
    brushSize.value = Math.max(4, Math.min(80, size))
  }

  function _saveSnapshot() {
    const stage = stageRef.value
    if (!stage) return
    const snapshot = stage.toDataURL({ pixelRatio: 1 })
    history.value.push(snapshot)
    // Keep last 20 steps max
    if (history.value.length > 20) history.value.shift()
  }

  function undo() {
    if (history.value.length < 2) return
    history.value.pop() // remove current state
    // Restore previous state
    const prev = history.value[history.value.length - 1]
    const stage = stageRef.value
    const layer = layerRef.value
    if (!stage || !layer || !prev) return

    const img = new Image()
    img.src = prev
    img.onload = () => {
      layer.destroyChildren()
      const konvaImg = new (window as any).Konva.Image({ image: img, x: 0, y: 0 })
      layer.add(konvaImg)
      layer.draw()
    }
  }

  function exportAsPNG(): string | null {
    return stageRef.value?.toDataURL({ pixelRatio: 2 }) ?? null
  }

  function handlePointerDown() {
    isDrawing.value = true
    _saveSnapshot()
  }

  function handlePointerUp() {
    isDrawing.value = false
  }

  return {
    stageRef,
    layerRef,
    activeColor,
    brushSize,
    isDrawing,
    history,
    PALETTE,
    setStage,
    setColor,
    setBrushSize,
    undo,
    exportAsPNG,
    handlePointerDown,
    handlePointerUp,
  }
}
