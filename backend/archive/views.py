import hashlib
import secrets
from pathlib import Path
from django.conf import settings
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.http import StreamingHttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.utils.http import content_disposition_header
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from .models import Production, Performance, Asset, Share, Audit
from .serializers import ProductionSerializer, PerformanceSerializer, AssetSerializer, ShareSerializer

class Internal(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_staff)

@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def session(request):
    return Response({"csrfToken": get_token(request), "user": {"username": request.user.username, "internal": request.user.is_staff} if request.user.is_authenticated else None})

class LoginThrottle(AnonRateThrottle):
    scope = "login"

@method_decorator(csrf_protect, name="dispatch")
class Login(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginThrottle]
    def post(self, request):
        user = authenticate(request, username=request.data.get("username", ""), password=request.data.get("password", ""))
        if user is None:
            return Response({"detail": "用户名或密码错误"}, status=400)
        login(request, user)
        return Response({"username": user.username})

@api_view(["POST"])
def signout(request):
    logout(request)
    return Response({"ok": True})

class InternalViewSet(viewsets.ModelViewSet):
    permission_classes = [Internal]
    http_method_names = ["get", "post", "head", "options"]
    def perform_create(self, serializer):
        obj = serializer.save()
        Audit.objects.create(actor=self.request.user, action=f"create_{obj._meta.model_name}", object_id=str(obj.pk))

class ProductionViewSet(InternalViewSet):
    queryset = Production.objects.order_by("-id")
    serializer_class = ProductionSerializer

class PerformanceViewSet(InternalViewSet):
    queryset = Performance.objects.select_related("production").order_by("-starts_at")
    serializer_class = PerformanceSerializer

class AssetViewSet(InternalViewSet):
    serializer_class = AssetSerializer
    def get_queryset(self):
        qs = Asset.objects.select_related("performance__production").order_by("-created_at")
        if not self.request.user.is_superuser:
            qs = qs.filter(owner=self.request.user)
        q = self.request.query_params.get("q", "")
        if q:
            from django.db.models import Q
            qs = qs.filter(Q(title__icontains=q) | Q(original_name__icontains=q) | Q(performance__title__icontains=q) | Q(performance__production__title__icontains=q))
        if self.request.query_params.get("category"):
            qs = qs.filter(category=self.request.query_params["category"])
        return qs
    def perform_create(self, serializer):
        f = self.request.FILES.get("file")
        if not f or not f.size or f.size > settings.MAX_UPLOAD_BYTES:
            raise serializers.ValidationError({"file": "请上传非空且不超过100MB的文件"})
        if len(f.name) > 255:
            raise serializers.ValidationError({"file": "文件名过长"})
        digest = hashlib.sha256()
        for chunk in f.chunks(): digest.update(chunk)
        f.seek(0)
        obj = serializer.save(owner=self.request.user, file=f, original_name=f.name, size=f.size, sha256=digest.hexdigest())
        Audit.objects.create(actor=self.request.user, action="upload", object_id=str(obj.pk))
    @action(detail=True, methods=["get"])
    def content(self, request, pk=None):
        return deliver(self.get_object(), request, download=True)
    @action(detail=True, methods=["get"])
    def preview(self, request, pk=None):
        return deliver(self.get_object(), request, download=False)

class ShareCreate(serializers.Serializer):
    asset = serializers.IntegerField()
    recipient_username = serializers.CharField()
    expires_at = serializers.DateTimeField()
    allow_download = serializers.BooleanField(default=False)
    def validate_expires_at(self, value):
        if not timezone.now() < value <= timezone.now() + timezone.timedelta(days=30):
            raise serializers.ValidationError("有效期须在未来30天内")
        return value

