"""api/views.py の DB を使わない純粋ヘルパー関数の単体テスト。

対象: _maybe_float / _to_rgb / _make_thumbnail / _error / _serialize_restaurant。
Django 設定は conftest.py で初期化済み（JsonResponse 利用のため）。
DB 接続は一切行わず、_serialize_restaurant にはダミーオブジェクトを渡す。
"""
import io
import json
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from PIL import Image

from api import messages as msg
from api.views import (
    THUMBNAIL_SIZE,
    _error,
    _make_thumbnail,
    _maybe_float,
    _serialize_restaurant,
    _to_rgb,
)


# ---------------------------------------------------------------------------
# _maybe_float
# ---------------------------------------------------------------------------
class TestMaybeFloat:
    def test_none_returns_none(self):
        assert _maybe_float(None) is None

    def test_decimal_converted_to_float(self):
        result = _maybe_float(Decimal("4.5"))
        assert result == 4.5
        assert isinstance(result, float)

    def test_int_converted_to_float(self):
        assert _maybe_float(3) == 3.0

    def test_zero_is_not_treated_as_none(self):
        # 0.0 は None ではないため float(0.0) を返す（falsy だが有効値）
        result = _maybe_float(Decimal("0"))
        assert result == 0.0
        assert result is not None


# ---------------------------------------------------------------------------
# _to_rgb
# ---------------------------------------------------------------------------
class TestToRgb:
    @pytest.mark.parametrize("mode", ["RGBA", "P", "LA"])
    def test_converts_modes_with_alpha_or_palette(self, mode):
        img = Image.new(mode, (10, 10))
        assert _to_rgb(img).mode == "RGB"

    def test_rgb_passed_through_unchanged(self):
        img = Image.new("RGB", (10, 10))
        assert _to_rgb(img) is img

    def test_grayscale_passed_through(self):
        # "L" は対象外なのでそのまま返る
        img = Image.new("L", (10, 10))
        assert _to_rgb(img) is img
        assert _to_rgb(img).mode == "L"


# ---------------------------------------------------------------------------
# _make_thumbnail
# ---------------------------------------------------------------------------
def _png_bytes(size, mode="RGB", color=(120, 80, 40)):
    img = Image.new(mode, size, color if mode == "RGB" else None)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestMakeThumbnail:
    def test_returns_valid_jpeg(self):
        out = _make_thumbnail(_png_bytes((800, 600)))
        result = Image.open(io.BytesIO(out))
        assert result.format == "JPEG"

    def test_fits_within_thumbnail_bounds(self):
        out = _make_thumbnail(_png_bytes((1000, 500)))
        result = Image.open(io.BytesIO(out))
        assert result.width <= THUMBNAIL_SIZE[0]
        assert result.height <= THUMBNAIL_SIZE[1]

    def test_aspect_ratio_preserved(self):
        out = _make_thumbnail(_png_bytes((1000, 500)))
        result = Image.open(io.BytesIO(out))
        # 2:1 の比率が保たれる（thumbnail は縦横比維持）
        assert result.width == result.height * 2

    def test_smaller_than_thumbnail_not_upscaled(self):
        out = _make_thumbnail(_png_bytes((100, 80)))
        result = Image.open(io.BytesIO(out))
        assert (result.width, result.height) == (100, 80)

    def test_rgba_source_handled(self):
        # アルファ付き PNG でも JPEG 化できる（_to_rgb 経由）
        out = _make_thumbnail(_png_bytes((400, 400), mode="RGBA"))
        assert Image.open(io.BytesIO(out)).format == "JPEG"


# ---------------------------------------------------------------------------
# _error
# ---------------------------------------------------------------------------
class TestError:
    def test_default_status_400(self):
        resp = _error(msg.ERR_INVALID_INPUT)
        assert resp.status_code == 400
        assert json.loads(resp.content) == {"error": msg.ERR_INVALID_INPUT}

    def test_custom_status(self):
        resp = _error(msg.ERR_SERVER, 500)
        assert resp.status_code == 500

    def test_details_included_when_provided(self):
        resp = _error(msg.ERR_INVALID_INPUT, details={"name": "必須です"})
        body = json.loads(resp.content)
        assert body["details"] == {"name": "必須です"}

    def test_details_omitted_when_none(self):
        body = json.loads(_error(msg.ERR_INVALID_INPUT).content)
        assert "details" not in body

    def test_empty_details_omitted(self):
        # 空 dict は falsy なので details キーを付けない
        body = json.loads(_error(msg.ERR_INVALID_INPUT, details={}).content)
        assert "details" not in body


