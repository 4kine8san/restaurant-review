export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const SCENES = ["朝", "昼", "夜", "持ち帰り", "その他"] as const;
export type Scene = (typeof SCENES)[number];

export const RATING_OPTIONS = Array.from({ length: 41 }, (_, i) =>
  Math.round((5.0 - i * 0.1) * 10) / 10
);
export const STAR_OPTIONS = [5, 4, 3, 2, 1];

export const DISPLAY_MODES = ["large", "medium", "small", "grid"] as const;
export type DisplayMode = (typeof DISPLAY_MODES)[number];

export const ORDER_OPTIONS = [
  { value: "created_at_desc", label: "登録日（新しい順）" },
  { value: "name_asc", label: "名前（昇順）" },
  { value: "rating_desc", label: "評価（高い順）" },
  { value: "visit_date_desc", label: "訪問日（新しい順）" },
] as const;