class ShareViewSet(viewsets.GenericViewSet):
    permission_classes = [Internal]
    serializer_class = ShareSerializer
    def get_queryset(self):
        qs = Share.objects.select_related("asset", "recipient").order_by("-id")
        return qs if self.request.user.is_superuser else qs.filter(created_by=self.request.user)
    def list(self, request):
        page = self.paginate_queryset(self.get_queryset())
        return self.get_paginated_response(self.get_serializer(page, many=True).data)
    def create(self, request):
        data = ShareCreate(data=request.data); data.is_valid(raise_exception=True); d=data.validated_data
        assets = Asset.objects.all() if request.user.is_superuser else Asset.objects.filter(owner=request.user)
        asset = get_object_or_404(assets, pk=d["asset"])
        recipient = get_user_model().objects.filter(username=d["recipient_username"], is_active=True).first()
        if recipient is None:
            raise serializers.ValidationError({"recipient_username": "接收账号不存在或不可用，请联系管理员创建"})
        if not d["allow_download"] and Path(asset.original_name).suffix.lower() not in [".pdf", ".jpg", ".jpeg", ".png"]:
            raise serializers.ValidationError({"allow_download": "此格式尚不支持仅预览，请允许下载或等待后续转码功能"})
        token = secrets.token_urlsafe(32)
        obj = Share.objects.create(asset=asset, recipient=recipient, created_by=request.user, expires_at=d["expires_at"], allow_download=d["allow_download"], token_hash=hashlib.sha256(token.encode()).hexdigest())
        Audit.objects.create(actor=request.user, action="share_create", object_id=str(obj.pk))
        return Response({**self.get_serializer(obj).data, "url": f"/share/{token}"}, status=status.HTTP_201_CREATED)
    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        obj = self.get_object(); obj.revoked_at=timezone.now(); obj.save(update_fields=["revoked_at"])
        Audit.objects.create(actor=request.user, action="share_revoke", object_id=str(obj.pk))
        return Response({"ok": True})

def active_share(request, token):
    return get_object_or_404(Share.objects.select_related("asset"), token_hash=hashlib.sha256(token.encode()).hexdigest(), recipient=request.user, recipient__is_active=True, revoked_at__isnull=True, expires_at__gt=timezone.now())

@api_view(["GET"])
def shared_detail(request, token):
    obj = active_share(request, token)
    return Response({"title": obj.asset.title, "original_name": obj.asset.original_name, "expires_at": obj.expires_at, "allow_download": obj.allow_download})

@api_view(["GET"])
def shared_content(request, token):
    obj = active_share(request, token)
    download = request.query_params.get("download") == "1"
    if download and not obj.allow_download:
        return Response({"detail": "未授权下载"}, status=403)
    return deliver(obj.asset, request, download=download, share=obj)

def deliver(asset, request, download, share=None):
    types = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    mime = types.get(Path(asset.original_name).suffix.lower())
    if not download:
        if not mime:
            return Response({"detail": "此格式暂不支持预览"}, status=415)
        with asset.file.open("rb") as source:
            prefix = source.read(8)
        signatures = {"application/pdf": b"%PDF-", "image/jpeg": b"\xff\xd8\xff", "image/png": b"\x89PNG\r\n\x1a\n"}
        if not prefix.startswith(signatures[mime]):
            return Response({"detail": "文件内容与扩展名不匹配，已禁止预览"}, status=415)
    def stream():
        with asset.file.open("rb") as source:
            while True:
                if share and not Share.objects.filter(pk=share.pk, recipient__is_active=True, revoked_at__isnull=True, expires_at__gt=timezone.now()).exists():
                    break
                chunk = source.read(64 * 1024)
                if not chunk: break
                yield chunk
    Audit.objects.create(actor=request.user, action="download" if download else "preview", object_id=str(asset.pk))
    response = StreamingHttpResponse(stream(), content_type="application/octet-stream" if download else mime)
    response["Content-Disposition"] = content_disposition_header(download, asset.original_name)
    response["Cache-Control"] = "private, no-store"
    response["X-Accel-Buffering"] = "no"
    response["Content-Security-Policy"] = "sandbox"
    return response
