import { useNavigate } from "react-router-dom";
import type { Restaurant } from "../types";
import type { DisplayMode } from "../constants";
import StarDisplay from "./StarDisplay";
import RatingBadge from "./RatingBadge";

interface Props {
  restaurant: Restaurant;
  displayMode: DisplayMode;
  isAdmin: boolean;
  onDelete: (id: number) => void;
}

export default function RestaurantCard({ restaurant: r, displayMode, isAdmin, onDelete }: Props) {
  const navigate = useNavigate();

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm(`「${r.name}」を削除しますか?`)) onDelete(r.id);
  };

  if (displayMode === "grid") {
    return (
      <tr
        className="hover:bg-amber-50 cursor-pointer border-b"
        onClick={() => navigate(`/restaurants/${r.id}`)}
      >
        <td className="px-4 py-2 font-medium">{r.name}</td>
        <td className="px-4 py-2 text-sm text-gray-600">{r.nearest_station ?? "-"}</td>
        <td className="px-4 py-2 text-sm">{r.genre_name ?? "-"}</td>
        <td className="px-4 py-2">
          <StarDisplay value={r.stars} />
        </td>
        <td className="px-4 py-2">
          <RatingBadge value={r.rating_overall} />
        </td>
        <td className="px-4 py-2 text-sm text-gray-500">{r.visit_date ?? "-"}</td>
        {isAdmin && (
          <td className="px-4 py-2">
            <button type="button" onClick={handleDelete} className="text-red-500 hover:text-red-700 text-sm">
              削除
            </button>
          </td>
        )}
      </tr>
    );
  }

  const thumbSize = displayMode === "large" ? "h-48" : displayMode === "medium" ? "h-36" : "h-24";

  return (
    <div
      className="bg-white/90 backdrop-blur-sm rounded-xl shadow-md overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
      onClick={() => navigate(`/restaurants/${r.id}`)}
    >
      {r.thumbnail_url ? (
        <img src={r.thumbnail_url} alt={r.name} className={`w-full ${thumbSize} object-cover`} />
      ) : (
        <div
          className={`w-full ${thumbSize} bg-gray-200 flex items-center justify-center text-gray-400 text-3xl`}
        >
          🍽
        </div>
      )}
      <div className="p-3 space-y-1">
        <h3 className="font-semibold text-gray-800 truncate">{r.name}</h3>
        {displayMode !== "small" && (
          <>
            <p className="text-xs text-gray-500">
              {r.nearest_station ?? ""} {r.genre_name ? `・${r.genre_name}` : ""}
            </p>
            <div className="flex items-center gap-2 flex-wrap">
              <StarDisplay value={r.stars} />
              <RatingBadge value={r.rating_overall} />
            </div>
            {r.visit_date && <p className="text-xs text-gray-400">{r.visit_date}</p>}
          </>
        )}
        {isAdmin && (
          <div className="flex justify-end">
            <button type="button" onClick={handleDelete} className="text-red-500 hover:text-red-700 text-xs">
              削除
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
