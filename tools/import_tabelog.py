"""
食べログ エクスポートデータ インポートスクリプト

事前準備:
  - バックエンドサーバーを起動しておく (http://127.0.0.1:8000)
  - 食べログのエクスポートデータフォルダを用意する（公式からはエクスポートできないので、自分で作成したデータを利用する）
    （tabelog_reviews.csv と photos/ フォルダを含むこと）

実行方法:
  python tools/import_tabelog.py <export_dir> [--dry-run] [--skip-photos]

引数:
  export_dir      エクスポートデータのフォルダパス（絶対・相対どちらも可）

オプション:
  --dry-run       DBへの書き込みを行わず、インポート内容のみ確認する
  --skip-photos   写真のアップロードをスキップする

例:
  python tools/import_tabelog.py ../export-tabelog-review
  python tools/import_tabelog.py D:/VSCodeFolder/export-tabelog-review --dry-run
"""

import csv
import re
import sys
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore

# ──────────────────────────── 設定 ────────────────────────────

API_BASE = "http://127.0.0.1:8000/api"

# 食べログジャンル → マスタジャンル名 のマッピング
# マスタに存在する値: 和食, 洋食, 中華, イタリアン, フレンチ, 焼肉, 寿司, ラーメン, 居酒屋, カフェ, その他
GENRE_MAP: dict[str, str] = {
    # ラーメン系
    "ラーメン": "ラーメン", "つけ麺": "ラーメン", "担々麺": "ラーメン",
    "汁なし担々麺": "ラーメン", "油そば・まぜそば": "ラーメン", "冷麺": "ラーメン",
    "麺類": "ラーメン",
    # 和食系
    "和食": "和食", "日本料理": "和食", "そば": "和食", "うどん": "和食",
    "うどんすき": "和食", "うなぎ": "和食", "天ぷら": "和食", "天丼": "和食",
    "とんかつ": "和食", "かつ丼": "和食", "もつ焼き": "和食", "もつ鍋": "和食",
    "和菓子": "和食", "甘味処": "和食", "おにぎり": "和食", "鍋": "和食",
    "食堂": "和食", "郷土料理": "和食", "海鮮": "和食", "海鮮丼": "和食",
    "丼": "和食", "牛丼": "和食", "豚丼": "和食", "もんじゃ焼き": "和食",
    "お好み焼き": "和食", "たこ焼き": "和食", "ろばた焼き": "和食",
    "焼きそば": "和食", "弁当": "和食", "惣菜・デリ": "和食",
    "立ち食いそば": "和食", "麦とろ": "和食", "あんこう": "和食",
    "かき": "和食", "かに": "和食", "沖縄料理": "和食", "沖縄そば": "和食",
    "豆腐料理": "和食", "野菜料理": "和食", "大福": "和食",
    "たい焼き・大判焼き": "和食", "せんべい": "和食",
    # 中華系
    "中華料理": "中華", "四川料理": "中華", "台湾料理": "中華",
    "餃子": "中華", "小籠包": "中華", "飲茶・点心": "中華", "火鍋": "中華",
    # イタリアン系
    "イタリアン": "イタリアン", "パスタ": "イタリアン", "ピザ": "イタリアン",
    # 洋食系
    "洋食": "洋食", "ステーキ": "洋食", "ハンバーグ": "洋食", "ハンバーガー": "洋食",
    "アメリカ料理": "洋食", "オムライス": "洋食", "サンドイッチ": "洋食",
    # フレンチ系
    "フレンチ": "フレンチ", "ヨーロッパ料理": "フレンチ",
    # 焼肉系
    "焼肉": "焼肉", "ジンギスカン": "焼肉", "ホルモン": "焼肉",
    "牛タン": "焼肉", "牛料理": "焼肉", "肉料理": "焼肉",
    "鉄板焼き": "焼肉", "バーベキュー": "焼肉", "焼き鳥": "焼肉",
    "鳥料理": "焼肉", "からあげ": "焼肉", "豚しゃぶ": "焼肉",
    "しゃぶしゃぶ": "焼肉", "すき焼き": "焼肉",
    # 寿司系
    "寿司": "寿司", "回転寿司": "寿司",
    # 居酒屋系
    "居酒屋": "居酒屋", "バル": "居酒屋", "ダイニングバー": "居酒屋",
    "ビアホール": "居酒屋", "ビアガーデン": "居酒屋", "ビアバー": "居酒屋",
    "バー": "居酒屋", "日本酒バー": "居酒屋", "ワインバー": "居酒屋",
    "焼酎バー": "居酒屋", "立ち飲み": "居酒屋",
    # カフェ系
    "カフェ": "カフェ", "喫茶店": "カフェ",
}


