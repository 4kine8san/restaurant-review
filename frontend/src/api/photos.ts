import client from "./client";
import { API_BASE_URL } from "../constants";

export async function uploadPhoto(
  restaurantId: number,
  file: File
): Promise<{ id: number; sort_order: number }> {
  const form = new FormData();
  form.append("restaurant_id", String(restaurantId));
  form.append("photo", file);
  const { data } = await client.post("/photos/", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function rotatePhoto(id: number): Promise<void> {
  await client.put(`/photos/${id}/rotate/`);
}

export async function reorderPhotos(photoIds: number[]): Promise<void> {
  await client.put("/photos/reorder/", { photo_ids: photoIds });
}

export async function deletePhoto(id: number): Promise<void> {
  await client.delete(`/photos/${id}/`);
}

export function photoUrl(id: number): string {
  return `${API_BASE_URL}/photos/${id}/`;
}

export function thumbUrl(id: number): string {
  return `${API_BASE_URL}/photos/${id}/thumb/`;
}
