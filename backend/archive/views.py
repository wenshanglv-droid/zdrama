import hashlib
import secrets
from pathlib import Path
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied, NotFound
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.http import StreamingHttpResponse, JsonResponse
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
from .models import Production, Performance, Asset, Share, Audit, Edition, Person, StageRole, CastAssignment, AssetVersion, AccessProfile
from . import access
from .serializers import ProductionSerializer, PerformanceSerializer, AssetSerializer, ShareSerializer, EditionSerializer, PersonSerializer, StageRoleSerializer, CastSerializer, VersionSerializer, AccountSerializer

def csrf_failure(request, reason=""):
    if reason.startswith("Origin checking failed"):
        code, detail = "csrf_origin", "登录来源校验失败，请更新并重启试用服务，使用welcome.py显示的网址访问。"
    elif "CSRF cookie not set" in reason:
        code, detail = "csrf_cookie", "浏览器未发送验证Cookie，请在独立浏览器标签页打开HTTPS试用网址，允许站点Cookie后刷新。"
    elif reason.startswith("Referer checking failed"):
        code, detail = "csrf_referer", "请求来源验证失败，请在独立浏览器标签页打开试用网址后刷新。"
    else:
        code, detail = "csrf_token", "页面验证信息已失效，请刷新页面后重新登录。"
    response = JsonResponse({"code": code, "detail": detail}, status=403)
    response["Cache-Control"] = "no-store"
    return response

class Internal(permissions.BasePermission):
    def has_permission(self, request, view):
        return access.role(request.user) != 'external'

@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def session(request):
    response = Response({"csrfToken": get_token(request), "user": {"username": request.user.username, "internal": access.role(request.user) != "external", "role": access.role(request.user), "can_download": access.can_download(request.user)} if request.user.is_authenticated else None})
    response["Cache-Control"] = "private, no-store"
    return response

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

class CatalogPermission(Internal):
    def has_permission(self, request, view):
        return super().has_permission(request,view) and (request.method in permissions.SAFE_METHODS or access.role(request.user) in access.EDITORS)

class SuperuserPermission(permissions.BasePermission):
    def has_permission(self,request,view):
        return bool(request.user.is_authenticated and request.user.is_active and request.user.is_superuser)

def audit(request, action_name, obj, details=None):
    Audit.objects.create(actor=request.user,action=action_name,object_id=str(obj.pk),details=details or {})

class InternalViewSet(viewsets.ModelViewSet):
    permission_classes = [CatalogPermission]
    http_method_names = ['get','post','patch','head','options']
    @transaction.atomic
    def perform_create(self, serializer):
        obj=serializer.save()
        audit(self.request,f'create_{obj._meta.model_name}',obj)
    @transaction.atomic
    def perform_update(self,serializer):
        before=dict(self.get_serializer(serializer.instance).data)
        obj=serializer.save()
        audit(self.request,f'update_{obj._meta.model_name}',obj,{'before':before,'after':dict(self.get_serializer(obj).data)})

class ProductionViewSet(InternalViewSet):
    serializer_class=ProductionSerializer
    def get_queryset(self):return access.productions(self.request.user).order_by('-id')
    @transaction.atomic
    def perform_create(self,serializer):
        obj=serializer.save(created_by=self.request.user)
        Edition.objects.create(production=obj,name='默认版')
        audit(self.request,'create_production',obj)

class EditionViewSet(InternalViewSet):
    serializer_class=EditionSerializer
    def get_queryset(self):
        qs=Edition.objects.filter(production__in=access.productions(self.request.user)).select_related('production').order_by('-id')
        if self.request.query_params.get('production'):qs=qs.filter(production_id=self.request.query_params['production'])
        return qs

class PersonViewSet(InternalViewSet):
    serializer_class=PersonSerializer
    queryset=Person.objects.order_by('name','id')

class StageRoleViewSet(InternalViewSet):
    serializer_class=StageRoleSerializer
    def get_queryset(self):
        qs=StageRole.objects.filter(edition__production__in=access.productions(self.request.user)).select_related('edition').order_by('id')
        if self.request.query_params.get('edition'):qs=qs.filter(edition_id=self.request.query_params['edition'])
        return qs

class PerformanceViewSet(InternalViewSet):
    serializer_class=PerformanceSerializer
    def get_queryset(self):
        qs=Performance.objects.filter(production__in=access.productions(self.request.user)).select_related('production','edition').order_by('-starts_at')
        if self.request.query_params.get('production'):qs=qs.filter(production_id=self.request.query_params['production'])
        return qs

