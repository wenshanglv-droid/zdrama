from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from . import access
from .models import Production, Performance, Asset, Share, Edition, Person, StageRole, CastAssignment, AssetVersion, AccessProfile

class ProductionSerializer(serializers.ModelSerializer):
    class Meta:
        model=Production
        fields=['id','title','genre','description','created_at']

class EditionSerializer(serializers.ModelSerializer):
    production_title=serializers.CharField(source='production.title',read_only=True)
    class Meta:
        model=Edition
        fields=['id','production','production_title','name','description']
    def validate_production(self,value):
        if not access.productions(self.context['request'].user).filter(pk=value.pk).exists():
            raise serializers.ValidationError('无权访问该剧目')
        if self.instance and value.pk!=self.instance.production_id:
            raise serializers.ValidationError('制作版本不能移动到其他剧目')
        return value

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model=Person
        fields=['id','name','specialty','biography']

class StageRoleSerializer(serializers.ModelSerializer):
    edition_name=serializers.CharField(source='edition.name',read_only=True)
    class Meta:
        model=StageRole
        fields=['id','edition','edition_name','name','kind']
    def validate_edition(self,value):
        if not access.productions(self.context['request'].user).filter(pk=value.production_id).exists():
            raise serializers.ValidationError('无权访问该制作版本')
        if self.instance and value.pk!=self.instance.edition_id:
            raise serializers.ValidationError('角色不能移动到其他制作版本')
        return value

class PerformanceSerializer(serializers.ModelSerializer):
    production_title=serializers.CharField(source='production.title',read_only=True)
    edition_name=serializers.CharField(source='edition.name',read_only=True,default='')
    class Meta:
        model=Performance
        fields=['id','production','production_title','edition','edition_name','title','starts_at','venue','cast_notes']
    def validate(self,data):
        production=data.get('production',getattr(self.instance,'production',None))
        if not production or not access.productions(self.context['request'].user).filter(pk=production.pk).exists():
            raise serializers.ValidationError({'production':'无权管理该剧目'})
        if self.instance and production.pk!=self.instance.production_id:
            raise serializers.ValidationError({'production':'已有场次不能移动到其他剧目'})
        edition=data.get('edition',getattr(self.instance,'edition',None))
        if edition and edition.production_id!=production.pk:
            raise serializers.ValidationError({'edition':'制作版本不属于当前剧目'})
        if self.instance and self.instance.cast.exists() and (not edition or edition.pk!=self.instance.edition_id):
            raise serializers.ValidationError({'edition':'已有演职记录，不能切换制作版本'})
        if not edition:
            edition,_=Edition.objects.get_or_create(production=production,name='默认版')
        data['edition']=edition
        return data

class CastSerializer(serializers.ModelSerializer):
    person_name=serializers.CharField(source='person.name',read_only=True)
    role_name=serializers.CharField(source='stage_role.name',read_only=True)
    class Meta:
        model=CastAssignment
        fields=['id','performance','person','person_name','stage_role','role_name','phase','note']
    def validate(self,data):
        event=data.get('performance',getattr(self.instance,'performance',None))
        stage_role=data.get('stage_role',getattr(self.instance,'stage_role',None))
        if not event or not access.productions(self.context['request'].user).filter(pk=event.production_id).exists():
            raise serializers.ValidationError('无权访问该场次')
        if not stage_role or stage_role.edition_id!=event.edition_id:
            raise serializers.ValidationError({'stage_role':'角色必须属于该场次的制作版本'})
        if self.instance and event.pk!=self.instance.performance_id:
            raise serializers.ValidationError('演职记录不能移动到其他场次')
        return data

class VersionSerializer(serializers.ModelSerializer):
    uploaded_by_name=serializers.CharField(source='uploaded_by.username',read_only=True)
    class Meta:
        model=AssetVersion
        fields=['id','number','original_name','size','sha256','uploaded_by_name','note','created_at']