# ---------------------------------------------------------------------------
# _serialize_restaurant
# ---------------------------------------------------------------------------
def _make_restaurant(**overrides):
    """DB を使わず _serialize_restaurant に渡せるダミーレストラン。"""
    base = dict(
        id=1,
        name="テスト店",
        nearest_station="新宿",
        genre_id=2,
        genre=SimpleNamespace(value="和食"),
        scene="夜",
        stars=4,
        rating_overall=Decimal("4.2"),
        rating_food=Decimal("4.5"),
        rating_service=Decimal("4.0"),
        rating_atmosphere=Decimal("4.0"),
        rating_cost_performance=Decimal("4.0"),
        rating_drinks=Decimal("4.0"),
        visit_date="2026/04/19",
        review_comment="美味しかった",
        notes="備考",
        tabelog_id="12345",
        prefecture="東京都",
        address="新宿区1-1",
        phone="03-1234-5678",
        business_hours="11:00-22:00",
        regular_holiday="月曜",
        photos=[],
        created_at=datetime(2026, 4, 19, 12, 0, 0),
        updated_at=datetime(2026, 4, 20, 9, 30, 0),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _photo(pid, deleted_at=None):
    return SimpleNamespace(id=pid, deleted_at=deleted_at)


class TestSerializeRestaurant:
    def test_basic_fields(self):
        data = _serialize_restaurant(_make_restaurant())
        assert data["id"] == 1
        assert data["name"] == "テスト店"
        assert data["genre_name"] == "和食"
        assert data["prefecture"] == "東京都"

    def test_ratings_serialized_as_float(self):
        data = _serialize_restaurant(_make_restaurant())
        assert data["rating_overall"] == 4.2
        assert isinstance(data["rating_food"], float)

    def test_none_ratings_stay_none(self):
        data = _serialize_restaurant(_make_restaurant(rating_overall=None, rating_drinks=None))
        assert data["rating_overall"] is None
        assert data["rating_drinks"] is None

    def test_genre_none_yields_none_name(self):
        data = _serialize_restaurant(_make_restaurant(genre=None))
        assert data["genre_name"] is None

    def test_timestamps_iso_formatted(self):
        data = _serialize_restaurant(_make_restaurant())
        assert data["created_at"] == "2026-04-19T12:00:00"
        assert data["updated_at"] == "2026-04-20T09:30:00"

    def test_none_timestamps(self):
        data = _serialize_restaurant(_make_restaurant(created_at=None, updated_at=None))
        assert data["created_at"] is None
        assert data["updated_at"] is None

    def test_no_photos_means_no_thumbnail(self):
        data = _serialize_restaurant(_make_restaurant(photos=[]))
        assert data["thumbnail_url"] is None
        assert data["photo_count"] == 0

    def test_thumbnail_uses_first_active_photo(self):
        photos = [_photo(10), _photo(11)]
        data = _serialize_restaurant(_make_restaurant(photos=photos))
        assert data["thumbnail_url"] == "/api/photos/10/thumb/"
        assert data["photo_count"] == 2

    def test_deleted_photos_excluded(self):
        # 先頭が論理削除済みなら次の有効写真がサムネイルになる
        photos = [_photo(10, deleted_at=datetime(2026, 4, 1)), _photo(11)]
        data = _serialize_restaurant(_make_restaurant(photos=photos))
        assert data["thumbnail_url"] == "/api/photos/11/thumb/"
        assert data["photo_count"] == 1

    def test_include_thumb_false_skips_thumbnail(self):
        # CSV/JSON エクスポート用: 写真があっても thumbnail_url は付けない
        photos = [_photo(10)]
        data = _serialize_restaurant(_make_restaurant(photos=photos), include_thumb=False)
        assert data["thumbnail_url"] is None
        # photo_count は写真の有無に関わらず数える
        assert data["photo_count"] == 1