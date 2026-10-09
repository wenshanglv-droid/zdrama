"""Verify built frontend, same-origin API, database sessions and media volume."""
import http.cookiejar
import json
import secrets
import subprocess
import time
import urllib.error
import urllib.request

base = 'http://127.0.0.1:8080'
jar = http.cookiejar.CookieJar()
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
for attempt in range(30):
    try:
        response = client.open(base+'/api/session/', timeout=3)
        csrf = json.load(response)['csrfToken']
        break
    except (OSError, urllib.error.URLError):
        if attempt == 29: raise
        time.sleep(1)
assert b'<div id="app">' in client.open(base).read()
password = secrets.token_urlsafe(24)
# Password remains in stdin; no credentials in shell args or logs.
code = "from django.contrib.auth import get_user_model; get_user_model().objects.create_user('container_smoke',password="+repr(password)+",is_staff=True)"
subprocess.run(['docker','compose','exec','-T','backend','python','manage.py','shell'],input=code,text=True,check=True,capture_output=True)
request = urllib.request.Request(base+'/api/login/',data=json.dumps({'username':'container_smoke','password':password}).encode(),headers={'Content-Type':'application/json','X-CSRFToken':csrf})
assert client.open(request).status == 200
session = json.load(client.open(base+'/api/session/'))
assert session['user']['internal'] is True
code = "from django.conf import settings; from pathlib import Path; p=Path(settings.MEDIA_ROOT); p.mkdir(parents=True,exist_ok=True); f=p/'.ci-write-probe'; f.write_text('ok'); assert f.read_text()=='ok'; f.unlink()"
subprocess.run(['docker','compose','exec','-T','backend','python','manage.py','shell'],input=code,text=True,check=True,capture_output=True)
print('PASS: built frontend, API session, PostgreSQL login and writable media volume')
