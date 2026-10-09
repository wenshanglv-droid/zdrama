"""Only seeds an empty, explicitly enabled demo database. Never resets users."""
import hashlib
import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from archive.models import Production, Performance, Asset


def pdf_bytes():
    content = b'BT /F1 20 Tf 72 740 Td (ZDRAMA - Fictional rehearsal archive) Tj 0 -40 Td /F1 12 Tf (Demo data only. No real troupe materials.) Tj ET'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
               b'<< /Length '+str(len(content)).encode()+b' >>\nstream\n'+content+b'\nendstream']
    output=b'%PDF-1.4\n'; offsets=[0]
    for i,obj in enumerate(objects,1):
        offsets.append(len(output)); output+=str(i).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
    position=len(output)
    output+=b'xref\n0 6\n0000000000 65535 f \n'
    output+=b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    return output+b'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n'+str(position).encode()+b'\n%%EOF\n'

class Command(BaseCommand):
    help='在隔离试用环境生成虚构资料；密码通过stdin JSON传入'
    def handle(self, *args, **options):
        if os.getenv('ZDRAMA_DEMO') != '1':
            raise CommandError('仅允许在显式启用的隔离试用环境执行')
        data=json.load(sys.stdin)
        if any(not isinstance(data.get(k),str) or len(data[k])<20 for k in ['admin_password','recipient_password']):
            raise CommandError('必须提供独立的强随机密码')
        User=get_user_model()
        if User.objects.exists():
            admin=User.objects.filter(username='demo_admin',is_superuser=True,is_active=True).first()
            guest=User.objects.filter(username='demo_guest',is_staff=False,is_active=True).first()
            if admin and guest and admin.check_password(data['admin_password']) and guest.check_password(data['recipient_password']):
                self.stdout.write('已有试用账号，保留原有数据和密码。'); return
            raise CommandError('数据库已有其他账号，拒绝覆盖或重置。')
        with transaction.atomic():
            admin=User.objects.create_superuser('demo_admin',password=data['admin_password'])
            User.objects.create_user('demo_guest',password=data['recipient_password'])
            for index,(title,genre,venue) in enumerate([
                ('长街灯火（模拟）','话剧','城市剧场'),
                ('山河回响（模拟）','音乐剧','艺术中心'),
                ('春日来信（模拟）','儿童剧','小剧场')],1):
                production=Production.objects.create(title=title,genre=genre,description='虚构演示档案，仅用于体验系统。')
                event=Performance.objects.create(production=production,title='首演场（模拟）',starts_at=datetime(2026,10,index+10,19,30,tzinfo=ZoneInfo('Asia/Shanghai')),venue=venue,cast_notes='演示演员甲、演示演员乙')
                payload=pdf_bytes()
                asset=Asset(title='排练剧本（模拟）',performance=event,category='剧本',owner=admin,original_name='演示剧本.pdf',size=len(payload),sha256=hashlib.sha256(payload).hexdigest())
                asset.file.save('演示剧本.pdf',ContentFile(payload),save=True)
        self.stdout.write('已创建模拟剧目、场次、PDF资料和两个试用账号。')
