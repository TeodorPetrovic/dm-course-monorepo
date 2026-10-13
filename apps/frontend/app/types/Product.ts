export interface Product {
  product_id: number
  slug: string
  name: string
  img_url: string
  description: string
  category_id: number
  price: number | null
  seo?: Seo
}

export interface Seo {
  title: string,
  description: string,
  key_words: string[]
}

// dm-ml preporuka (neki endpoint-i vraćaju samo product_id/name/score -> dopuni iz kataloga)
export interface Rec {
  product_id: number
  name: string
  score?: number
  sources?: string[]
  slug?: string
  img_url?: string
  price?: number | null
  description?: string
  category_id?: number
}
