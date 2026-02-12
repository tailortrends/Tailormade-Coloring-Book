import { ref } from 'vue'

const MAX_DIMENSION = 1024 // px — downscale before sending to backend

export function useImagePipeline() {
  const isProcessing = ref(false)
  const preview = ref<string | null>(null)

  /**
   * Resize image client-side to MAX_DIMENSION on longest side.
   * Converts to grayscale preview for display.
   * Returns a Blob ready to upload — never sends a 4K raw photo to the server.
   */
  async function processImage(file: File): Promise<Blob | null> {
    if (!file.type.startsWith('image/')) {
      console.warn('useImagePipeline: not an image file')
      return null
    }

    isProcessing.value = true

    return new Promise((resolve) => {
      const img = new Image()
      const objectUrl = URL.createObjectURL(file)

      img.onload = () => {
        URL.revokeObjectURL(objectUrl)

        // Calculate scaled dimensions
        let { width, height } = img
        if (width > MAX_DIMENSION || height > MAX_DIMENSION) {
          if (width > height) {
            height = Math.round((height * MAX_DIMENSION) / width)
            width = MAX_DIMENSION
          } else {
            width = Math.round((width * MAX_DIMENSION) / height)
            height = MAX_DIMENSION
          }
        }

        // Draw resized to hidden canvas
        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext('2d')!
        ctx.drawImage(img, 0, 0, width, height)

        // Grayscale preview for display
        const imageData = ctx.getImageData(0, 0, width, height)
        const data = imageData.data
        for (let i = 0; i < data.length; i += 4) {
          const avg = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]
          data[i] = data[i + 1] = data[i + 2] = avg
        }
        ctx.putImageData(imageData, 0, 0)
        preview.value = canvas.toDataURL('image/jpeg', 0.85)

        canvas.toBlob(
          (blob) => {
            isProcessing.value = false
            resolve(blob)
          },
          'image/jpeg',
          0.85
        )
      }

      img.onerror = () => {
        isProcessing.value = false
        resolve(null)
      }

      img.src = objectUrl
    })
  }

  function clearPreview() {
    preview.value = null
  }

  return { isProcessing, preview, processImage, clearPreview }
}
