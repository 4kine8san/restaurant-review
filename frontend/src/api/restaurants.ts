import client from "./client";
import type { Restaurant, RestaurantListResponse, RestaurantFormData } from "../types";

export interface ListParams {
  keyword?: string;
  genre_id?: number | null;
  order?: string;
  page?: number;
}

export async function listRestaurants(params: ListParams): Promise<RestaurantListResponse> {
  const { data } = await client.get<RestaurantListResponse>("/restaurants/", { params });
  return data;
}

export async function getRestaurant(id: number): Promise<Restaurant> {
  const { data } = await client.get<Restaurant>(`/restaurants/${id}/`);
  return data;
}

export async function createRestaurant(form: RestaurantFormData): Promise<Restaurant> {
  const { data } = await client.post<Restaurant>("/restaurants/", form);
  return data;
}

export async function updateRestaurant(
  id: number,
  form: Partial<RestaurantFormData>
): Promise<Restaurant> {
  const { data } = await client.put<Restaurant>(`/restaurants/${id}/`, form);
  return data;
}

export async function deleteRestaurant(id: number): Promise<void> {
  await client.delete(`/restaurants/${id}/`);
}

export function exportUrl(params: ListParams, format: "csv" | "json"): string {
  const q = new URLSearchParams();
  if (params.keyword) q.set("keyword", params.keyword);
  if (params.genre_id != null) q.set("genre_id", String(params.genre_id));
  q.set("format", format);
  return `/api/restaurants/export/?${q.toString()}`;
}
