<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useDebounceFn } from '@vueuse/core'
import { useGeneration } from '@/composables/useGeneration'
import KidButton from '@/components/shared/KidButton.vue'
import LoadingOverlay from '@/components/shared/LoadingOverlay.vue'
import type { BookRequest } from '@/types/book'

const router = useRouter()
const { draft, isGenerating, error, progress, updateDraft, generate } = useGeneration()

const debouncedUpdate = useDebounceFn((key: string, value: string) => {
  updateDraft({ [key]: value } as Partial<BookRequest>)
}, 300)

async function handleSubmit() {
  if (!draft.value.title || !draft.value.theme) return

  const book = await generate(draft.value as BookRequest)
  if (book) {
    router.push(`/studio/${book.book_id}`)
  }
}

const ageOptions = [
  { value: '3-5', label: '🐣 Ages 3–5 (simple)' },
  { value: '6-9', label: '🌟 Ages 6–9 (standard)' },
  { value: '10-12', label: '🎯 Ages 10–12 (detailed)' },
]
</script>

<template>
  <div class="max-w-2xl mx-auto px-4 py-10">
    <LoadingOverlay v-if="isGenerating" :progress="progress" />

    <div
      v-motion
      :initial="{ opacity: 0, y: 20 }"
      :enter="{ opacity: 1, y: 0 }"
    >
      <h1 class="font-display text-4xl text-primary mb-2">Create Your Book</h1>
      <p class="font-body text-neutral/60 mb-8">Fill in the details and let the magic begin ✨</p>

      <div class="card-kid p-8 flex flex-col gap-6">
        <!-- Title -->
        <div class="form-control">
          <label class="label font-display text-lg">Book Title</label>
          <input
            type="text"
            class="input input-bordered input-primary rounded-2xl font-body text-lg h-14"
            placeholder="Luna and the Magic Forest"
            :value="draft.title"
            maxlength="80"
            @input="debouncedUpdate('title', ($event.target as HTMLInputElement).value)"
          />
        </div>

        <!-- Theme / Story -->
        <div class="form-control">
          <label class="label font-display text-lg">Story & Characters</label>
          <textarea
            class="textarea textarea-primary rounded-2xl font-body text-base leading-relaxed min-h-[120px]"
            placeholder="A small bunny named Luna discovers a glowing mushroom that leads her to a hidden fairy village…"
            :value="draft.theme"
            maxlength="300"
            @input="debouncedUpdate('theme', ($event.target as HTMLTextAreaElement).value)"
          />
          <label class="label">
            <span class="label-text-alt text-neutral/40">
              {{ (draft.theme?.length ?? 0) }}/300 characters
            </span>
          </label>
        </div>

        <!-- Character Name -->
        <div class="form-control">
          <label class="label font-display text-lg">Character Name <span class="text-neutral/40 text-sm font-body">(optional)</span></label>
          <input
            type="text"
            class="input input-bordered rounded-2xl font-body text-lg h-14"
            placeholder="Luna"
            :value="draft.character_name"
            maxlength="50"
            @input="debouncedUpdate('character_name', ($event.target as HTMLInputElement).value)"
          />
        </div>

        <!-- Age Range -->
        <div class="form-control">
          <label class="label font-display text-lg">Age Group</label>
          <div class="flex flex-col sm:flex-row gap-3">
            <label
              v-for="opt in ageOptions"
              :key="opt.value"
              class="flex items-center gap-3 cursor-pointer card-kid px-5 py-4 flex-1 transition-colors"
              :class="draft.age_range === opt.value ? 'border-primary bg-primary/10' : ''"
            >
              <input
                type="radio"
                name="age_range"
                :value="opt.value"
                :checked="draft.age_range === opt.value"
                class="radio radio-primary"
                @change="updateDraft({ age_range: opt.value as any })"
              />
              <span class="font-body text-sm">{{ opt.label }}</span>
            </label>
          </div>
        </div>

        <!-- Page count -->
        <div class="form-control">
          <label class="label font-display text-lg">
            Number of Pages
            <span class="font-body text-neutral/60 ml-2">{{ draft.page_count }}</span>
          </label>
          <input
            type="range"
            min="2"
            max="12"
            :value="draft.page_count"
            class="range range-primary"
            step="2"
            @input="updateDraft({ page_count: +($event.target as HTMLInputElement).value })"
          />
          <div class="flex justify-between text-xs font-body text-neutral/40 mt-1">
            <span>2</span><span>6</span><span>10</span><span>12</span>
          </div>
        </div>

        <!-- Error -->
        <div v-if="error" class="alert alert-error rounded-2xl font-body">
          <span>⚠️ {{ error }}</span>
        </div>

        <!-- Submit -->
        <KidButton
          size="lg"
          :loading="isGenerating"
          :disabled="!draft.title || !draft.theme"
          @click="handleSubmit"
        >
          🎨 Generate My Book!
        </KidButton>
      </div>
    </div>
  </div>
</template>
