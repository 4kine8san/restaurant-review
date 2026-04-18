import { useRef, useState } from "react";
import type { PhotoMeta } from "../types";
import {
  uploadPhoto,
  rotatePhoto,
  reorderPhotos,
  deletePhoto,
  photoUrl,
  thumbUrl,
} from "../api/photos";

interface Props {
  restaurantId: number;
  photos: PhotoMeta[];
  onChange: (photos: PhotoMeta[]) => void;
}

export default function PhotoManager({ restaurantId, photos, onChange }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const result = await uploadPhoto(restaurantId, file);
      onChange([...photos, { id: result.id, sort_order: result.sort_order, rotation: 0 }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "アップロードに失敗しました");
    } finally {
      setLoading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const handleRotate = async (photo: PhotoMeta) => {
    try {
      await rotatePhoto(photo.id);
      const next = (photo.rotation + 90) % 360;
      onChange(photos.map((p) => (p.id === photo.id ? { ...p, rotation: next } : p)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "回転に失敗しました");
    }
  };

  const handleDelete = async (photo: PhotoMeta) => {
    if (!confirm("この写真を削除しますか?")) return;
    try {
      await deletePhoto(photo.id);
      const updated = photos
        .filter((p) => p.id !== photo.id)
        .map((p, i) => ({ ...p, sort_order: i }));
      onChange(updated);
      if (updated.length > 0) await reorderPhotos(updated.map((p) => p.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "削除に失敗しました");
    }
  };

  const movePhoto = async (index: number, direction: -1 | 1) => {
    const target = index + direction;
    if (target < 0 || target >= photos.length) return;
    const updated = [...photos];
    [updated[index], updated[target]] = [updated[target], updated[index]];
    const reordered = updated.map((p, i) => ({ ...p, sort_order: i }));
    onChange(reordered);
    try {
      await reorderPhotos(reordered.map((p) => p.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "並び替えに失敗しました");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={loading}
          className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 text-sm"
        >
          {loading ? "アップロード中..." : "写真を追加"}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleUpload}
        />
      </div>

      {error && <p className="text-red-500 text-sm">{error}</p>}

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {photos.map((photo, i) => (
          <div
            key={photo.id}
            className="relative group border rounded-lg overflow-hidden bg-gray-50"
          >
            <img
              src={thumbUrl(photo.id)}
              alt={`写真${i + 1}`}
              className="w-full aspect-square object-cover cursor-pointer"
              onClick={() => setPreview(photo.id)}
            />
            {i === 0 && (
              <span className="absolute top-1 left-1 bg-amber-600 text-white text-xs px-1.5 py-0.5 rounded">
                表紙
              </span>
            )}
            <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white p-1 flex justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => movePhoto(i, -1)}
                className="p-1 hover:text-amber-300"
                title="前へ"
              >
                ◀
              </button>
              <button
                onClick={() => handleRotate(photo)}
                className="p-1 hover:text-amber-300"
                title="回転"
              >
                ↻
              </button>
              <button
                onClick={() => movePhoto(i, 1)}
                className="p-1 hover:text-amber-300"
                title="後へ"
              >
                ▶
              </button>
              <button
                onClick={() => handleDelete(photo)}
                className="p-1 hover:text-red-400"
                title="削除"
              >
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>

      {preview !== null && (
        <div
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-50"
          onClick={() => setPreview(null)}
        >
          <img
            src={photoUrl(preview)}
            alt="原寸表示"
            className="max-h-[90vh] max-w-[90vw] object-contain"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  );
}
