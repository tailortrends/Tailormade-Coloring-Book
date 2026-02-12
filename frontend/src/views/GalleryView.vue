<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAutoAnimate } from '@formkit/auto-animate/vue'
import { booksApi } from '@/api/books'
import KidButton from '@/components/shared/KidButton.vue'
import type { BookSummary } from '@/types/book'

const router = useRouter()
const books = ref<BookSummary[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const [gridRef] = useAutoAnimate()

onMounted(async () => {
  try {
    books.value = await booksApi.list()
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Failed to load books.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-10">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8 flex-wrap gap-4">
      <h1 class="font-display text-4xl text-primary">My Books 📚</h1>
      <KidButton @click="router.push('/create')">
        + New Book
      </KidButton>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <span class="loading loading-spinner loading-lg text-primary" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="alert alert-error rounded-2xl font-body">
      {{ error }}
    </div>

    <!-- Empty state -->
    <div
      v-else-if="books.length === 0"
      v-motion
      :initial="{ opacity: 0, scale: 0.9 }"
      :enter="{ opacity: 1, scale: 1 }"
      class="text-center py-20 flex flex-col items-center gap-6"
    >
      <span class="text-7xl">🎨</span>
      <h2 class="font-display text-3xl text-neutral/50">No books yet!</h2>
      <p class="font-body text-neutral/40">Create your first personalized coloring book</p>
      <KidButton size="lg" @click="router.push('/create')">
        Create My First Book
      </KidButton>
    </div>

    <!-- Book grid -->
    <div
      v-else
      ref="gridRef"
      class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-6"
    >
      <div
        v-for="book in books"
        :key="book.book_id"
        v-motion
        :initial="{ opacity: 0, y: 20 }"
        :enter="{ opacity: 1, y: 0 }"
        class="card-kid cursor-pointer hover:shadow-xl transition-shadow"
        @click="router.push(`/studio/${book.book_id}`)"
      >
        <!-- Cover thumbnail -->
        <figure class="rounded-t-4xl overflow-hidden">
          <img
            :src="book.cover_thumbnail"
            :alt="book.title"
            class="w-full aspect-[8.5/11] object-cover bg-base-200"
            loading="lazy"
            decoding="async"
          />
        </figure>
        <div class="p-4">
          <h3 class="font-display text-base leading-tight line-clamp-2">{{ book.title }}</h3>
          <p class="font-body text-xs text-neutral/40 mt-1">
            {{ book.page_count }} pages
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
