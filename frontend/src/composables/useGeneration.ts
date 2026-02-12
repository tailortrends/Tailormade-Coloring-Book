import { ref } from 'vue'
import { useSessionStorage } from '@vueuse/core'
import { booksApi } from '@/api/books'
import { useDrawingStore } from '@/store/drawing'
import type { BookRequest, BookResponse } from '@/types/book'

// Persist draft in sessionStorage — survives page refresh but cleared when browser closes
// This avoids storing PII (child names, school names in themes) in plaintext permanently
const draftKey = 'tailormade:book-draft'

export function useGeneration() {
  const drawing = useDrawingStore()
  const isGenerating = ref(false)
  const error = ref<string | null>(null)
  const progress = ref(0)
  const statusMessage = ref('Starting...')

  // SessionStorage draft — survives page refresh, cleared on browser close
  const draft = useSessionStorage<Partial<BookRequest>>(draftKey, {
    title: '',
    theme: '',
    page_count: 6, // default to 6
    age_range: '6-9',
    art_style: 'standard',
    character_name: '',
  })

  function updateDraft(updates: Partial<BookRequest>) {
    draft.value = { ...draft.value, ...updates }
  }

  function clearDraft() {
    draft.value = {
      title: '',
      theme: '',
      page_count: 6,
      age_range: '6-9',
      art_style: 'standard',
      character_name: '',
    }
  }

  async function generate(payload: BookRequest): Promise<BookResponse | null> {
    isGenerating.value = true
    error.value = null
    progress.value = 0
    statusMessage.value = 'Queuing job...'

    try {
      // 1. Kick off job
      const initialStatus = await booksApi.generate(payload)
      const jobId = initialStatus.job_id
      
      // 2. Poll until complete
      return await new Promise<BookResponse | null>((resolve, reject) => {
        const poll = async () => {
          try {
            const status = await booksApi.getStatus(jobId)
            
            // Update UI
            progress.value = status.progress
            if (status.message) statusMessage.value = status.message

            if (status.status === 'complete' && status.result) {
              drawing.setBook(status.result)
              clearDraft()
              resolve(status.result)
            } else if (status.status === 'failed') {
              reject(new Error(status.message || 'Generation failed'))
            } else {
              // Keep polling
              setTimeout(poll, 2000)
            }
          } catch (err) {
            reject(err)
          }
        }
        // Start polling
        setTimeout(poll, 1000)
      })

    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : 'Generation failed. Please try again.'
      return null
    } finally {
      isGenerating.value = false
    }
  }

  return {
    draft,
    isGenerating,
    error,
    progress,
    statusMessage,
    updateDraft,
    clearDraft,
    generate,
  }
}
