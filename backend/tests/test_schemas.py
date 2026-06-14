"""api/schemas.py の Pydantic 入力スキーマの単体テスト。

DB・Django に依存せず、バリデーション境界（必須・max_length・ge/le・
カスタムバリデータ）が ADR のレビュー観点 #16 通りに効くことを検証する。
"""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from api.schemas import (
    AdminVerify,
    MasterCreate,
    PhotoReorder,
    RestaurantCreate,
    RestaurantUpdate,
)


# ---------------------------------------------------------------------------
# RestaurantCreate
# ---------------------------------------------------------------------------
class TestRestaurantCreate:
    def test_minimal_valid(self):
        r = RestaurantCreate(name="寿司屋")
        assert r.name == "寿司屋"
        # name 以外は省略可能で None になる
        assert r.nearest_station is None
        assert r.rating_food is None

    def test_full_valid(self):
        r = RestaurantCreate(
            name="ビストロ",
            nearest_station="渋谷",
            genre_id=3,
            scene="夜",
            stars=5,
            rating_overall=Decimal("4.5"),
            rating_food=Decimal("5.0"),
            visit_date="2026/04/19",
        )
        assert r.genre_id == 3
        assert r.stars == 5
        assert r.rating_overall == Decimal("4.5")

    def test_name_required(self):
        with pytest.raises(ValidationError):
            RestaurantCreate()

    def test_name_empty_rejected(self):
        # min_length=1 のため空文字は不可
        with pytest.raises(ValidationError):
            RestaurantCreate(name="")

    def test_name_too_long_rejected(self):
        with pytest.raises(ValidationError):
            RestaurantCreate(name="あ" * 201)

    def test_name_max_length_ok(self):
        r = RestaurantCreate(name="あ" * 200)
        assert len(r.name) == 200

    @pytest.mark.parametrize("stars", [0, 6, -1])
    def test_stars_out_of_range_rejected(self, stars):
        with pytest.raises(ValidationError):
            RestaurantCreate(name="店", stars=stars)

    @pytest.mark.parametrize("stars", [1, 3, 5])
    def test_stars_in_range_ok(self, stars):
        assert RestaurantCreate(name="店", stars=stars).stars == stars

    @pytest.mark.parametrize(
        "field",
        [
            "rating_overall",
            "rating_food",
            "rating_service",
            "rating_atmosphere",
            "rating_cost_performance",
            "rating_drinks",
        ],
    )
    @pytest.mark.parametrize("value", [Decimal("0.9"), Decimal("5.1")])
    def test_rating_out_of_range_rejected(self, field, value):
        with pytest.raises(ValidationError):
            RestaurantCreate(name="店", **{field: value})

    @pytest.mark.parametrize("value", [Decimal("1.0"), Decimal("3.3"), Decimal("5.0")])
    def test_rating_in_range_ok(self, value):
        assert RestaurantCreate(name="店", rating_food=value).rating_food == value

    def test_genre_id_must_be_positive(self):
        with pytest.raises(ValidationError):
            RestaurantCreate(name="店", genre_id=0)

    @pytest.mark.parametrize("scene", ["朝", "昼", "夜", "持ち帰り", "その他", ""])
    def test_scene_valid_values(self, scene):
        assert RestaurantCreate(name="店", scene=scene).scene == scene

    def test_scene_none_allowed(self):
        assert RestaurantCreate(name="店", scene=None).scene is None

    @pytest.mark.parametrize("scene", ["深夜", "ランチ", "invalid"])
    def test_scene_invalid_rejected(self, scene):
        with pytest.raises(ValidationError):
            RestaurantCreate(name="店", scene=scene)

    def test_review_comment_max_length(self):
        with pytest.raises(ValidationError):
            RestaurantCreate(name="店", review_comment="x" * 5001)

    def test_notes_max_length(self):
        with pytest.raises(ValidationError):
            RestaurantCreate(name="店", notes="x" * 2001)


# ---------------------------------------------------------------------------
# RestaurantUpdate
# ---------------------------------------------------------------------------
class TestRestaurantUpdate:
    def test_name_optional_on_update(self):
        # Create と異なり name 省略が許される（部分更新用）
        u = RestaurantUpdate(stars=4)
        assert u.name is None
        assert u.stars == 4

    def test_empty_update_ok(self):
        u = RestaurantUpdate()
        assert u.name is None

    def test_name_still_validated_when_present(self):
        # 渡した場合は Create と同じ制約（min_length=1）が効く
        with pytest.raises(ValidationError):
            RestaurantUpdate(name="")

    def test_inherits_scene_validator(self):
        with pytest.raises(ValidationError):
            RestaurantUpdate(scene="不正")

    def test_exclude_unset_only_returns_provided_fields(self):
        # views の PUT は model_dump(exclude_unset=True) で部分更新する
        u = RestaurantUpdate(stars=4)
        dumped = u.model_dump(exclude_unset=True)
        assert dumped == {"stars": 4}


# ---------------------------------------------------------------------------
# MasterCreate
# ---------------------------------------------------------------------------
class TestMasterCreate:
    def test_valid(self):
        m = MasterCreate(category="genre", value="和食", sort_order=2)
        assert m.category == "genre"
        assert m.value == "和食"
        assert m.sort_order == 2

    def test_sort_order_defaults_to_zero(self):
        m = MasterCreate(category="genre", value="和食")
        assert m.sort_order == 0

    def test_category_required(self):
        with pytest.raises(ValidationError):
            MasterCreate(value="和食")

    def test_value_required(self):
        with pytest.raises(ValidationError):
            MasterCreate(category="genre")

    def test_sort_order_negative_rejected(self):
        with pytest.raises(ValidationError):
            MasterCreate(category="genre", value="和食", sort_order=-1)

    def test_category_max_length(self):
        with pytest.raises(ValidationError):
            MasterCreate(category="x" * 51, value="和食")

    def test_value_max_length(self):
        with pytest.raises(ValidationError):
            MasterCreate(category="genre", value="x" * 101)


# ---------------------------------------------------------------------------
# AdminVerify
# ---------------------------------------------------------------------------
class TestAdminVerify:
    def test_valid(self):
        assert AdminVerify(password="secret").password == "secret"

    def test_password_required(self):
        with pytest.raises(ValidationError):
            AdminVerify()

    def test_password_max_length(self):
        with pytest.raises(ValidationError):
            AdminVerify(password="x" * 201)


# ---------------------------------------------------------------------------
# PhotoReorder
# ---------------------------------------------------------------------------
class TestPhotoReorder:
    def test_valid(self):
        p = PhotoReorder(photo_ids=[3, 1, 2])
        assert p.photo_ids == [3, 1, 2]

    def test_single_id_ok(self):
        assert PhotoReorder(photo_ids=[1]).photo_ids == [1]

    def test_empty_list_rejected(self):
        # min_length=1
        with pytest.raises(ValidationError):
            PhotoReorder(photo_ids=[])

    def test_missing_field_rejected(self):
        with pytest.raises(ValidationError):
            PhotoReorder()

    def test_non_int_rejected(self):
        with pytest.raises(ValidationError):
            PhotoReorder(photo_ids=["a", "b"])