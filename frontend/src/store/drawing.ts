import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { BookResponse, PageResult } from '@/types/book'

export const useDrawingStore = defineStore('drawing', () => {
  // Active book being viewed / colored
  const activeBook = ref<BookResponse | null>(null)
  const currentPageIndex = ref(0)
  const isGenerating = ref(false)
  const generationError = ref<string | null>(null)

  const currentPage = computed<PageResult | null>(
    () => activeBook.value?.pages[currentPageIndex.value] ?? null
  )

  const totalPages = computed(() => activeBook.value?.pages.length ?? 0)

  const canGoNext = computed(
    () => currentPageIndex.value < totalPages.value - 1
  )

  const canGoPrev = computed(() => currentPageIndex.value > 0)

  function setBook(book: BookResponse) {
    activeBook.value = book
    currentPageIndex.value = 0
  }

  function nextPage() {
    if (canGoNext.value) currentPageIndex.value++
  }

  function prevPage() {
    if (canGoPrev.value) currentPageIndex.value--
  }

  function goToPage(index: number) {
    if (index >= 0 && index < totalPages.value) {
      currentPageIndex.value = index
    }
  }

  function clearBook() {
    activeBook.value = null
    currentPageIndex.value = 0
    generationError.value = null
  }

  return {
    activeBook,
    currentPageIndex,
    isGenerating,
    generationError,
    currentPage,
    totalPages,
    canGoNext,
    canGoPrev,
    setBook,
    nextPage,
    prevPage,
    goToPage,
    clearBook,
  }
})
