import { useEffect, useState, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { listRestaurants, deleteRestaurant, exportUrl } from "../api/restaurants";
import { listMasters } from "../api/masters";
import type { Restaurant, Master } from "../types";
import { DISPLAY_MODES, ORDER_OPTIONS } from "../constants";
import type { DisplayMode } from "../constants";
import { useListState } from "../hooks/useListState";
import RestaurantCard from "../components/RestaurantCard";
import AdminLoginModal from "../components/AdminLoginModal";

interface Props {
  isAdmin: boolean;
  onLogout: () => void;
  onLogin: (password: string) => Promise<boolean>;
}

export default function ListPage({ isAdmin, onLogout, onLogin }: Props) {
  const navigate = useNavigate();
  const { state, update } = useListState();
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [total, setTotal] = useState(0);
  const [genres, setGenres] = useState<Master[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [keyword, setKeyword] = useState(state.params.keyword ?? "");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await listRestaurants(state.params);
      setRestaurants(result.items);
      setTotal(result.total);
      if (result.page !== (state.params.page ?? 1)) {
        update({ params: { ...state.params, page: result.page } });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "データ取得に失敗しました");
    } finally {
      setLoading(false);
    }
  }, [state.params]);

  useEffect(() => {
    listMasters("genre")
      .then(setGenres)
      .catch(() => setError("ジャンルの取得に失敗しました"));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    update({ params: { ...state.params, keyword, page: 1 } });
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteRestaurant(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "削除に失敗しました");
    }
  };

  const totalPages = Math.ceil(total / 50);

  const displayModeLabels: Record<DisplayMode, string> = {
    large: "大",
    medium: "中",
    small: "小",
    grid: "一覧",
  };

  return (
    <div className="min-h-screen">
      {showLogin && <AdminLoginModal onLogin={onLogin} onClose={() => setShowLogin(false)} />}

      <header className="bg-white/80 backdrop-blur-sm shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <h1 className="text-xl font-bold text-amber-800 shrink-0">🍽 レストランレビュー</h1>

          <form onSubmit={handleSearch} className="flex gap-2 flex-1 max-w-lg">
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="店名・駅名・訪問年月で検索"
              className="flex-1 border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
            <button
              type="submit"
              className="px-4 py-1.5 bg-amber-600 text-white rounded-lg text-sm hover:bg-amber-700"
            >
              検索
            </button>
            {(keyword || state.params.genre_id) && (
              <button
                type="button"
                onClick={() => {
                  setKeyword("");
                  update({ params: { page: 1, order: state.params.order } });
                }}
                className="px-3 py-1.5 text-gray-500 hover:text-gray-700 text-sm"
              >
                クリア
              </button>
            )}
          </form>

          <div className="flex items-center gap-2">
            {isAdmin ? (
              <>
                <button
                  type="button"
                  onClick={() => navigate("/restaurants/new")}
                  className="px-3 py-1.5 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700"
                >
                  + 新規登録
                </button>
                <button type="button" onClick={onLogout} className="text-sm text-gray-500 hover:text-gray-700">
                  管理者終了
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={() => setShowLogin(true)}
                className="px-3 py-1.5 border border-amber-600 text-amber-600 rounded-lg text-sm hover:bg-amber-50"
              >
                管理者モード
              </button>
            )}
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 pb-2 flex items-center gap-4 flex-wrap">
          <select
            value={state.params.genre_id ?? ""}
            onChange={(e) =>
              update({
                params: {
                  ...state.params,
                  genre_id: e.target.value ? Number(e.target.value) : null,
                  page: 1,
                },
              })
            }
            className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
          >
            <option value="">ジャンル: すべて</option>
            {genres.map((g) => (
              <option key={g.id} value={g.id}>
                {g.value}
              </option>
            ))}
          </select>

          <select
            value={state.params.order ?? "created_at_desc"}
            onChange={(e) =>
              update({ params: { ...state.params, order: e.target.value, page: 1 } })
            }
            className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
          >
            {ORDER_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>

          <div className="flex rounded-lg border border-gray-300 overflow-hidden">
            {DISPLAY_MODES.map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => update({ displayMode: mode })}
                className={`px-3 py-1 text-sm ${state.displayMode === mode ? "bg-amber-600 text-white" : "hover:bg-gray-100"}`}
              >
                {displayModeLabels[mode]}
              </button>
            ))}
          </div>

          <div className="ml-auto flex items-center gap-2">
            <span className="text-sm text-gray-500">{total}件</span>
            <a
              href={exportUrl(state.params, "csv")}
              className="text-xs text-amber-700 hover:underline"
            >
              CSV
            </a>
            <a
              href={exportUrl(state.params, "json")}
              className="text-xs text-amber-700 hover:underline"
            >
              JSON
            </a>
            <Link
              to="/chart"
              className="text-xs text-amber-700 hover:underline"
            >
              グラフ
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12 text-gray-400">読み込み中...</div>
        ) : restaurants.length === 0 ? (
          <div className="text-center py-12 text-gray-400">レストランが見つかりません</div>
        ) : state.displayMode === "grid" ? (
          <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-amber-50">
                <tr>
                  <th className="px-4 py-2 text-left">店名</th>
                  <th className="px-4 py-2 text-left">最寄り駅</th>
                  <th className="px-4 py-2 text-left">ジャンル</th>
                  <th className="px-4 py-2 text-left">星</th>
                  <th className="px-4 py-2 text-left">総合</th>
                  <th className="px-4 py-2 text-left">訪問日</th>
                  {isAdmin && <th className="px-4 py-2 text-left">操作</th>}
                </tr>
              </thead>
              <tbody>
                {restaurants.map((r) => (
                  <RestaurantCard
                    key={r.id}
                    restaurant={r}
                    displayMode="grid"
                    isAdmin={isAdmin}
                    onDelete={handleDelete}
                  />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div
            className={`grid gap-4 ${
              state.displayMode === "large"
                ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3"
                : state.displayMode === "medium"
                  ? "grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
                  : "grid-cols-3 sm:grid-cols-4 lg:grid-cols-6"
            }`}
          >
            {restaurants.map((r) => (
              <RestaurantCard
                key={r.id}
                restaurant={r}
                displayMode={state.displayMode}
                isAdmin={isAdmin}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex justify-center gap-2 mt-8">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => update({ params: { ...state.params, page: p } })}
                className={`w-8 h-8 rounded-lg text-sm ${
                  (state.params.page ?? 1) === p
                    ? "bg-amber-600 text-white"
                    : "bg-white hover:bg-amber-50 border"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
