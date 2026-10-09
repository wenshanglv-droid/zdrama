import uuid
from django.conf import settings
from django.db import models

def original_path(instance, filename):
    return f"originals/{uuid.uuid4().hex}"

class Production(models.Model):
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Performance(models.Model):
    production = models.ForeignKey(Production, on_delete=models.PROTECT, related_name="performances")
    title = models.CharField(max_length=200)
    starts_at = models.DateTimeField()
    venue = models.CharField(max_length=200)
    cast_notes = models.TextField(blank=True)

class Asset(models.Model):
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
    token_hash = models.CharField(max_length=64, unique=True)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="received_shares")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_shares")
    expires_at = models.DateTimeField()
    allow_download = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Audit(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=40)
    object_id = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
