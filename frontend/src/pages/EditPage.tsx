import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getRestaurant, createRestaurant, updateRestaurant } from "../api/restaurants";
import { listMasters } from "../api/masters";
import type { RestaurantFormData, Master, PhotoMeta } from "../types";
import { SCENES, RATING_OPTIONS, STAR_OPTIONS } from "../constants";
import PhotoManager from "../components/PhotoManager";

const EMPTY_FORM: RestaurantFormData = {
  name: "",
  nearest_station: "",
  genre_id: null,
  scene: "",
  stars: null,
  rating_overall: null,
  rating_food: null,
  rating_service: null,
  rating_atmosphere: null,
  rating_cost_performance: null,
  rating_drinks: null,
  visit_date: "",
  review_comment: "",
  notes: "",
};

function SelectField({
  label,
  value,
  onChange,
  options,
  nullable = true,
}: {
  label: string;
  value: number | null | string;
  onChange: (v: string) => void;
  options: { value: string | number; label: string }[];
  nullable?: boolean;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <select
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-400 text-sm"
      >
        {nullable && <option value="">-</option>}
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export default function EditPage() {
  const { id } = useParams<{ id: string }>();
  const isNew = id === "new";
  const navigate = useNavigate();

  const [form, setForm] = useState<RestaurantFormData>(EMPTY_FORM);
  const [photos, setPhotos] = useState<PhotoMeta[]>([]);
  const [genres, setGenres] = useState<Master[]>([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [restaurantId, setRestaurantId] = useState<number | null>(null);

  useEffect(() => {
    listMasters("genre")
      .then(setGenres)
      .catch(() => setError("ジャンルの取得に失敗しました"));
    if (!isNew && id) {
      getRestaurant(Number(id))
        .then((r) => {
          setForm({
            name: r.name,
            nearest_station: r.nearest_station ?? "",
            genre_id: r.genre_id,
            scene: r.scene ?? "",
            stars: r.stars,
            rating_overall: r.rating_overall,
            rating_food: r.rating_food,
            rating_service: r.rating_service,
            rating_atmosphere: r.rating_atmosphere,
            rating_cost_performance: r.rating_cost_performance,
            rating_drinks: r.rating_drinks,
            visit_date: r.visit_date ?? "",
            review_comment: r.review_comment ?? "",
            notes: r.notes ?? "",
          });
          setPhotos(r.photos ?? []);
          setRestaurantId(r.id);
        })
        .catch(() => setError("データの取得に失敗しました"));
    }
  }, [id, isNew]);

  const set = (key: keyof RestaurantFormData, value: unknown) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) {
      setError("店名は必須です");
      return;
    }
    setSaving(true);
    setError("");
    try {
      if (isNew) {
        const r = await createRestaurant(form);
        navigate(`/restaurants/${r.id}`, { replace: true });
      } else {
        await updateRestaurant(Number(id), form);
        navigate(-1);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存に失敗しました");
    } finally {
      setSaving(false);
    }
  };

  const ratingOptions = RATING_OPTIONS.map((v) => ({ value: v, label: String(v.toFixed(1)) }));
  const starOptions = STAR_OPTIONS.map((v) => ({ value: v, label: "★".repeat(v) }));

  return (
    <div className="min-h-screen">
      <header className="bg-white/80 backdrop-blur-sm shadow-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="text-amber-600 hover:text-amber-800">
            ← 戻る
          </button>
          <h1 className="text-lg font-bold text-amber-800">{isNew ? "新規登録" : "編集"}</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow p-6 space-y-4">
            <h2 className="font-semibold text-gray-700 border-b pb-2">基本情報</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                店名 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => set("name", e.target.value)}
                maxLength={200}
                required
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-400 text-sm"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">最寄り駅</label>
                <input
                  type="text"
                  value={form.nearest_station}
                  onChange={(e) => set("nearest_station", e.target.value)}
                  maxLength={100}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-400 text-sm"
                />
              </div>
              <SelectField
                label="ジャンル"
                value={form.genre_id}
                onChange={(v) => set("genre_id", v ? Number(v) : null)}
                options={genres.map((g) => ({ value: g.id, label: g.value }))}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <SelectField
                label="利用シーン"
                value={form.scene}
                onChange={(v) => set("scene", v)}
                options={SCENES.map((s) => ({ value: s, label: s }))}
              />
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">訪問年月日</label>
                <input
                  type="text"
                  value={form.visit_date}
                  onChange={(e) => set("visit_date", e.target.value)}
                  placeholder="例: 2026-04"
                  maxLength={20}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-400 text-sm"
                />
              </div>
            </div>
          </div>

          <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow p-6 space-y-4">
            <h2 className="font-semibold text-gray-700 border-b pb-2">評価</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <SelectField
                label="星"
                value={form.stars}
                onChange={(v) => set("stars", v ? Number(v) : null)}
                options={starOptions}
              />
              <SelectField
                label="総合評価"
                value={form.rating_overall}
                onChange={(v) => set("rating_overall", v ? Number(v) : null)}
                options={ratingOptions}
              />
              <SelectField
                label="料理"
                value={form.rating_food}
                onChange={(v) => set("rating_food", v ? Number(v) : null)}
                options={ratingOptions}
              />
              <SelectField
                label="サービス"
                value={form.rating_service}
                onChange={(v) => set("rating_service", v ? Number(v) : null)}
                options={ratingOptions}
              />
              <SelectField
                label="雰囲気"
                value={form.rating_atmosphere}
                onChange={(v) => set("rating_atmosphere", v ? Number(v) : null)}
                options={ratingOptions}
              />
              <SelectField
                label="CP"
                value={form.rating_cost_performance}
                onChange={(v) => set("rating_cost_performance", v ? Number(v) : null)}
                options={ratingOptions}
              />
              <SelectField
                label="酒・ドリンク"
                value={form.rating_drinks}
                onChange={(v) => set("rating_drinks", v ? Number(v) : null)}
                options={ratingOptions}
              />
            </div>
          </div>

          <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow p-6 space-y-4">
            <h2 className="font-semibold text-gray-700 border-b pb-2">コメント</h2>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                レビューコメント
              </label>
              <textarea
                value={form.review_comment}
                onChange={(e) => set("review_comment", e.target.value)}
                rows={4}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-400 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">備考</label>
              <textarea
                value={form.notes}
                onChange={(e) => set("notes", e.target.value)}
                rows={3}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-400 text-sm"
              />
            </div>
          </div>

          {restaurantId !== null && (
            <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow p-6 space-y-4">
              <h2 className="font-semibold text-gray-700 border-b pb-2">写真</h2>
              <PhotoManager restaurantId={restaurantId} photos={photos} onChange={setPhotos} />
            </div>
          )}

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="px-6 py-2 text-gray-600 hover:text-gray-800"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-8 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 font-medium"
            >
              {saving ? "保存中..." : "保存"}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
