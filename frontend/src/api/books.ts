import { apiClient } from './client'
import type { BookRequest, BookResponse, BookSummary, GenerationStatus } from '@/types/book'

export const booksApi = {
  // Returns Job ID immediately
  async generate(payload: BookRequest): Promise<GenerationStatus> {
    const { data } = await apiClient.post<GenerationStatus>('/books/generate', payload)
    return data
  },

  // Poll status
  async getStatus(jobId: string): Promise<GenerationStatus> {
    const { data } = await apiClient.get<GenerationStatus>(`/books/generate/${jobId}`)
    return data
  },

  async list(): Promise<BookSummary[]> {
    const { data } = await apiClient.get<BookSummary[]>('/books/')
    return data
  },

  async getById(bookId: string): Promise<BookResponse> {
    const { data } = await apiClient.get<BookResponse>(`/books/${bookId}`)
    return data
  },
}
