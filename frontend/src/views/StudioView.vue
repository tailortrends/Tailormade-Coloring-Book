<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { saveAs } from 'file-saver'
import { useDrawingStore } from '@/store/drawing'
import { booksApi } from '@/api/books'
import DrawingCanvas from '@/components/canvas/DrawingCanvas.vue'
import KidButton from '@/components/shared/KidButton.vue'

const route = useRoute()
const router = useRouter()
const drawing = useDrawingStore()

onMounted(async () => {
  const bookId = route.params.bookId as string
  if (!drawing.activeBook || drawing.activeBook.book_id !== bookId) {
    try {
      const book = await booksApi.getById(bookId)
      drawing.setBook(book)
    } catch {
      router.push('/gallery')
    }
  }
})

function downloadPDF() {
  if (drawing.activeBook?.pdf_url) {
    saveAs(drawing.activeBook.pdf_url, `${drawing.activeBook.title}.pdf`)
  }
}
</script>

<template>
  <div v-if="drawing.activeBook" class="max-w-4xl mx-auto px-4 py-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6 flex-wrap gap-4">
      <div>
        <h1 class="font-display text-3xl text-primary">{{ drawing.activeBook.title }}</h1>
        <p class="font-body text-sm text-neutral/50">
          Page {{ drawing.currentPageIndex + 1 }} of {{ drawing.totalPages }}
        </p>
      </div>
      <div class="flex gap-3">
        <KidButton variant="secondary" size="sm" @click="router.push('/gallery')">
          My Books
        </KidButton>
        <KidButton variant="accent" size="sm" @click="downloadPDF">
          🖨️ Print PDF
        </KidButton>
      </div>
    </div>

    <!-- Main canvas -->
    <DrawingCanvas
      v-if="drawing.currentPage"
      :image-url="drawing.currentPage.image_url"
    />

    <!-- Page description -->
    <p class="font-body text-sm text-neutral/50 text-center mt-3 italic">
      {{ drawing.currentPage?.scene_description }}
    </p>

    <!-- Page navigation -->
    <div class="flex items-center justify-center gap-4 mt-6">
      <KidButton
        variant="ghost"
        :disabled="!drawing.canGoPrev"
        @click="drawing.prevPage()"
      >
        ← Prev
      </KidButton>

      <!-- Page thumbnails -->
      <div class="flex gap-2 overflow-x-auto py-2">
        <button
          v-for="(page, i) in drawing.activeBook.pages"
          :key="page.page_number"
          class="flex-shrink-0 w-14 h-18 rounded-xl overflow-hidden border-4 transition-all"
          :class="i === drawing.currentPageIndex
            ? 'border-primary shadow-lg scale-105'
            : 'border-base-300 opacity-60 hover:opacity-100'"
          @click="drawing.goToPage(i)"
        >
          <img
            :src="page.thumbnail_url"
            :alt="`Page ${page.page_number}`"
            class="w-full h-full object-cover"
            loading="lazy"
            decoding="async"
          />
        </button>
      </div>

      <KidButton
        variant="ghost"
        :disabled="!drawing.canGoNext"
        @click="drawing.nextPage()"
      >
        Next →
      </KidButton>
    </div>
  </div>

  <!-- Loading state -->
  <div v-else class="flex items-center justify-center min-h-[60vh]">
    <span class="loading loading-spinner loading-lg text-primary" />
  </div>
</template>
