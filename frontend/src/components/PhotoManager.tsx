import { useRef, useState } from "react";
import { createPortal } from "react-dom";
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
  const [progress, setProgress] = useState("");
  const [isFileDragging, setIsFileDragging] = useState(false);

  // 写真並び替えドラッグ用の状態
  const [sortDragIndex, setSortDragIndex] = useState<number | null>(null);
  const [sortDragOver, setSortDragOver] = useState<number | null>(null);
  const isSortingRef = useRef(false); // ファイルドロップゾーンとの区別用

  // ---- アップロード ----

  const uploadFiles = async (files: File[]) => {
    const images = files.filter((f) => f.type.startsWith("image/"));
    if (images.length === 0) {
      setError("画像ファイルを選択してください");
      return;
    }
    setLoading(true);
    setError("");
    let current = [...photos];
    for (let i = 0; i < images.length; i++) {
      if (images.length > 1) setProgress(`${i + 1} / ${images.length}`);
      try {
        const result = await uploadPhoto(restaurantId, images[i]);
        current = [...current, { id: result.id, sort_order: result.sort_order, rotation: 0 }];
        onChange(current);
      } catch (err) {
        setError(
          images.length > 1
            ? `${images[i].name}: ${err instanceof Error ? err.message : "アップロードに失敗しました"}`
            : err instanceof Error ? err.message : "アップロードに失敗しました"
        );
      }
    }
    setLoading(false);
    setProgress("");
  };

  const handleInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    await uploadFiles(files);
    if (fileRef.current) fileRef.current.value = "";
  };

  // ドロップゾーンへのファイルドラッグ（写真並び替えドラッグ中は無視）
  const handleZoneDragOver = (e: React.DragEvent) => {
    if (isSortingRef.current) return;
    e.preventDefault();
    setIsFileDragging(true);
  };
  const handleZoneDragLeave = (e: React.DragEvent) => {
    if (!e.currentTarget.contains(e.relatedTarget as Node)) setIsFileDragging(false);
  };
  const handleZoneDrop = async (e: React.DragEvent) => {
    if (isSortingRef.current) return;
    e.preventDefault();
    setIsFileDragging(false);
    await uploadFiles(Array.from(e.dataTransfer.files));
  };

  // ---- 写真操作 ----

  const handleRotate = async (photo: PhotoMeta) => {
    try {
      await rotatePhoto(photo.id);
      onChange(photos.map((p) => (p.id === photo.id ? { ...p, rotation: (photo.rotation + 90) % 360 } : p)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "回転に失敗しました");
    }
  };

  const handleDelete = async (photo: PhotoMeta) => {
    if (!confirm("この写真を削除しますか?")) return;
    try {
      await deletePhoto(photo.id);
      const updated = photos.filter((p) => p.id !== photo.id).map((p, i) => ({ ...p, sort_order: i }));
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

  // ---- 写真並び替えドラッグ ----

  const onSortDragStart = (e: React.DragEvent, index: number) => {
    isSortingRef.current = true;
    setSortDragIndex(index);
    e.dataTransfer.effectAllowed = "move";
  };

  const onSortDragOver = (e: React.DragEvent, index: number) => {
    if (!isSortingRef.current) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setSortDragOver(index);
  };

  const onSortDrop = async (e: React.DragEvent, targetIndex: number) => {
    e.preventDefault();
    if (sortDragIndex === null || sortDragIndex === targetIndex) return;
    const updated = [...photos];
    const [moved] = updated.splice(sortDragIndex, 1);
    updated.splice(targetIndex, 0, moved);
    const reordered = updated.map((p, i) => ({ ...p, sort_order: i }));
    onChange(reordered);
    setSortDragIndex(null);
    setSortDragOver(null);
    isSortingRef.current = false;
    try {
      await reorderPhotos(reordered.map((p) => p.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "並び替えに失敗しました");
    }
  };

  const onSortDragEnd = () => {
    isSortingRef.current = false;
    setSortDragIndex(null);
    setSortDragOver(null);
  };

  return (
    <div className="space-y-4">
      {/* アップロードゾーン */}
      <div
        onDragOver={handleZoneDragOver}
        onDragLeave={handleZoneDragLeave}
        onDrop={handleZoneDrop}
        onClick={() => !loading && fileRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-6 flex flex-col items-center gap-2 cursor-pointer transition-colors
          ${isFileDragging ? "border-amber-500 bg-amber-50" : "border-gray-300 bg-gray-50 hover:border-amber-400 hover:bg-amber-50/50"}
          ${loading ? "cursor-not-allowed opacity-60" : ""}`}
      >
        <span className="text-3xl">📷</span>
        {loading ? (
          <span className="text-sm text-gray-600">
            アップロード中{progress ? `… ${progress}` : "…"}
          </span>
        ) : (
          <>
            <span className="text-sm font-medium text-gray-700">
              クリックまたはドラッグ&ドロップで写真を追加
            </span>
            <span className="text-xs text-gray-400">複数選択可</span>
          </>
        )}
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          multiple
          className="hidden"
          onChange={handleInputChange}
        />
      </div>

      {error && <p className="text-red-500 text-sm">{error}</p>}

      {photos.length > 0 && (
        <p className="text-xs text-gray-400">ドラッグで並び替えできます</p>
      )}

      {/* 写真グリッド */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {photos.map((photo, i) => {
          const isDraggingThis = sortDragIndex === i;
          const isDropTarget = sortDragOver === i && sortDragIndex !== i;
          return (
            <div
              key={photo.id}
              draggable
              onDragStart={(e) => onSortDragStart(e, i)}
              onDragOver={(e) => onSortDragOver(e, i)}
              onDrop={(e) => onSortDrop(e, i)}
              onDragEnd={onSortDragEnd}
              className={[
                "relative group border rounded-lg overflow-hidden bg-gray-50 cursor-grab active:cursor-grabbing transition-all",
                isDraggingThis ? "opacity-40 scale-95" : "",
                isDropTarget ? "ring-2 ring-amber-500 scale-105" : "",
              ].filter(Boolean).join(" ")}
            >
              <img
                src={thumbUrl(photo.id)}
                alt={`写真${i + 1}`}
                className="w-full aspect-square object-cover"
                onClick={() => !isSortingRef.current && setPreview(photo.id)}
                draggable={false}
              />
              {i === 0 && (
                <span className="absolute top-1 left-1 bg-amber-600 text-white text-xs px-1.5 py-0.5 rounded">
                  表紙
                </span>
              )}
              <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white p-1 flex justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  type="button"
                  onClick={() => movePhoto(i, -1)}
                  className="p-1 hover:text-amber-300"
                  title="前へ"
                >
                  ◀
                </button>
                <button
                  type="button"
                  onClick={() => handleRotate(photo)}
                  className="p-1 hover:text-amber-300"
                  title="回転"
                >
                  ↻
                </button>
                <button
                  type="button"
                  onClick={() => movePhoto(i, 1)}
                  className="p-1 hover:text-amber-300"
                  title="後へ"
                >
                  ▶
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(photo)}
                  className="p-1 hover:text-red-400"
                  title="削除"
                >
                  ✕
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {preview !== null &&
        createPortal(
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
          </div>,
          document.body
        )}
    </div>
  );
}