class CastViewSet(InternalViewSet):
    serializer_class=CastSerializer
    http_method_names=['get','post','patch','delete','head','options']
    def get_queryset(self):
        qs=CastAssignment.objects.filter(performance__production__in=access.productions(self.request.user)).select_related('person','stage_role').order_by('phase','id')
        if self.request.query_params.get('performance'):qs=qs.filter(performance_id=self.request.query_params['performance'])
        return qs
    @transaction.atomic
    def perform_destroy(self,instance):
        audit(self.request,'delete_cast',instance,dict(self.get_serializer(instance).data))
        instance.delete()

class AccountViewSet(InternalViewSet):
    permission_classes=[SuperuserPermission]
    serializer_class=AccountSerializer
    queryset=get_user_model().objects.order_by('username')
    @transaction.atomic
    def perform_update(self,serializer):
        before=dict(self.get_serializer(serializer.instance).data)
        obj=serializer.save()
        audit(self.request,'update_account',obj,{'before':before,'after':dict(self.get_serializer(obj).data)})


def checked_upload(request):
    uploaded=request.FILES.get('file')
    if not uploaded or not uploaded.size or uploaded.size>settings.MAX_UPLOAD_BYTES:
        raise serializers.ValidationError({'file':'请上传非空且不超过100MB的文件'})
    if len(uploaded.name)>255:raise serializers.ValidationError({'file':'文件名过长'})
    digest=hashlib.sha256()
    for chunk in uploaded.chunks():digest.update(chunk)
    uploaded.seek(0)
    return uploaded,digest.hexdigest()

class AssetViewSet(InternalViewSet):
    permission_classes=[Internal]
    serializer_class=AssetSerializer
    def get_queryset(self):
        qs=access.assets(self.request.user).select_related('performance__production','current_version').order_by('-created_at')
        q=self.request.query_params.get('q','')
        if q:
            qs=qs.filter(Q(title__icontains=q)|Q(current_version__original_name__icontains=q)|Q(performance__title__icontains=q)|Q(performance__production__title__icontains=q))
        if self.request.query_params.get('category'):qs=qs.filter(category=self.request.query_params['category'])
        if self.request.query_params.get('performance'):qs=qs.filter(performance_id=self.request.query_params['performance'])
        return qs
    @transaction.atomic
    def perform_create(self,serializer):
        if access.role(self.request.user) not in {'admin','archivist','business','finance'}:raise PermissionDenied('当前岗位不能上传资料')
        uploaded,digest=checked_upload(self.request)
        obj=serializer.save(owner=self.request.user,file=uploaded,original_name=uploaded.name,size=uploaded.size,sha256=digest)
        version=AssetVersion.objects.create(asset=obj,number=1,file=obj.file.name,original_name=obj.original_name,size=obj.size,sha256=obj.sha256,uploaded_by=self.request.user,note='首次上传')
        obj.current_version=version;obj.save(update_fields=['current_version'])
        audit(self.request,'upload',obj,{'version':version.pk})
    @transaction.atomic
    def perform_update(self,serializer):
        if not access.can_edit_asset(self.request.user,serializer.instance):raise PermissionDenied('无权编辑此资料')
        super().perform_update(serializer)
    @action(detail=True,methods=['get','post'])
    def versions(self,request,pk=None):
        obj=self.get_object()
        if request.method=='GET':return Response(VersionSerializer(obj.versions.all(),many=True).data)
        if not access.can_edit_asset(request.user,obj):raise PermissionDenied('无权上传新版本')
        uploaded,digest=checked_upload(request)
        note=str(request.data.get('note','')).strip()
        if not note or len(note)>1000:raise serializers.ValidationError({'note':'请填写1至1000字的版本说明'})
        with transaction.atomic():
            locked=Asset.objects.select_for_update().get(pk=obj.pk)
            if not access.can_edit_asset(request.user,locked):raise PermissionDenied('权限已变更')
            previous=locked.versions.order_by('-number').first()
            version=AssetVersion.objects.create(asset=locked,number=previous.number+1 if previous else 1,file=uploaded,original_name=uploaded.name,size=uploaded.size,sha256=digest,uploaded_by=request.user,note=note)
            locked.current_version=version;locked.save(update_fields=['current_version'])
            audit(request,'upload_version',locked,{'version':version.pk,'number':version.number,'note':note})
        return Response(VersionSerializer(version).data,status=201)
    def selected_version(self,obj,request):
        version_id=request.query_params.get('version')
        if version_id and not version_id.isdigit():raise serializers.ValidationError({'version':'版本ID必须是整数'})
        return get_object_or_404(obj.versions,pk=version_id) if version_id else get_object_or_404(obj.versions,pk=obj.current_version_id)
    @action(detail=True,methods=['get'])
    def content(self,request,pk=None):
        if not access.can_download(request.user):raise PermissionDenied('普通查看岗位仅允许预览')
        return deliver(self.selected_version(self.get_object(),request),request,download=True)
    @action(detail=True,methods=['get'])
    def preview(self,request,pk=None):
        return deliver(self.selected_version(self.get_object(),request),request,download=False)

