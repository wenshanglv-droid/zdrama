import uuid
from django.conf import settings
from django.db import models

def original_path(instance, filename):
    return f"originals/{uuid.uuid4().hex}"

class Production(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Performance(models.Model):
    edition = models.ForeignKey("Edition", null=True, blank=True, on_delete=models.PROTECT, related_name="performances")
    production = models.ForeignKey(Production, on_delete=models.PROTECT, related_name="performances")
    title = models.CharField(max_length=200)
    starts_at = models.DateTimeField()
    venue = models.CharField(max_length=200)
    cast_notes = models.TextField(blank=True)

class Asset(models.Model):
    description = models.TextField(blank=True)
    financial = models.BooleanField(default=False)
    current_version = models.ForeignKey("AssetVersion", null=True, blank=True, on_delete=models.PROTECT, related_name="current_for")
    CATEGORIES = [(v,v) for v in ["剧本", "照片", "录像", "音频", "票房", "其他"]]
    title = models.CharField(max_length=200)
    performance = models.ForeignKey(Performance, on_delete=models.PROTECT, related_name="assets")
    category = models.CharField(max_length=20, choices=CATEGORIES)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    file = models.FileField(upload_to=original_path)
    original_name = models.CharField(max_length=255)
    size = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

class Share(models.Model):
    version = models.ForeignKey("AssetVersion", null=True, blank=True, on_delete=models.PROTECT)
    title_snapshot = models.CharField(max_length=200, blank=True)
    token_hash = models.CharField(max_length=64, unique=True)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="received_shares")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_shares")
    expires_at = models.DateTimeField()
    allow_download = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Audit(models.Model):
    details = models.JSONField(default=dict, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=40)
    object_id = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

class Edition(models.Model):
    production = models.ForeignKey(Production, on_delete=models.PROTECT, related_name='editions')
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['production','name'], name='edition_name_unique')]

class Person(models.Model):
    name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100, blank=True)
    biography = models.TextField(blank=True)

class StageRole(models.Model):
    edition = models.ForeignKey(Edition, on_delete=models.PROTECT, related_name='stage_roles')
    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=[('actor','演员角色'),('crew','工作人员岗位')], default='actor')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['edition','name','kind'], name='stage_role_unique')]

class CastAssignment(models.Model):
    performance = models.ForeignKey(Performance, on_delete=models.PROTECT, related_name='cast')
    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name='assignments')
    stage_role = models.ForeignKey(StageRole, on_delete=models.PROTECT)
    phase = models.CharField(max_length=10, choices=[('planned','计划'),('actual','实际')])
    note = models.CharField(max_length=500, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['performance','person','stage_role','phase'], name='cast_assignment_unique')]

class AssetVersion(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='versions')
    number = models.PositiveIntegerField()
    file = models.FileField(upload_to=original_path)
    original_name = models.CharField(max_length=255)
    size = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    note = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-number']
        constraints = [models.UniqueConstraint(fields=['asset','number'], name='asset_version_number_unique')]

class AccessProfile(models.Model):
    ROLES = [('archivist','档案员'),('business','演出业务'),('finance','财务'),('viewer','普通查看'),('external','外部接收人')]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='archive_access')
    role = models.CharField(max_length=20, choices=ROLES, default='external')
    productions = models.ManyToManyField(Production, blank=True, related_name='access_profiles')
