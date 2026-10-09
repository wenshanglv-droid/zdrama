"""Exercise the real Nginx/API chain with Codespaces-rewritten Origin."""
import json
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError

root = Path(__file__).resolve().parents[1]/'.codespaces'
credentials = json.loads((root/'access.json').read_text())
host = urlparse((root/'ready').read_text()).netloc
cookies = SimpleCookie()

def request(path, data=None, origin=None, token=None):
    headers={'Host':host}
    if cookies: headers['Cookie']='; '.join(f'{key}={value.value}' for key,value in cookies.items())
    if origin: headers['Origin']=origin
    if token: headers['X-CSRFToken']=token
    if data is not None: headers['Content-Type']='application/json'
    req=Request('http://127.0.0.1:8080/api/'+path,headers=headers,data=None if data is None else json.dumps(data).encode())
    try: response=urlopen(req,timeout=10)
    except HTTPError as error: response=error
    with response:
        for cookie in response.headers.get_all('Set-Cookie',[]): cookies.load(cookie)
        return response.status,json.load(response)

status,data=request('session/')
assert status==200
token=data['csrfToken']
login={'username':'demo_admin','password':credentials['admin_password']}
status,data=request('login/',login,'https://untrusted.example',token)
assert status==403 and data['code']=='csrf_origin'
status,data=request('login/',login,'http://localhost:8080')
assert status==403
status,data=request('login/',login,'http://localhost:8080',token)
assert status==200, (status,data)
status,data=request('session/')
assert status==200 and data['user']['username']=='demo_admin'
print('PASS: proxy origin login, CSRF token enforcement and untrusted origin rejection')
