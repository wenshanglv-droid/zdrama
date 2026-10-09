import {reactive} from 'vue'
import {pages} from './catalog'
const key='zdrama-ui-review-v1'
function initial(){return {rows:Object.fromEntries(pages.map(p=>[p.id,structuredClone(p.rows)])),notes:{} as Record<string,string>,reviews:{} as Record<string,string>,drafts:{} as Record<string,any>}}
function restore(){try{const value=JSON.parse(localStorage.getItem(key)||'null');return value?.rows?{...initial(),...value}:initial()}catch{return initial()}}
export const state=reactive(restore())
export function persist(){try{localStorage.setItem(key,JSON.stringify(state))}catch{/* in-memory demo still works */}}
export function reset(){Object.assign(state,initial());persist()}
export function downloadDemo(name:string,data:unknown){const blob=new Blob([typeof data==='string'?data:JSON.stringify(data,null,2)],{type:'text/plain;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();URL.revokeObjectURL(url)}
