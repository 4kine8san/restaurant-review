export interface Master {
  id: number;
  category: string;
  value: string;
  sort_order: number;
}

export interface PhotoMeta {
  id: number;
  sort_order: number;
  rotation: number;
}

export interface Restaurant {
  id: number;
  name: string;
  nearest_station: string | null;
  genre_id: number | null;
  genre_name: string | null;
  scene: string | null;
  stars: number | null;
  rating_overall: number | null;
  rating_food: number | null;
  rating_service: number | null;
  rating_atmosphere: number | null;
  rating_cost_performance: number | null;
  rating_drinks: number | null;
  visit_date: string | null;
  review_comment: string | null;
  notes: string | null;
  thumbnail_url: string | null;
  photo_count: number;
  created_at: string | null;
  updated_at: string | null;
  photos?: PhotoMeta[];
}

export interface RestaurantListResponse {
  total: number;
  page: number;
  per_page: number;
  items: Restaurant[];
}

export interface RestaurantFormData {
  name: string;
  nearest_station: string;
  genre_id: number | null;
  scene: string;
  stars: number | null;
  rating_overall: number | null;
  rating_food: number | null;
  rating_service: number | null;
  rating_atmosphere: number | null;
  rating_cost_performance: number | null;
  rating_drinks: number | null;
  visit_date: string;
  review_comment: string;
  notes: string;
}
