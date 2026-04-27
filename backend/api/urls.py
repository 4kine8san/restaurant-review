from django.urls import path
from . import views

urlpatterns = [
    path("restaurants/", views.restaurant_list),
    path("restaurants/<int:pk>/", views.restaurant_detail),
    path("restaurants/export/", views.restaurant_export),
    path("photos/", views.photo_upload),
    path("photos/<int:pk>/", views.photo_detail),
    path("photos/<int:pk>/thumb/", views.photo_thumbnail),
    path("photos/<int:pk>/rotate/", views.photo_rotate),
    path("photos/reorder/", views.photo_reorder),
    path("masters/", views.master_list),
    path("masters/<int:pk>/", views.master_detail),
    path("admin/verify/", views.admin_verify),
    path("stats/", views.restaurant_stats),
]
