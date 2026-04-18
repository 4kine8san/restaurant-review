import client from "./client";
import type { Master } from "../types";

export async function listMasters(category?: string): Promise<Master[]> {
  const { data } = await client.get<{ items: Master[] }>("/masters/", {
    params: category ? { category } : undefined,
  });
  return data.items;
}

export async function verifyAdmin(password: string): Promise<boolean> {
  try {
    const { data } = await client.post<{ ok: boolean }>("/admin/verify/", { password });
    return data.ok;
  } catch {
    return false;
  }
}
