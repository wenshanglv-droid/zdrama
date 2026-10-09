from django.urls import path, include
from rest_framework.routers import DefaultRouter
from archive import views
router = DefaultRouter()
router.register("productions", views.ProductionViewSet, basename="productions")
router.register("performances", views.PerformanceViewSet, basename="performances")
router.register("assets", views.AssetViewSet, basename="assets")
router.register("shares", views.ShareViewSet, basename="shares")
router.register("editions", views.EditionViewSet, basename="editions")
router.register("people", views.PersonViewSet)
router.register("stage-roles", views.StageRoleViewSet, basename="stage-roles")
router.register("cast", views.CastViewSet, basename="cast")
router.register("accounts", views.AccountViewSet)
urlpatterns = [path("api/session/", views.session), path("api/login/", views.Login.as_view()), path("api/logout/", views.signout), path("api/shared/<str:token>/", views.shared_detail), path("api/shared/<str:token>/content/", views.shared_content), path("api/", include(router.urls))]
