let csrf = ''
export async function api(path:string, data?:unknown, form=false):Promise<any> {
  const headers:Record<string,string> = {}
  if(data !== undefined) {headers['X-CSRFToken']=csrf; if(!form) headers['Content-Type']='application/json'}
  const res=await fetch('/api/'+path,{method:data===undefined?'GET':'POST',credentials:'same-origin',headers,body:data===undefined?undefined:form?data as FormData:JSON.stringify(data)})
  const value=await res.json()
  if(!res.ok) throw new Error(typeof value.detail==='string'?value.detail:JSON.stringify(value))
  if(value.csrfToken) csrf=value.csrfToken
  return value
}
export async function all(path:string) {
  const rows:any[]=[];let page=1
  while(true) {const r=await api(path+(path.includes('?')?'&':'?')+'page='+page);rows.push(...r.results);if(!r.next) return rows;page++}
}
