import os
import io
import csv
import json
import logging
from datetime import datetime

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from PIL import Image
from pydantic import ValidationError

from database.connection import SessionLocal
from database.models import Restaurant, Photo, Master
from .schemas import RestaurantCreate, RestaurantUpdate, MasterCreate, AdminVerify, PhotoReorder

logger = logging.getLogger(__name__)

THUMBNAIL_SIZE = (300, 300)


def _get_db():
    return SessionLocal()


def _error(message: str, status: int = 400):
    return JsonResponse({"error": message}, status=status)


def _to_rgb(img: Image.Image) -> Image.Image:
    if img.mode in ("RGBA", "P", "LA"):
        return img.convert("RGB")
    return img


def _make_thumbnail(image_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    img = _to_rgb(img)
    img.thumbnail(THUMBNAIL_SIZE)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _apply_filters(query, params):
    keyword = params.get("keyword", "").strip()
    if keyword:
        query = query.filter(
            Restaurant.name.ilike(f"%{keyword}%") |
            Restaurant.nearest_station.ilike(f"%{keyword}%") |
            Restaurant.visit_date.ilike(f"%{keyword}%")
        )
    genre_id = params.get("genre_id")
    if genre_id:
        query = query.filter(Restaurant.genre_id == int(genre_id))
    return query


def _serialize_restaurant(r: Restaurant, include_thumb: bool = True) -> dict:
    active_photos = [p for p in r.photos if p.deleted_at is None]
    thumb_url = None
    if include_thumb and active_photos:
        thumb_url = f"/api/photos/{active_photos[0].id}/thumb/"
    return {
        "id": r.id,
        "name": r.name,
        "nearest_station": r.nearest_station,
        "genre_id": r.genre_id,
        "genre_name": r.genre.value if r.genre else None,
        "scene": r.scene,
        "stars": r.stars,
        "rating_overall": float(r.rating_overall) if r.rating_overall else None,
        "rating_food": float(r.rating_food) if r.rating_food else None,
        "rating_service": float(r.rating_service) if r.rating_service else None,
        "rating_atmosphere": float(r.rating_atmosphere) if r.rating_atmosphere else None,
        "rating_cost_performance": float(r.rating_cost_performance) if r.rating_cost_performance else None,
        "rating_drinks": float(r.rating_drinks) if r.rating_drinks else None,
        "visit_date": r.visit_date,
        "review_comment": r.review_comment,
        "notes": r.notes,
        "thumbnail_url": thumb_url,
        "photo_count": len(active_photos),
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
def restaurant_list(request):
    db = _get_db()
    try:
        if request.method == "GET":
            query = db.query(Restaurant).filter(Restaurant.deleted_at.is_(None))
            query = _apply_filters(query, request.GET)

            order = request.GET.get("order", "created_at_desc")
            if order == "name_asc":
                query = query.order_by(Restaurant.name.asc())
            elif order == "rating_desc":
                query = query.order_by(Restaurant.rating_overall.desc().nullslast())
            elif order == "visit_date_desc":
                query = query.order_by(Restaurant.visit_date.desc().nullslast())
            else:
                query = query.order_by(Restaurant.created_at.desc())

            total = query.count()
            page = max(1, int(request.GET.get("page", 1)))
            per_page = 50
            restaurants = query.offset((page - 1) * per_page).limit(per_page).all()

            return JsonResponse({
                "total": total,
                "page": page,
                "per_page": per_page,
                "items": [_serialize_restaurant(r) for r in restaurants],
            })

        # POST
        try:
            data = RestaurantCreate.model_validate_json(request.body)
        except ValidationError:
            return _error("入力値が不正です")

        restaurant = Restaurant(**data.model_dump())
        db.add(restaurant)
        db.commit()
        db.refresh(restaurant)
        return JsonResponse(_serialize_restaurant(restaurant), status=201)
    except Exception:
        logger.exception("restaurant_list error")
        db.rollback()
        return _error("サーバーエラーが発生しました", 500)
    finally:
        db.close()


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def restaurant_detail(request, pk: int):
    db = _get_db()
    try:
        restaurant = db.query(Restaurant).filter(
            Restaurant.id == pk, Restaurant.deleted_at.is_(None)
        ).first()
        if not restaurant:
            return _error("レストランが見つかりません", 404)

        if request.method == "GET":
            data = _serialize_restaurant(restaurant)
            data["photos"] = [
                {"id": p.id, "sort_order": p.sort_order, "rotation": p.rotation}
                for p in restaurant.photos if p.deleted_at is None
            ]
            return JsonResponse(data)

        if request.method == "PUT":
            try:
                patch = RestaurantUpdate.model_validate_json(request.body)
            except ValidationError:
                return _error("入力値が不正です")
            for field, value in patch.model_dump(exclude_unset=True).items():
                setattr(restaurant, field, value)
            restaurant.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(restaurant)
            return JsonResponse(_serialize_restaurant(restaurant))

        # DELETE
        restaurant.deleted_at = datetime.utcnow()
        db.commit()
        return JsonResponse({"ok": True})
    except Exception:
        logger.exception("restaurant_detail error")
        db.rollback()
        return _error("サーバーエラーが発生しました", 500)
    finally:
        db.close()


@require_http_methods(["GET"])
def restaurant_export(request):
    db = _get_db()
    try:
        query = db.query(Restaurant).filter(Restaurant.deleted_at.is_(None))
        query = _apply_filters(query, request.GET)
        restaurants = query.order_by(Restaurant.created_at.desc()).all()
        fmt = request.GET.get("format", "csv")

        if fmt == "json":
            data = [_serialize_restaurant(r, include_thumb=False) for r in restaurants]
            response = HttpResponse(
                json.dumps(data, ensure_ascii=False, indent=2),
                content_type="application/json; charset=utf-8",
            )
            response["Content-Disposition"] = 'attachment; filename="restaurants.json"'
            return response

        # CSV
        output = io.StringIO()
        writer = csv.writer(output)
        headers = ["ID", "名前", "最寄り駅", "ジャンル", "利用シーン", "星", "総合", "料理",
                   "サービス", "雰囲気", "CP", "酒", "訪問日", "コメント", "備考", "登録日"]
        writer.writerow(headers)
        for r in restaurants:
            writer.writerow([
                r.id, r.name, r.nearest_station or "",
                r.genre.value if r.genre else "",
                r.scene or "", r.stars or "",
                r.rating_overall or "", r.rating_food or "",
                r.rating_service or "", r.rating_atmosphere or "",
                r.rating_cost_performance or "", r.rating_drinks or "",
                r.visit_date or "", r.review_comment or "", r.notes or "",
                r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
            ])
        response = HttpResponse(
            "\ufeff" + output.getvalue(),
            content_type="text/csv; charset=utf-8-sig",
        )
        response["Content-Disposition"] = 'attachment; filename="restaurants.csv"'
        return response
    except Exception:
        logger.exception("restaurant_export error")
        return _error("サーバーエラーが発生しました", 500)
    finally:
        db.close()


@csrf_exempt
@require_http_methods(["POST"])
def photo_upload(request):
    db = _get_db()
    try:
        restaurant_id = request.POST.get("restaurant_id")
        if not restaurant_id:
            return _error("restaurant_id は必須です")

        file = request.FILES.get("photo")
        if not file:
            return _error("photo ファイルが必要です")

        image_bytes = file.read()
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()
        except Exception:
            return _error("有効な画像ファイルを指定してください")

        thumbnail_bytes = _make_thumbnail(image_bytes)

        max_order = db.query(Photo).filter(
            Photo.restaurant_id == int(restaurant_id),
            Photo.deleted_at.is_(None),
        ).count()

        photo_obj = Photo(
            restaurant_id=int(restaurant_id),
            image_data=image_bytes,
            thumbnail_data=thumbnail_bytes,
            sort_order=max_order,
        )
        db.add(photo_obj)
        db.commit()
        db.refresh(photo_obj)
        return JsonResponse({"id": photo_obj.id, "sort_order": photo_obj.sort_order}, status=201)
    except Exception:
        logger.exception("photo_upload error")
        db.rollback()
        return _error("サーバーエラーが発生しました", 500)
    finally:
        db.close()


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def photo_detail(request, pk: int):
    db = _get_db()
    try:
        photo = db.query(Photo).filter(Photo.id == pk, Photo.deleted_at.is_(None)).first()
        if not photo:
            return _error("写真が見つかりません", 404)

        if request.method == "DELETE":
            photo.deleted_at = datetime.utcnow()
            db.commit()
            return JsonResponse({"ok": True})

        return HttpResponse(photo.image_data, content_type="image/jpeg")
    except Exception:
        logger.exception("photo_detail error")
        db.rollback()
        return _error("サーバーエラーが発生しました", 500)
    finally:
        db.close()


@require_http_methods(["GET"])
def photo_thumbnail(request, pk: int):
    db = _get_db()
    try:
        photo = db.query(Photo).filter(Photo.id == pk, Photo.deleted_at.is_(None)).first()
        if not photo:
            return _error("写真が見つかりません", 404)
        return HttpResponse(photo.thumbnail_data, content_type="image/jpeg")
    finally:
        db.close()


@csrf_exempt
@require_http_methods(["PUT"])
def photo_rotate(request, pk: int):
    """現在保存されている画像を時計回りに90度回転して保存する。"""
    db = _get_db()
    try:
        photo = db.query(Photo).filter(Photo.id == pk, Photo.deleted_at.is_(None)).first()
        if not photo:
            return _error("写真が見つかりません", 404)

        img = Image.open(io.BytesIO(photo.image_data))
        img = _to_rgb(img)
        rotated = img.rotate(-90, expand=True)
        buf = io.BytesIO()
        rotated.save(buf, format="JPEG", quality=95)
        image_bytes = buf.getvalue()

        photo.image_data = image_bytes
        photo.thumbnail_data = _make_thumbnail(image_bytes)
        photo.rotation = (photo.rotation + 90) % 360
        db.commit()
        return JsonResponse({"ok": True, "rotation": photo.rotation})
    except Exception:
        logger.exception("photo_rotate error")
        db.rollback()
        return _error("サーバーエラーが発生しました", 500)
    finally:
        db.close()


@csrf_exempt
@require_http_methods(["PUT"])
def photo_reorder(request):
    db = _get_db()
    try:
        try:
            data = PhotoReorder.model_validate_json(request.body)
        except ValidationError:
            return _error("photo_ids が不正です")

        for i, photo_id in enumerate(data.photo_ids):
            db.query(Photo).filter(
                Photo.id == photo_id,
                Photo.deleted_at.is_(None),
            ).update({"sort_order": i})
        db.commit()
        return JsonResponse({"ok": True})
    except Exception:
        logger.exception("photo_reorder error")
        db.rollback()
        return _error("サーバーエラーが発生しました", 500)
    finally:
        db.close()


@csrf_exempt
@require_http_methods(["GET", "POST"])
def master_list(request):
    db = _get_db()
    try:
        if request.method == "GET":
            category = request.GET.get("category")
            query = db.query(Master).filter(Master.deleted_at.is_(None))
            if category:
                query = query.filter(Master.category == category)
            masters = query.order_by(Master.sort_order).all()
            return JsonResponse({
                "items": [
                    {"id": m.id, "category": m.category, "value": m.value, "sort_order": m.sort_order}
                    for m in masters
                ]
            })

        try:
            data = MasterCreate.model_validate_json(request.body)
        except ValidationError:
            return _error("入力値が不正です")
        master = Master(**data.model_dump())
        db.add(master)
        db.commit()
        db.refresh(master)
        return JsonResponse({"id": master.id, "category": master.category, "value": master.value}, status=201)
    except Exception:
        logger.exception("master_list error")
        db.rollback()
        return _error("サーバーエラーが発生しました", 500)
    finally:
        db.close()


@csrf_exempt
@require_http_methods(["DELETE"])
def master_detail(request, pk: int):
    db = _get_db()
    try:
        master = db.query(Master).filter(Master.id == pk, Master.deleted_at.is_(None)).first()
        if not master:
            return _error("マスタが見つかりません", 404)
        master.deleted_at = datetime.utcnow()
        db.commit()
        return JsonResponse({"ok": True})
    except Exception:
        logger.exception("master_detail error")
        db.rollback()
        return _error("サーバーエラーが発生しました", 500)
    finally:
        db.close()


@csrf_exempt
@require_http_methods(["POST"])
def admin_verify(request):
    try:
        data = AdminVerify.model_validate_json(request.body)
    except ValidationError:
        return _error("パスワードが不正です")

    admin_password = os.environ.get("ADMIN_PASSWORD", "")
    if not admin_password:
        return _error("管理者パスワードが設定されていません", 500)

    if data.password == admin_password:
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False, "error": "パスワードが違います"}, status=401)
