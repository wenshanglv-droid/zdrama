"""Single permission policy used by records, versions, search and shares."""
from django.db.models import Q
from .models import Production, Asset, AccessProfile

EDITORS={'admin','archivist','business'}

def role(user):
    if not user.is_authenticated or not user.is_active: return 'external'
    if user.is_superuser: return 'admin'
    if not user.is_staff: return 'external'
    profile=AccessProfile.objects.filter(user=user).first()
    return profile.role if profile else 'business'

def assigned_ids(user):
    return Production.objects.filter(access_profiles__user=user).values_list('pk',flat=True)

def productions(user):
    if role(user)=='admin': return Production.objects.all()
    if role(user)=='external': return Production.objects.none()
    return Production.objects.filter(Q(pk__in=assigned_ids(user))|Q(created_by=user)|Q(performances__assets__owner=user)).distinct()

def assets(user):
    if role(user)=='admin': return Asset.objects.all()
    if role(user)=='external': return Asset.objects.none()
    queryset=Asset.objects.filter(Q(owner=user)|Q(performance__production_id__in=assigned_ids(user)))
    if role(user)!='finance': queryset=queryset.filter(financial=False).exclude(category='票房')
    return queryset.distinct()

def can_edit_asset(user,asset):
    job=role(user)
    if job=='admin': return True
    if not assets(user).filter(pk=asset.pk).exists(): return False
    if asset.financial or asset.category=='票房': return job=='finance'
    return job=='archivist' or (job=='business' and asset.owner_id==user.pk)

def can_share_asset(user,asset):
    return role(user)=='admin' or (not asset.financial and asset.category!='票房' and can_edit_asset(user,asset))

def can_download(user):
    return role(user) in {'admin','archivist','business','finance'}

def share_active(share):
    return share.version_id is not None and share.created_by.is_active and can_share_asset(share.created_by,share.asset)
