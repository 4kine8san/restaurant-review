"""
Google Takeout インポートスクリプト

事前準備:
  - バックエンドサーバーを起動しておく (http://127.0.0.1:8000)
  - takeout/ フォルダをプロジェクトルートに配置する

実行方法:
  python tools/import_google_takeout.py [--dry-run] [--skip-photos]

オプション:
  --dry-run       DBへの書き込みを行わず、インポート内容のみ確認する
  --skip-photos   写真のアップロードをスキップする
"""

import json
import math
import sys
from datetime import datetime
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8") # type: ignore

# ──────────────────────────── 設定 ────────────────────────────

API_BASE = "http://127.0.0.1:8000/api"

TAKEOUT_DIR = Path(__file__).parent.parent / "takeout"
REVIEWS_JSON = TAKEOUT_DIR / "マップ（マイプレイス）" / "クチコミ.json"
PHOTOS_BASE = TAKEOUT_DIR / "Google フォト"

# 写真マッチング条件
GPS_MATCH_METERS = 150   # レビューのGPS座標から何m以内の写真を紐づけるか
DATE_MATCH_DAYS = 180    # レビュー日から何日以内（前）の写真を紐づけるか
MAX_PHOTOS_PER_REVIEW = 10  # 1件あたり最大アップロード枚数

# 利用シーンのマッピング
SCENE_MAP = {
    "ランチ": "昼",
    "ディナー": "夜",
    "朝食": "朝",
    "ブランチ": "昼",
    "テイクアウト": "持ち帰り",
    "持ち帰り": "持ち帰り",
    "デリバリー": "その他",
}

# ──────────────────────────── ユーティリティ ────────────────────────────

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """2点間の距離をメートルで返す（Haversine公式）"""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def log(msg: str) -> None:
    print(msg, flush=True, file=sys.stdout)


# ──────────────────────────── レビューのパース ────────────────────────────

def parse_review(feature: dict) -> dict:
    props = feature["properties"]
    if "location" not in props:
        raise ValueError("location フィールドがありません（削除済みの場所）")
    coords = feature["geometry"]["coordinates"]  # [lng, lat]

    dt = datetime.fromisoformat(props["date"].replace("Z", "+00:00"))
    visit_date = dt.strftime("%Y/%m/%d")

    questions = {q["question"]: q for q in props.get("questions", [])}

    # 利用シーン（食事の種類 → 注文の種類 の順で確認）
    scene = ""
    for key in ("食事の種類", "注文の種類"):
        raw = questions.get(key, {}).get("selected_option", "")
        scene = SCENE_MAP.get(raw, "")
        if scene:
            break

    def get_rating(key: str) -> float | None:
        r = questions.get(key, {}).get("rating")
        return float(r) if r is not None else None

    rating_food = get_rating("食事")
    rating_service = get_rating("サービス")
    rating_atmosphere = get_rating("雰囲気")

    # 総合評価（入力済みのサブ評価の平均、小数点第2位以下四捨五入）
    subs = [v for v in [rating_food, rating_service, rating_atmosphere] if v is not None]
    rating_overall = round(sum(subs) / len(subs) * 10) / 10 if subs else None

    # 備考（Googleのみにある情報を保存）
    extras = []
    for key in ("1 人あたりの料金", "おすすめの料理", "騒音レベル", "座席の種類"):
        q = questions.get(key, {})
        val = q.get("selected_option") or q.get("text", "")
        if val:
            extras.append(f"{key}: {val}")
    notes = "\n".join(extras)

    return {
        "name": props["location"]["name"],
        "nearest_station": "",
        "genre_id": None,
        "scene": scene,
        "stars": props.get("five_star_rating_published"),
        "rating_overall": rating_overall,
        "rating_food": rating_food,
        "rating_service": rating_service,
        "rating_atmosphere": rating_atmosphere,
        "rating_cost_performance": None,
        "rating_drinks": None,
        "visit_date": visit_date,
        "review_comment": props.get("review_text_published", ""),
        "notes": notes,
        # インポート処理用（APIには送らない）
        "_lat": coords[1],
        "_lng": coords[0],
        "_dt": dt,
    }


# ──────────────────────────── 写真インデックスの構築 ────────────────────────────

def build_photo_index() -> list[tuple[Path, float, float, int]]:
    """
    Google フォトの年別フォルダを走査し、GPS付き写真のリストを返す。
    戻り値: [(画像パス, 緯度, 経度, 撮影UNIXタイムスタンプ), ...]
    """
    photos = []
    if not PHOTOS_BASE.exists():
        log("警告: Google フォトフォルダが見つかりません。写真のインポートをスキップします。")
        return photos

    year_dirs = sorted(PHOTOS_BASE.glob("* 年の写真"))
    log(f"写真フォルダ数: {len(year_dirs)}")

    for year_dir in year_dirs:
        for meta_path in year_dir.glob("*.json"):
            try:
                with open(meta_path, encoding="utf-8") as f:
                    meta = json.load(f)

                geo = meta.get("geoData") or {}
                lat = geo.get("latitude", 0.0)
                lng = geo.get("longitude", 0.0)
                if lat == 0.0 and lng == 0.0:
                    continue  # GPS なし

                taken_ts = int(meta.get("photoTakenTime", {}).get("timestamp", 0))
                if taken_ts == 0:
                    continue

                title = meta.get("title", "")
                img_path = meta_path.parent / title
                if not img_path.exists():
                    # ファイル名が長すぎて短縮されているケースを探す
                    stem = Path(title).stem[:40]
                    candidates = list(meta_path.parent.glob(f"{stem}*"))
                    candidates = [p for p in candidates if not p.suffix == ".json"]
                    if not candidates:
                        continue
                    img_path = candidates[0]

                photos.append((img_path, lat, lng, taken_ts))
            except Exception:
                continue

    return photos


