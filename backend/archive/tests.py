import hashlib
import tempfile
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient
from .models import Production, Performance, Asset, Share, Audit

class ArchiveTests(TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.setting=override_settings(MEDIA_ROOT=self.temp.name)
        self.setting.enable();self.addCleanup(self.temp.cleanup);self.addCleanup(self.setting.disable)
        User=get_user_model()
        self.owner=User.objects.create_user("owner",password="test-secret-123",is_staff=True)
        self.other=User.objects.create_user("other",password="test-secret-123",is_staff=True)
        self.external=User.objects.create_user("external",password="test-secret-123")
        self.client=APIClient();self.client.force_login(self.owner)
        self.p=Production.objects.create(title="试演剧目")
        self.event=Performance.objects.create(production=self.p,title="首演",starts_at=timezone.now(),venue="剧场")
        r=self.client.post("/api/assets/",{"title":"剧本","performance":self.event.pk,"category":"剧本","file":SimpleUploadedFile("script.pdf",b"%PDF-1.4 test")},format="multipart")
        self.assertEqual(r.status_code,201,r.data);self.asset=Asset.objects.get(pk=r.data["id"])
    def new_share(self,**kwargs):
        data={"asset":self.asset.pk,"recipient_username":"external","expires_at":(timezone.now()+timezone.timedelta(days=1)).isoformat(),"allow_download":False,**kwargs}
        r=self.client.post("/api/shares/",data,format="json")
        self.assertEqual(r.status_code,201,r.data)
        return r.data["url"].split("/")[-1],r.data["id"]
    def test_upload_hash_and_private_storage(self):
        self.assertEqual(self.asset.sha256,hashlib.sha256(b"%PDF-1.4 test").hexdigest())
        self.assertNotIn("script.pdf",self.asset.file.name)
        self.assertEqual(self.client.get("/media/"+self.asset.file.name).status_code,404)
    def test_other_staff_cannot_list_download_or_share_asset(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get("/api/assets/").data["count"],0)
        self.assertEqual(self.client.get(f"/api/assets/{self.asset.pk}/content/").status_code,404)
        r=self.client.post("/api/shares/",{"asset":self.asset.pk,"recipient_username":"external","expires_at":(timezone.now()+timezone.timedelta(days=1)).isoformat()},format="json")
        self.assertEqual(r.status_code,404)
    def test_external_cannot_access_internal_records(self):
        self.client.force_login(self.external)
        for url in ["productions/","performances/","assets/","shares/"]:
            self.assertEqual(self.client.get("/api/"+url).status_code,403)
    def test_share_recipient_preview_download_and_revoke(self):
        token,pk=self.new_share()
        url=f"/api/shared/{token}/"
        self.assertEqual(self.client.get(url).status_code,404)
        self.client.force_login(self.external)
        self.assertEqual(self.client.get(url).status_code,200)
        response=self.client.get(url+"content/")
        self.assertEqual(b"".join(response.streaming_content),b"%PDF-1.4 test")
        self.assertEqual(response["Cache-Control"],"private, no-store")
        self.assertEqual(self.client.get(url+"content/?download=1").status_code,403)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(f"/api/shares/{pk}/revoke/",{}).status_code,200)
        self.client.force_login(self.external)
        self.assertEqual(self.client.get(url).status_code,404)
        self.assertEqual(self.client.get(url+"content/").status_code,404)
    def test_expired_and_disabled_recipient(self):
        token,pk=self.new_share()
        Share.objects.filter(pk=pk).update(expires_at=timezone.now()-timezone.timedelta(seconds=1))
        self.client.force_login(self.external)
        self.assertEqual(self.client.get(f"/api/shared/{token}/").status_code,404)
    def test_inflight_stream_stops_when_share_revoked(self):
        self.asset.file.save("large.pdf",SimpleUploadedFile("large.pdf",b"x"*200000))
        token,pk=self.new_share();self.client.force_login(self.external)
        response=self.client.get(f"/api/shared/{token}/content/");iterator=iter(response.streaming_content)
        self.assertEqual(len(next(iterator)),65536)
        Share.objects.filter(pk=pk).update(revoked_at=timezone.now())
        self.assertEqual(list(iterator),[])
    def test_download_requires_explicit_permission(self):
        token,_=self.new_share(allow_download=True);self.client.force_login(self.external)
        response=self.client.get(f"/api/shared/{token}/content/?download=1")
        self.assertEqual(response.status_code,200)
        self.assertIn("attachment",response["Content-Disposition"])
        self.assertEqual(b"".join(response.streaming_content),b"%PDF-1.4 test")
    def test_invalid_share_expiry_and_no_token_in_list(self):
        self.new_share()
        self.assertNotIn("token_hash",self.client.get("/api/shares/").data["results"][0])
        response=self.client.post("/api/shares/",{"asset":self.asset.pk,"recipient_username":"external","expires_at":timezone.now().isoformat()},format="json")
        self.assertEqual(response.status_code,400)
    def test_oversized_and_empty_upload_rejected(self):
        with override_settings(MAX_UPLOAD_BYTES=1):
            r=self.client.post("/api/assets/",{"title":"x","performance":self.event.pk,"category":"其他","file":SimpleUploadedFile("x.txt",b"xx")},format="multipart")
        self.assertEqual(r.status_code,400)
    def test_login_requires_csrf_and_works_with_token(self):
        c=APIClient(enforce_csrf_checks=True)
        self.assertEqual(c.post("/api/login/",{"username":"owner","password":"test-secret-123"}).status_code,403)
        token=c.get("/api/session/").data["csrfToken"]
        r=c.post("/api/login/",{"username":"owner","password":"test-secret-123"},HTTP_X_CSRFTOKEN=token)
        self.assertEqual(r.status_code,200)
        self.assertEqual(c.get("/api/session/").data["user"]["username"],"owner")
    def test_unauthenticated_denied_and_audit_written(self):
        self.client.logout()
        self.assertEqual(self.client.get("/api/assets/").status_code,403)
        self.assertTrue(Audit.objects.filter(action="upload",actor=self.owner).exists())
