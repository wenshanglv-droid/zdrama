from django.conf import settings
from django.db import migrations

def migrate(apps, schema_editor):
    Edition=apps.get_model('archive','Edition')
    Performance=apps.get_model('archive','Performance')
    Asset=apps.get_model('archive','Asset')
    Version=apps.get_model('archive','AssetVersion')
    Share=apps.get_model('archive','Share')
    Profile=apps.get_model('archive','AccessProfile')
    User=apps.get_model(settings.AUTH_USER_MODEL)
    for event in Performance.objects.filter(edition__isnull=True).iterator():
        edition,_=Edition.objects.get_or_create(production_id=event.production_id,name='历史默认版')
        event.edition_id=edition.pk;event.save(update_fields=['edition'])
    for asset in Asset.objects.filter(current_version__isnull=True).iterator():
        version=Version.objects.create(asset_id=asset.pk,number=1,file=asset.file.name,original_name=asset.original_name,size=asset.size,sha256=asset.sha256,uploaded_by_id=asset.owner_id,note='历史资料迁移：保留原文件路径')
        Version.objects.filter(pk=version.pk).update(created_at=asset.created_at)
        asset.current_version_id=version.pk;asset.financial=asset.category=='票房';asset.save(update_fields=['current_version','financial'])
        Share.objects.filter(asset_id=asset.pk,version__isnull=True).update(version_id=version.pk,title_snapshot=asset.title)
    for user in User.objects.all().iterator():
        Profile.objects.get_or_create(user_id=user.pk,defaults={'role':'business' if user.is_staff else 'external'})

class Migration(migrations.Migration):
    dependencies=[('archive','0002_person_asset_description_asset_financial_and_more')]
    operations=[migrations.RunPython(migrate,migrations.RunPython.noop)]