def find_matching_photos(
    review_lat: float,
    review_lng: float,
    review_dt: datetime,
    all_photos: list,
) -> list[Path]:
    """
    レビューのGPS座標・日時に近い写真を返す。
    写真の撮影日はレビュー投稿日より前（＝訪問時に撮影）を想定。
    """
    review_ts = review_dt.timestamp()
    max_delta = DATE_MATCH_DAYS * 86_400

    matched = []
    for img_path, lat, lng, taken_ts in all_photos:
        dist = haversine(review_lat, review_lng, lat, lng)
        if dist > GPS_MATCH_METERS:
            continue
        delta = review_ts - taken_ts  # 正 = 写真がレビューより前
        if delta < 0 or delta > max_delta:
            continue
        matched.append((img_path, dist, delta))

    matched.sort(key=lambda x: (x[1], x[2]))
    return [p for p, _, _ in matched[:MAX_PHOTOS_PER_REVIEW]]


# ──────────────────────────── API呼び出し ────────────────────────────

def create_restaurant(payload: dict) -> int:
    resp = requests.post(f"{API_BASE}/restaurants/", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["id"]


def upload_photo(restaurant_id: int, img_path: Path) -> None:
    suffix = img_path.suffix.lower()
    content_type = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"
    with open(img_path, "rb") as f:
        resp = requests.post(
            f"{API_BASE}/photos/",
            data={"restaurant_id": restaurant_id},
            files={"photo": (img_path.name, f, content_type)},
            timeout=60,
        )
    resp.raise_for_status()


# ──────────────────────────── メイン処理 ────────────────────────────

def main() -> None:
    dry_run = "--dry-run" in sys.argv
    skip_photos = "--skip-photos" in sys.argv

    if dry_run:
        log("【DRY RUN モード】DBへの書き込みは行いません\n")

    # レビューの読み込み
    if not REVIEWS_JSON.exists():
        log(f"エラー: {REVIEWS_JSON} が見つかりません")
        sys.exit(1)

    with open(REVIEWS_JSON, encoding="utf-8") as f:
        features = json.load(f)["features"]
    log(f"レビュー数: {len(features)} 件\n")

    # 写真インデックスの構築
    all_photos: list = []
    if not skip_photos:
        log("写真メタデータを収集中...")
        all_photos = build_photo_index()
        log(f"GPS付き写真: {len(all_photos)} 枚\n")

    # API疎通確認 + 既存レストラン名の取得（重複スキップ用）
    existing_names: set[str] = set()
    if not dry_run:
        try:
            r = requests.get(f"{API_BASE}/restaurants/?per_page=9999", timeout=10)
            r.raise_for_status()
            data = r.json()
            existing_names = {item["name"] for item in data.get("items", [])}
            if existing_names:
                log(f"既存レストラン {len(existing_names)} 件を検出。同名はスキップします。\n")
        except requests.ConnectionError:
            log(f"エラー: APIサーバーに接続できません ({API_BASE})")
            log("バックエンドサーバーを起動してから再実行してください。")
            sys.exit(1)

    success = 0
    skipped = 0
    photo_total = 0
    errors: list[tuple[str, str]] = []

    for i, feature in enumerate(features, 1):
        name = feature["properties"].get("location", {}).get("name", f"不明#{i}")
        try:
            review = parse_review(feature)

            if not dry_run and review["name"] in existing_names:
                log(f"[{i:3d}/{len(features)}] SKIP {name} (既存)")
                skipped += 1
                continue

            matched_photos = find_matching_photos(
                review["_lat"], review["_lng"], review["_dt"], all_photos
            )

            if dry_run:
                log(
                    f"[{i:3d}/{len(features)}] {name} "
                    f"| 星:{review['stars']} 訪問:{review['visit_date']} "
                    f"シーン:{review['scene'] or '-'} "
                    f"料理:{review['rating_food']} サービス:{review['rating_service']} 雰囲気:{review['rating_atmosphere']} "
                    f"写真:{len(matched_photos)}枚"
                )
                success += 1
                continue

            # レストランを登録
            payload = {k: v for k, v in review.items() if not k.startswith("_")}
            restaurant_id = create_restaurant(payload)

            # 写真をアップロード
            uploaded = 0
            for img_path in matched_photos:
                try:
                    upload_photo(restaurant_id, img_path)
                    uploaded += 1
                except Exception as e:
                    log(f"  写真アップロード失敗 ({img_path.name}): {e}")

            log(f"[{i:3d}/{len(features)}] OK {name} (写真: {uploaded}枚)")
            success += 1
            photo_total += uploaded

        except Exception as e:
            log(f"[{i:3d}/{len(features)}] NG {name}: {e}")
            errors.append((name, str(e)))

    # 結果サマリー
    log(f"\n{'='*50}")
    log(f"完了: 成功 {success}件 / スキップ {skipped}件 / エラー {len(errors)}件")
    if not dry_run and not skip_photos:
        log(f"アップロード写真: 計 {photo_total}枚")
    if errors:
        log("\nエラー一覧:")
        for name, err in errors:
            log(f"  - {name}: {err}")
    if not dry_run:
        log("\n※ ジャンル・CP・酒ドリンク・最寄り駅は一覧画面から補完してください。")


if __name__ == "__main__":
    main()