class AssetSerializer(serializers.ModelSerializer):
    performance_title=serializers.CharField(source='performance.title',read_only=True)
    production_title=serializers.CharField(source='performance.production.title',read_only=True)
    original_name=serializers.CharField(source='current_version.original_name',read_only=True,default='')
    size=serializers.IntegerField(source='current_version.size',read_only=True,default=0)
    sha256=serializers.CharField(source='current_version.sha256',read_only=True,default='')
    version_number=serializers.IntegerField(source='current_version.number',read_only=True,default=1)
    can_edit=serializers.SerializerMethodField()
    can_share=serializers.SerializerMethodField()
    def get_can_edit(self,obj): return access.can_edit_asset(self.context['request'].user,obj)
    def get_can_share(self,obj): return access.can_share_asset(self.context['request'].user,obj)
    class Meta:
        model=Asset
        fields=['id','title','description','performance','performance_title','production_title','category','financial','original_name','size','sha256','version_number','created_at','can_edit','can_share']
        read_only_fields=['financial']
    def validate(self,data):
        user=self.context['request'].user
        event=data.get('performance',getattr(self.instance,'performance',None))
        if not event or not access.productions(user).filter(pk=event.production_id).exists():
            raise serializers.ValidationError({'performance':'无权访问该场次'})
        if self.instance and event.pk!=self.instance.performance_id:
            raise serializers.ValidationError({'performance':'已有资料不能移动到其他场次'})
        category=data.get('category',getattr(self.instance,'category',None))
        financial=category=='票房' or bool(self.instance and self.instance.financial)
        if financial and access.role(user) not in {'admin','finance'}:
            raise serializers.ValidationError({'category':'财务资料仅管理员及财务岗位可管理'})
        if access.role(user)=='finance' and not financial:
            raise serializers.ValidationError({'category':'财务岗位只能编辑财务资料'})
        data['financial']=financial
        return data

class ShareSerializer(serializers.ModelSerializer):
    effective_active=serializers.SerializerMethodField()
    def get_effective_active(self,obj):
        return not obj.revoked_at and obj.expires_at>timezone.now() and access.share_active(obj)
    recipient_name=serializers.CharField(source='recipient.username',read_only=True)
    asset_title=serializers.CharField(source='title_snapshot',read_only=True)
    version_number=serializers.IntegerField(source='version.number',read_only=True)
    class Meta:
        model=Share
        fields=['id','asset','asset_title','version_number','recipient_name','expires_at','allow_download','revoked_at','created_at','effective_active']

class AccountSerializer(serializers.ModelSerializer):
    role=serializers.ChoiceField(choices=AccessProfile.ROLES)
    productions=serializers.PrimaryKeyRelatedField(queryset=Production.objects.all(),many=True,required=False)
    password=serializers.CharField(write_only=True,required=False,trim_whitespace=False)
    class Meta:
        model=get_user_model()
        fields=['id','username','password','is_active','role','productions']
    def to_representation(self,instance):
        return {'id':instance.pk,'username':instance.username,'is_active':instance.is_active,'role':access.role(instance) if instance.is_active else getattr(getattr(instance,'archive_access',None),'role','external'),'productions':list(Production.objects.filter(access_profiles__user=instance).values_list('pk',flat=True))}
    def validate(self,data):
        if self.instance and self.instance.is_superuser:
            raise serializers.ValidationError('超级管理员不能通过此接口修改')
        if self.instance and 'username' in data and data['username']!=self.instance.username:
            raise serializers.ValidationError('账号名称不能修改')
        password=data.get('password')
        if not self.instance and not password: raise serializers.ValidationError({'password':'请设置初始密码'})
        if password:
            try: validate_password(password,self.instance or get_user_model()(username=data.get('username','')))
            except DjangoValidationError as error: raise serializers.ValidationError({'password':error.messages})
        return data
    def create(self,data):
        role=data.pop('role'); productions=data.pop('productions',[])
        user=get_user_model().objects.create_user(**data,is_staff=role!='external')
        profile=AccessProfile.objects.create(user=user,role=role);profile.productions.set(productions)
        return user
    def update(self,instance,data):
        role=data.pop('role',None);productions=data.pop('productions',None);password=data.pop('password',None)
        for key,value in data.items():setattr(instance,key,value)
        if role is not None:instance.is_staff=role!='external'
        if password:instance.set_password(password)
        instance.save()
        profile,_=AccessProfile.objects.get_or_create(user=instance,defaults={'role':access.role(instance)})
        if role is not None:profile.role=role;profile.save(update_fields=['role'])
        if productions is not None:profile.productions.set(productions)
        return instance
