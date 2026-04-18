export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const SCENES = ["朝", "昼", "夜", "持ち帰り", "その他"] as const;
export type Scene = (typeof SCENES)[number];

export const RATING_OPTIONS = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0];
export const STAR_OPTIONS = [1, 2, 3, 4, 5];

export const DISPLAY_MODES = ["large", "medium", "small", "grid"] as const;
export type DisplayMode = (typeof DISPLAY_MODES)[number];

export const ORDER_OPTIONS = [
  { value: "created_at_desc", label: "登録日（新しい順）" },
  { value: "name_asc", label: "名前（昇順）" },
  { value: "rating_desc", label: "評価（高い順）" },
  { value: "visit_date_desc", label: "訪問日（新しい順）" },
] as const;