# ──────────────────────────── ユーティリティ ────────────────────────────

def log(msg: str) -> None:
    print(msg, flush=True)


def parse_float(value: str) -> float | None:
    """'-' または空文字は None、それ以外は float に変換する"""
    v = value.strip()
    if not v or v == "-":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def parse_area_genre(raw: str) -> tuple[str, str]:
    """
    'エリア/ジャンル' フィールドをパースして (最寄り駅, ジャンル名) を返す。
    例: '（新宿三丁目、新宿、代々木/つけ麺）' → ('新宿三丁目', 'つけ麺')
    """
    # 括弧を取り除く
    inner = re.sub(r"[（）()]", "", raw).strip()
    if "/" in inner:
        area_part, genre_part = inner.split("/", 1)
    else:
        area_part, genre_part = inner, ""

    nearest = area_part.split("、")[0].split("、")[0].strip()
    first_genre = genre_part.split("、")[0].strip()
    return nearest, first_genre


# ──────────────────────────── マスタジャンルの取得 ────────────────────────────

def fetch_genre_masters() -> dict[str, int]:
    """マスタジャンルを取得し {ジャンル名: id} の辞書を返す"""
    resp = requests.get(f"{API_BASE}/masters/?type=genre", timeout=10)
    resp.raise_for_status()
    return {item["value"]: item["id"] for item in resp.json().get("items", [])}


