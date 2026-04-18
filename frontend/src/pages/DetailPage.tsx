import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getRestaurant } from "../api/restaurants";
import { thumbUrl } from "../api/photos";
import type { Restaurant } from "../types";
import StarDisplay from "../components/StarDisplay";
import RatingBadge from "../components/RatingBadge";

interface Props {
  isAdmin: boolean;
}

const RATING_LABELS: { key: keyof Restaurant; label: string }[] = [
  { key: "rating_overall", label: "総合" },
  { key: "rating_food", label: "料理" },
  { key: "rating_service", label: "サービス" },
  { key: "rating_atmosphere", label: "雰囲気" },
  { key: "rating_cost_performance", label: "CP" },
  { key: "rating_drinks", label: "酒・ドリンク" },
];

export default function DetailPage({ isAdmin }: Props) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [restaurant, setRestaurant] = useState<Restaurant | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getRestaurant(Number(id))
      .then(setRestaurant)
      .catch(() => setError("データの取得に失敗しました"));
  }, [id]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  if (!restaurant) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        読み込み中...
      </div>
    );
  }

  const r = restaurant;

  return (
    <div className="min-h-screen">
      <header className="bg-white/80 backdrop-blur-sm shadow-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate(-1)} className="text-amber-600 hover:text-amber-800">
              ← 戻る
            </button>
            <h1 className="text-lg font-bold text-amber-800">{r.name}</h1>
          </div>
          {isAdmin && (
            <button
              onClick={() => navigate(`/restaurants/${r.id}/edit`)}
              className="px-4 py-1.5 bg-amber-600 text-white rounded-lg text-sm hover:bg-amber-700"
            >
              編集
            </button>
          )}
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow p-6">
          <div className="flex flex-wrap gap-6">
            {r.thumbnail_url && (
              <img
                src={r.thumbnail_url}
                alt={r.name}
                className="w-48 h-48 object-cover rounded-lg"
              />
            )}
            <div className="flex-1 space-y-3">
              <h2 className="text-2xl font-bold text-gray-800">{r.name}</h2>
              <div className="flex flex-wrap gap-3 text-sm text-gray-600">
                {r.nearest_station && <span>📍 {r.nearest_station}</span>}
                {r.genre_name && <span>🍴 {r.genre_name}</span>}
                {r.scene && <span>🕐 {r.scene}</span>}
                {r.visit_date && <span>📅 {r.visit_date}</span>}
              </div>
              <div className="flex items-center gap-3">
                <StarDisplay value={r.stars} />
                <div className="flex flex-wrap gap-2">
                  {RATING_LABELS.map(({ key, label }) => (
                    <RatingBadge key={key} value={r[key] as number | null} label={label} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {(r.review_comment || r.notes) && (
          <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow p-6 space-y-4">
            {r.review_comment && (
              <div>
                <h3 className="font-semibold text-gray-700 mb-2">レビューコメント</h3>
                <p className="text-gray-700 whitespace-pre-wrap text-sm">{r.review_comment}</p>
              </div>
            )}
            {r.notes && (
              <div>
                <h3 className="font-semibold text-gray-700 mb-2">備考</h3>
                <p className="text-gray-700 whitespace-pre-wrap text-sm">{r.notes}</p>
              </div>
            )}
          </div>
        )}

        {r.photos && r.photos.length > 0 && (
          <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow p-6">
            <h3 className="font-semibold text-gray-700 mb-4">写真 ({r.photos.length}枚)</h3>
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
              {r.photos.map((p) => (
                <img
                  key={p.id}
                  src={thumbUrl(p.id)}
                  alt="写真"
                  className="w-full aspect-square object-cover rounded-lg"
                />
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
