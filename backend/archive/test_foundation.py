import tempfile
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase, override_settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from rest_framework.test import APIClient
from .models import Production, Edition, Performance, Person, StageRole, Asset, AccessProfile, Audit


class FoundationTests(TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        setting=override_settings(MEDIA_ROOT=self.directory.name);setting.enable();self.addCleanup(setting.disable)
        User=get_user_model()
        self.admin=User.objects.create_superuser('admin',password='Test-Password-42!')
        self.business=User.objects.create_user('business',is_staff=True)
        self.guest=User.objects.create_user('guest')
        self.client=APIClient();self.client.force_login(self.admin)
        self.production=Production.objects.create(title='剧目',created_by=self.admin)
        self.edition=Edition.objects.create(production=self.production,name='首演版')
        self.event=Performance.objects.create(production=self.production,edition=self.edition,title='首演',starts_at=timezone.now(),venue='剧场')
        self.asset=self.upload()
    def upload(self,category='剧本'):
        response=self.client.post('/api/assets/',{'performance':self.event.pk,'title':'第一稿','category':category,'file':SimpleUploadedFile('v1.pdf',b'%PDF-v1')},format='multipart')
        self.assertEqual(response.status_code,201,response.data)
        return Asset.objects.get(pk=response.data['id'])
    def grant(self,user,role,scope=True):
        profile,_=AccessProfile.objects.update_or_create(user=user,defaults={'role':role})
        profile.productions.set([self.production] if scope else [])
        self.client.force_login(user)
        return profile
    def share(self,asset=None,**kwargs):
        return self.client.post('/api/shares/',{'asset':(asset or self.asset).pk,'recipient_username':'guest','expires_at':(timezone.now()+timezone.timedelta(days=1)).isoformat(),**kwargs},format='json')
    def test_immutable_versions_and_pinned_share(self):
        share=self.share();self.assertEqual(share.status_code,201,share.data)
        old=self.asset.current_version
        response=self.client.post(f'/api/assets/{self.asset.pk}/versions/',{'file':SimpleUploadedFile('v2.pdf',b'%PDF-v2'),'note':'修改第二幕'},format='multipart')
        self.assertEqual(response.status_code,201,response.data);self.assertEqual(response.data['number'],2)
        self.asset.refresh_from_db();self.assertNotEqual(old.file.name,self.asset.current_version.file.name)
        self.assertEqual(self.share().data['version_number'],2)
        self.assertEqual(self.share(version=old.pk).data['version_number'],1)
        self.client.patch(f'/api/assets/{self.asset.pk}/',{'title':'新名称'},format='json')
        self.client.force_login(self.guest)
        path=share.data['url'].replace('/share/','/api/shared/')+'/'
        self.assertEqual(self.client.get(path).data['title'],'第一稿')
        self.assertEqual(b''.join(self.client.get(path+'content/').streaming_content),b'%PDF-v1')
        self.client.force_login(self.admin)
        response=self.client.get(f'/api/assets/{self.asset.pk}/content/')
        self.assertEqual(b''.join(response.streaming_content),b'%PDF-v2')
        self.assertEqual(self.client.patch(f'/api/assets/{self.asset.pk}/versions/',{'note':'overwrite'}).status_code,405)
    def test_version_validation_and_cross_asset_selection(self):
        other=self.upload()
        self.assertEqual(self.share(version=other.current_version_id).status_code,404)
        self.assertEqual(self.client.get(f'/api/assets/{self.asset.pk}/preview/?version={other.current_version_id}').status_code,404)
        self.assertEqual(self.client.post(f'/api/assets/{self.asset.pk}/versions/',{'file':SimpleUploadedFile('v2.pdf',b'%PDF-v2')},format='multipart').status_code,400)
        self.assertEqual(self.asset.versions.count(),1)
    def test_roles_and_financial_isolation(self):
        financial=self.upload('票房')
        self.client.patch(f'/api/assets/{financial.pk}/',{'category':'其他'},format='json')
        financial.refresh_from_db();self.assertTrue(financial.financial)
        profile=self.grant(self.business,'viewer')
        self.assertEqual(self.client.get('/api/assets/?q=第一稿').data['count'],1)
        self.assertEqual(self.client.get(f'/api/assets/{financial.pk}/').status_code,404)
        self.assertEqual(self.client.get(f'/api/assets/{financial.pk}/versions/').status_code,404)
        response=self.client.get(f'/api/assets/{self.asset.pk}/preview/');self.assertEqual(response.status_code,200);list(response.streaming_content)
        self.assertEqual(self.client.get(f'/api/assets/{self.asset.pk}/content/').status_code,403)
        self.assertEqual(self.client.patch(f'/api/assets/{self.asset.pk}/',{'title':'x'}).status_code,403)
        self.assertEqual(self.client.post('/api/productions/',{'title':'x'}).status_code,403)
        self.assertEqual(self.share().status_code,403)
        self.grant(self.business,'finance')
        self.assertEqual(self.client.get('/api/assets/').data['count'],2)
        self.assertEqual(self.client.patch(f'/api/assets/{financial.pk}/',{'title':'财务修订'}).status_code,200)
        self.assertEqual(self.share(financial).status_code,403)
        self.assertEqual(self.client.patch(f'/api/assets/{self.asset.pk}/',{'title':'x'}).status_code,400)
        self.grant(self.business,'business')
        self.assertEqual(self.client.patch(f'/api/assets/{self.asset.pk}/',{'title':'x'}).status_code,403)
        own=self.upload();self.assertEqual(self.client.patch(f'/api/assets/{own.pk}/',{'title':'修订'}).status_code,200)
        self.grant(self.business,'archivist')
        self.assertEqual(self.client.patch(f'/api/assets/{self.asset.pk}/',{'title':'档案修订'}).status_code,200)
        self.assertTrue(Audit.objects.filter(action='update_asset',details__before__title='第一稿').exists())
    def test_scope_removal_and_downgrade_invalidate_shares(self):
        profile=self.grant(self.business,'archivist')
        response=self.share();self.assertEqual(response.status_code,201)
        url=response.data['url'].replace('/share/','/api/shared/')+'/'
        self.client.force_login(self.guest);self.assertEqual(self.client.get(url).status_code,200)
        profile.productions.clear();self.assertEqual(self.client.get(url).status_code,404)
        profile.productions.add(self.production);profile.role='viewer';profile.save()
        self.assertEqual(self.client.get(url).status_code,404)
        self.client.force_login(self.business)
        profile.productions.clear()
        for endpoint in ['assets','productions','performances','editions','stage-roles','cast']:
            self.assertEqual(self.client.get(f'/api/{endpoint}/').data['count'],0)
        self.assertEqual(self.client.get(f'/api/assets/{self.asset.pk}/versions/').status_code,404)
    def test_editions_cast_and_audit(self):
        second=Edition.objects.create(production=self.production,name='复排版')
        role=StageRole.objects.create(edition=self.edition,name='主角')
        foreign=StageRole.objects.create(edition=second,name='主角')
        person=Person.objects.create(name='甲')
        data={'performance':self.event.pk,'person':person.pk,'stage_role':role.pk,'phase':'planned'}
        response=self.client.post('/api/cast/',data);self.assertEqual(response.status_code,201,response.data)
        self.assertEqual(self.client.post('/api/cast/',{**data,'phase':'actual'}).status_code,201)
        self.assertEqual(self.client.post('/api/cast/',{**data,'stage_role':foreign.pk}).status_code,400)
        self.assertEqual(self.client.post('/api/cast/',data).status_code,400)
        self.assertEqual(self.client.patch(f'/api/performances/{self.event.pk}/',{'edition':second.pk}).status_code,400)
        self.assertEqual(self.client.patch(f'/api/performances/{self.event.pk}/',{'edition':None},format='json').status_code,400)
        self.assertEqual(self.client.patch(f"/api/cast/{response.data['id']}/",{'note':'替补说明'}).status_code,200)
        self.assertEqual(self.client.delete(f"/api/cast/{response.data['id']}/").status_code,204)
        self.assertTrue(Audit.objects.filter(action='delete_cast',details__note='替补说明').exists())
    def test_accounts_only_admin_and_password_not_audited(self):
        data={'username':'reader','password':'Strong-Initial-42!','role':'viewer','productions':[self.production.pk]}
        response=self.client.post('/api/accounts/',data,format='json');self.assertEqual(response.status_code,201,response.data)
        self.assertNotIn('password',response.data)
        account=get_user_model().objects.get(pk=response.data['id']);self.assertTrue(account.check_password(data['password']))
        self.assertEqual(self.client.patch(f'/api/accounts/{account.pk}/',{'is_active':False},format='json').status_code,200)
        self.assertNotIn(data['password'],str(list(Audit.objects.values('details'))))
        self.assertEqual(self.client.patch(f'/api/accounts/{self.admin.pk}/',{'role':'external'}).status_code,400)
        self.grant(self.business,'archivist')
        self.assertEqual(self.client.get('/api/accounts/').status_code,403)
        self.assertEqual(self.client.post('/api/accounts/',data,format='json').status_code,403)


class HistoryMigrationTests(TransactionTestCase):
    def test_legacy_files_and_links_preserved(self):
        executor=MigrationExecutor(connection)
        target=[('archive','0001_initial')]
        executor.migrate(target)
        old=executor.loader.project_state(target).apps
        User=old.get_model('auth','User');owner=User.objects.create(username='legacy',is_staff=True);guest=User.objects.create(username='legacy_guest')
        p=old.get_model('archive','Production').objects.create(title='历史剧目')
        event=old.get_model('archive','Performance').objects.create(production=p,title='历史首演',starts_at=timezone.now(),venue='剧场')
        asset=old.get_model('archive','Asset').objects.create(performance=event,owner=owner,title='旧剧本',category='剧本',file='originals/unchanged',original_name='原件.pdf',size=42,sha256='a'*64)
        share=old.get_model('archive','Share').objects.create(asset=asset,recipient=guest,created_by=owner,token_hash='b'*64,expires_at=timezone.now()+timezone.timedelta(days=1))
        try:
            executor=MigrationExecutor(connection);target=[('archive','0003_preserve_archive_history')];executor.migrate(target)
            new=executor.loader.project_state(target).apps
            migrated=new.get_model('archive','Asset').objects.get(pk=asset.pk)
            version=new.get_model('archive','AssetVersion').objects.get(pk=migrated.current_version_id)
            self.assertEqual(version.file.name,'originals/unchanged');self.assertEqual(version.created_at,asset.created_at)
            self.assertEqual(version.sha256,'a'*64)
            saved=new.get_model('archive','Share').objects.get(pk=share.pk)
            self.assertEqual(saved.token_hash,'b'*64);self.assertEqual(saved.version_id,version.pk);self.assertEqual(saved.title_snapshot,'旧剧本')
            self.assertIsNotNone(new.get_model('archive','Performance').objects.get(pk=event.pk).edition_id)
            self.assertEqual(new.get_model('archive','AccessProfile').objects.get(user_id=owner.pk).role,'business')
        finally:
            executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes())
