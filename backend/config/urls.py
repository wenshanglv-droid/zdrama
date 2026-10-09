from django.urls import path, include
from rest_framework.routers import DefaultRouter
from archive import views
router = DefaultRouter()
router.register("productions", views.ProductionViewSet)
router.register("performances", views.PerformanceViewSet)
router.register("assets", views.AssetViewSet, basename="assets")
router.register("shares", views.ShareViewSet, basename="shares")
urlpatterns = [path("api/session/", views.session), path("api/login/", views.Login.as_view()), path("api/logout/", views.signout), path("api/shared/<str:token>/", views.shared_detail), path("api/shared/<str:token>/content/", views.shared_content), path("api/", include(router.urls))]