class ShareCreate(serializers.Serializer):
    asset = serializers.IntegerField()
    version = serializers.IntegerField(required=False)
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
        qs = Share.objects.filter(asset__in=access.assets(self.request.user)).select_related("asset", "recipient", "version", "created_by").order_by("-id")
        return qs if self.request.user.is_superuser else qs.filter(created_by=self.request.user)
    def list(self, request):
        page = self.paginate_queryset(self.get_queryset())
        return self.get_paginated_response(self.get_serializer(page, many=True).data)
    def create(self, request):
        data = ShareCreate(data=request.data); data.is_valid(raise_exception=True); d=data.validated_data
        assets = access.assets(request.user)
        asset = get_object_or_404(assets, pk=d["asset"])
        if not access.can_share_asset(request.user,asset):raise PermissionDenied('无权分享此资料')
        version=get_object_or_404(asset.versions,pk=d.get('version',asset.current_version_id))
        recipient = get_user_model().objects.filter(username=d["recipient_username"], is_active=True).first()
        if recipient is None:
            raise serializers.ValidationError({"recipient_username": "接收账号不存在或不可用，请联系管理员创建"})
        if not d["allow_download"] and Path(version.original_name).suffix.lower() not in [".pdf", ".jpg", ".jpeg", ".png"]:
            raise serializers.ValidationError({"allow_download": "此格式尚不支持仅预览，请允许下载或等待后续转码功能"})
        token = secrets.token_urlsafe(32)
        obj = Share.objects.create(asset=asset, version=version, title_snapshot=asset.title, recipient=recipient, created_by=request.user, expires_at=d["expires_at"], allow_download=d["allow_download"], token_hash=hashlib.sha256(token.encode()).hexdigest())
        Audit.objects.create(actor=request.user, action="share_create", object_id=str(obj.pk))
        return Response({**self.get_serializer(obj).data, "url": f"/share/{token}"}, status=status.HTTP_201_CREATED)
    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        obj = self.get_object(); obj.revoked_at=timezone.now(); obj.save(update_fields=["revoked_at"])
        Audit.objects.create(actor=request.user, action="share_revoke", object_id=str(obj.pk))
        return Response({"ok": True})

def active_share(request, token):
    obj=get_object_or_404(Share.objects.select_related('asset','version','created_by'),token_hash=hashlib.sha256(token.encode()).hexdigest(),recipient=request.user,recipient__is_active=True,revoked_at__isnull=True,expires_at__gt=timezone.now())
    if not access.share_active(obj):raise NotFound('分享已失效')
    return obj

@api_view(["GET"])
def shared_detail(request, token):
    obj = active_share(request, token)
    return Response({"title": obj.title_snapshot, "version_number": obj.version.number, "original_name": obj.version.original_name, "expires_at": obj.expires_at, "allow_download": obj.allow_download})

@api_view(["GET"])
def shared_content(request, token):
    obj = active_share(request, token)
    download = request.query_params.get("download") == "1"
    if download and not obj.allow_download:
        return Response({"detail": "未授权下载"}, status=403)
    return deliver(obj.version, request, download=download, share=obj)

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
                if share:
                    fresh=Share.objects.select_related('asset','created_by').filter(pk=share.pk,recipient__is_active=True,revoked_at__isnull=True,expires_at__gt=timezone.now()).first()
                    if not fresh or not access.share_active(fresh):break
                else:
                    fresh_user=get_user_model().objects.get(pk=request.user.pk)
                    if not access.assets(fresh_user).filter(pk=asset.asset_id).exists():break
                    if download and not access.can_download(fresh_user):break
                chunk = source.read(64 * 1024)
                if not chunk: break
                yield chunk
    Audit.objects.create(actor=request.user, action="download" if download else "preview", object_id=str(asset.asset_id),details={"version":asset.pk})
    response = StreamingHttpResponse(stream(), content_type="application/octet-stream" if download else mime)
    response["Content-Disposition"] = content_disposition_header(download, asset.original_name)
    response["Cache-Control"] = "private, no-store"
    response["X-Accel-Buffering"] = "no"
    response["Content-Security-Policy"] = "sandbox"
    return response
