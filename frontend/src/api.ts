let csrf = ''
export async function api(path:string, data?:unknown, form=false, method?:string):Promise<any> {
  const headers:Record<string,string> = {}
  if(data !== undefined) {headers['X-CSRFToken']=csrf; if(!form) headers['Content-Type']='application/json'}
  const res=await fetch('/api/'+path,{method:method??(data===undefined?'GET':'POST'),credentials:'same-origin',cache:'no-store',headers,body:data===undefined?undefined:form?data as FormData:JSON.stringify(data)})
  if(res.status===204) return null
  const isJSON=res.headers.get('content-type')?.includes('application/json')
  if(!isJSON) throw new Error(res.ok?'服务返回了非预期数据':`请求失败（${res.status}），请检查登录状态或服务配置`)
  const value=await res.json()
  if(!res.ok) throw new Error(typeof value.detail==='string'?value.detail:JSON.stringify(value))
  if(value.csrfToken) csrf=value.csrfToken
  return value
}
export async function all(path:string) {
  const rows:any[]=[];let page=1
  while(true) {const r=await api(path+(path.includes('?')?'&':'?')+'page='+page);rows.push(...r.results);if(!r.next) return rows;page++}
}
