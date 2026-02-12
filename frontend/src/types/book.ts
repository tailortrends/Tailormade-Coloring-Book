export type ArtStyle = 'simple' | 'standard' | 'detailed'
export type AgeRange = '3-5' | '6-9' | '10-12'

export interface BookRequest {
  title: string
  theme: string
  page_count: number
  age_range: AgeRange
  art_style: ArtStyle
  character_name?: string
}

export interface PageResult {
  page_number: number
  scene_description: string
  image_url: string
  thumbnail_url: string
}

export interface BookResponse {
  book_id: string
  title: string
  theme: string
  page_count: number
  pages: PageResult[]
  pdf_url: string
  created_at: string
  user_uid: string
}

export interface BookSummary {
  book_id: string
  title: string
  cover_thumbnail: string
  page_count: number
  created_at: string
}

export interface GenerationStatus {
  job_id: string
  status: 'pending' | 'generating' | 'complete' | 'failed'
  progress: number
  message: string
  result?: BookResponse
}