def fetch_all_restaurants() -> dict[str, int]:
    """全レストランを全ページ取得し {tabelog_id: id} の辞書を返す（tabelog_id が未設定のものは除外）"""
    result: dict[str, int] = {}
    page = 1
    while True:
        resp = requests.get(f"{API_BASE}/restaurants/?page={page}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("items", []):
            tid = item.get("tabelog_id")
            if tid:
                result[tid] = item["id"]
        if page * data.get("per_page", 50) >= data.get("total", 0):
            break
        page += 1
    return result


# ──────────────────────────── CSV パース ────────────────────────────

def parse_row(row: dict, genre_name_to_id: dict[str, int]) -> dict:
    nearest, tabelog_genre = parse_area_genre(row.get("エリア/ジャンル", ""))

    # ジャンルマッピング（食べログ固有名 → マスタ名 → マスタ ID）
    master_genre_name = GENRE_MAP.get(tabelog_genre, "その他")
    genre_id = genre_name_to_id.get(master_genre_name)

    # 評価（'-' は None）
    rating_food = parse_float(row.get("料理・味", ""))
    rating_service = parse_float(row.get("サービス", ""))
    rating_atmosphere = parse_float(row.get("雰囲気", ""))
    rating_cp = parse_float(row.get("CP", ""))
    rating_drinks = parse_float(row.get("酒・ドリンク", ""))

    # 総合評価：「評価」列を優先し、なければサブ評価の平均
    rating_overall = parse_float(row.get("評価", ""))
    if rating_overall is None:
        subs = [v for v in [rating_food, rating_service, rating_atmosphere, rating_cp, rating_drinks]
                if v is not None]
        rating_overall = round(sum(subs) / len(subs) * 10) / 10 if subs else None

    # レビューコメント（タイトルを先頭に付加）
    title = row.get("タイトル(全文)", "").strip()
    comment = row.get("コメント(全文)", "").strip()
    if title and comment:
        review_comment = f"【{title}】\n{comment}"
    elif title:
        review_comment = f"【{title}】"
    else:
        review_comment = comment

    return {
        "name": row["店名"].strip(),
        "nearest_station": nearest,
        "genre_id": genre_id,
        "tabelog_id": row.get("店舗ID", "").strip() or None,
        "scene": "",
        "stars": None,
        "rating_overall": rating_overall,
        "rating_food": rating_food,
        "rating_service": rating_service,
        "rating_atmosphere": rating_atmosphere,
        "rating_cost_performance": rating_cp,
        "rating_drinks": rating_drinks,
        "visit_date": row.get("訪問日", "").strip(),
        "review_comment": review_comment,
        "notes": "",
        # インポート処理用
        "_photo_paths": [
            p.strip() for p in row.get("写真ローカルパス", "").split(";") if p.strip()
        ],
        "_tabelog_genre": tabelog_genre,
        "_mapped_genre": master_genre_name,
    }


# ──────────────────────────── API呼び出し ────────────────────────────

def create_restaurant(payload: dict) -> int:
    resp = requests.post(f"{API_BASE}/restaurants/", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["id"]


def update_restaurant(restaurant_id: int, payload: dict) -> None:
    resp = requests.put(f"{API_BASE}/restaurants/{restaurant_id}/", json=payload, timeout=30)
    resp.raise_for_status()


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
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv
    skip_photos = "--skip-photos" in sys.argv

    if not args:
        log("使い方: python tools/import_tabelog.py <export_dir> [--dry-run] [--skip-photos]")
        sys.exit(1)

    export_dir = Path(args[0]).resolve()
    csv_path = export_dir / "tabelog_reviews.csv"

    if not csv_path.exists():
        log(f"エラー: {csv_path} が見つかりません")
        sys.exit(1)

    if dry_run:
        log("【DRY RUN モード】DBへの書き込みは行いません\n")

    # CSV 読み込み
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    log(f"レビュー数: {len(rows)} 件\n")

    # API 疎通確認 + 既存レストラン名の取得（名前→IDの辞書）
    genre_name_to_id: dict[str, int] = {}
    existing_tabelog_id_to_id: dict[str, int] = {}
    if not dry_run:
        try:
            genre_name_to_id = fetch_genre_masters()
            existing_tabelog_id_to_id = fetch_all_restaurants()
            if existing_tabelog_id_to_id:
                log(f"既存レストラン（tabelog_id あり）{len(existing_tabelog_id_to_id)} 件を検出。同一店舗IDは更新します。\n")
        except requests.ConnectionError:
            log(f"エラー: APIサーバーに接続できません ({API_BASE})")
            log("バックエンドサーバーを起動してから再実行してください。")
            sys.exit(1)
    else:
        # dry-run 時もマスタ・既存レストランを取得して正確に表示する
        try:
            genre_name_to_id = fetch_genre_masters()
            existing_tabelog_id_to_id = fetch_all_restaurants()
            if existing_tabelog_id_to_id:
                log(f"既存レストラン（tabelog_id あり）{len(existing_tabelog_id_to_id)} 件を検出。\n")
        except Exception:
            log("警告: マスタ/既存データを取得できませんでした。")

    created = 0
    updated = 0
    photo_total = 0
    errors: list[tuple[str, str]] = []

    for i, row in enumerate(rows, 1):
        name = row.get("店名", "").strip() or f"不明#{i}"
        try:
            review = parse_row(row, genre_name_to_id)
            payload = {k: v for k, v in review.items() if not k.startswith("_")}

            if dry_run:
                existing_id = existing_tabelog_id_to_id.get(review["tabelog_id"])
                action = f"UPDATE(id={existing_id})" if existing_id else "CREATE"
                log(
                    f"[{i:3d}/{len(rows)}] [{action}] {name} "
                    f"| 訪問:{review['visit_date']} "
                    f"ジャンル:{review['_tabelog_genre']}→{review['_mapped_genre']} "
                    f"料理:{review['rating_food']} CP:{review['rating_cost_performance']} 酒:{review['rating_drinks']} "
                    f"写真:{len(review['_photo_paths'])}枚"
                )
                created += 1
                continue

            existing_id = existing_tabelog_id_to_id.get(review["tabelog_id"])

            if existing_id:
                # 既存レコードを更新（写真・星はスキップ）
                update_payload = {k: v for k, v in payload.items() if k != "stars"}
                update_restaurant(existing_id, update_payload)
                log(f"[{i:3d}/{len(rows)}] UPDATE {name} (id={existing_id})")
                updated += 1
            else:
                # 新規登録 + 写真アップロード
                restaurant_id = create_restaurant(payload)

                uploaded = 0
                if not skip_photos:
                    for rel_path in review["_photo_paths"]:
                        img_path = export_dir / Path(rel_path.replace("\\", "/"))
                        if not img_path.exists():
                            log(f"  写真が見つかりません: {img_path}")
                            continue
                        try:
                            upload_photo(restaurant_id, img_path)
                            uploaded += 1
                        except Exception as e:
                            log(f"  写真アップロード失敗 ({img_path.name}): {e}")

                log(f"[{i:3d}/{len(rows)}] CREATE {name} (写真: {uploaded}枚)")
                created += 1
                photo_total += uploaded

        except Exception as e:
            log(f"[{i:3d}/{len(rows)}] NG {name}: {e}")
            errors.append((name, str(e)))

    # 結果サマリー
    log(f"\n{'='*50}")
    log(f"完了: 新規 {created}件 / 更新 {updated}件 / エラー {len(errors)}件")
    if not dry_run and not skip_photos:
        log(f"アップロード写真: 計 {photo_total}枚")
    if errors:
        log("\nエラー一覧:")
        for name, err in errors:
            log(f"  - {name}: {err}")


if __name__ == "__main__":
    main()