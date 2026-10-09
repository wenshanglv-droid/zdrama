<script setup lang="ts">
import {ref,onMounted,computed} from 'vue'
import {ElMessage} from 'element-plus'
import {api,all} from './api'
const props=defineProps<{kind:string,id:number,user:any}>()
const emit=defineEmits(['updated','share'])
const record=ref<any>(null),editions=ref<any[]>([]),roles=ref<any[]>([]),people=ref<any[]>([]),cast=ref<any[]>([]),versions=ref<any[]>([])
const busy=ref(false),edition=ref<any>({name:'',description:''}),stage=ref<any>({edition:null,name:'',kind:'actor'}),assignment=ref<any>({person:null,stage_role:null,phase:'actual',note:''})
const file=ref<File|null>(null),note=ref('')
const editable=computed(()=>props.kind==='assets'?record.value?.can_edit:['admin','archivist','business'].includes(props.user.role))
async function run(fn:()=>Promise<void>){busy.value=true;try{await fn()}catch(e){ElMessage.error((e as Error).message)}finally{busy.value=false}}
async function load(){
 record.value=await api(`${props.kind}/${props.id}/`)
 if(props.kind==='productions'){editions.value=await all(`editions/?production=${props.id}`);roles.value=(await all('stage-roles/')).filter(r=>editions.value.some(e=>e.id===r.edition))}
 if(props.kind==='performances'){[editions.value,people.value,cast.value]=await Promise.all([all(`editions/?production=${record.value.production}`),all('people/'),all(`cast/?performance=${props.id}`)]);roles.value=await all(`stage-roles/?edition=${record.value.edition}`)}
 if(props.kind==='assets')versions.value=await api(`assets/${props.id}/versions/`)
}
onMounted(()=>run(load))
async function changed(){await load();emit('updated');ElMessage.success('已保存')}
function save(){run(async()=>{const keys=props.kind==='productions'?['title','genre','description']:props.kind==='performances'?['title','edition','starts_at','venue','cast_notes']:['title','description','category'];const data=Object.fromEntries(keys.map(k=>[k,record.value[k]]));await api(`${props.kind}/${props.id}/`,data,false,'PATCH');await changed()})}
function addEdition(){run(async()=>{await api('editions/',{...edition.value,production:props.id});edition.value={name:'',description:''};await changed()})}
function editEdition(e:any){run(async()=>{await api(`editions/${e.id}/`,{name:e.name,description:e.description},false,'PATCH');await changed()})}
function addRole(){run(async()=>{await api('stage-roles/',stage.value);stage.value.name='';await changed()})}
function editRole(r:any){run(async()=>{await api(`stage-roles/${r.id}/`,{name:r.name,kind:r.kind},false,'PATCH');await changed()})}
function addCast(){run(async()=>{await api('cast/',{...assignment.value,performance:props.id});await changed()})}
function removeCast(id:number){run(async()=>{await api(`cast/${id}/`,{},false,'DELETE');await changed()})}
function editCast(c:any){run(async()=>{await api(`cast/${c.id}/`,{person:c.person,stage_role:c.stage_role,phase:c.phase,note:c.note},false,'PATCH');await changed()})}
function upload(){run(async()=>{if(!file.value)throw new Error('请选择新版本文件');const f=new FormData();f.append('file',file.value);f.append('note',note.value);await api(`assets/${props.id}/versions/`,f,true);note.value='';await changed()})}
function previewable(name:string){return /\.(pdf|jpe?g|png)$/i.test(name)}
</script>
<template>
<div v-loading="busy" v-if="record" class="details">
 <el-tag>{{kind==='assets'?'资料档案':kind==='productions'?'剧目档案':'演出档案'}}</el-tag><h2>{{record.title}}</h2>
 <el-form label-position="top" @submit.prevent="save" :disabled="!editable">
 <el-form-item label="名称"><el-input v-model="record.title" aria-label="档案名称"/></el-form-item>
 <template v-if="kind==='productions'"><el-form-item label="剧种"><el-input v-model="record.genre"/></el-form-item><el-form-item label="简介"><el-input type="textarea" v-model="record.description"/></el-form-item></template>
 <template v-if="kind==='performances'"><p>{{record.production_title}}</p><el-form-item label="制作版本"><el-select v-model="record.edition" :disabled="cast.length>0"><el-option v-for="e in editions" :key="e.id" :label="e.name" :value="e.id"/></el-select></el-form-item><p class="muted">已有演职记录时不能切换制作版本。</p><el-form-item label="演出时间"><el-date-picker v-model="record.starts_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ssZ"/></el-form-item><el-form-item label="地点"><el-input v-model="record.venue"/></el-form-item><el-form-item label="演职备注"><el-input type="textarea" v-model="record.cast_notes"/></el-form-item></template>
 <template v-if="kind==='assets'"><p>{{record.production_title}} / {{record.performance_title}}</p><el-form-item label="资料类型"><el-select v-model="record.category"><el-option v-for="c in ['剧本','照片','录像','音频','票房','其他']" :key="c" :value="c" :label="c"/></el-select></el-form-item><el-form-item label="说明"><el-input type="textarea" v-model="record.description"/></el-form-item><el-alert v-if="record.financial" title="财务资料始终受财务权限保护，修改类型不会解除保护。" :closable="false"/></template>
 <el-button v-if="editable" native-type="submit" type="primary">保存档案</el-button>
 </el-form>
 <template v-if="kind==='productions'">
 <h3>制作版本</h3><p class="muted">例如首演版、复排版、巡演版；每个版本独立维护角色与岗位。</p>
 <div v-for="e in editions" :key="e.id" class="detail-row"><el-input v-model="e.name" :disabled="!editable" aria-label="制作版本名称"/><el-input v-model="e.description" :disabled="!editable" placeholder="版本说明"/><el-button v-if="editable" @click="editEdition(e)">保存版本</el-button></div>
 <el-form v-if="editable" inline @submit.prevent="addEdition"><el-form-item label="新版本"><el-input aria-label="新版本名称" v-model="edition.name"/></el-form-item><el-form-item label="说明"><el-input v-model="edition.description"/></el-form-item><el-button native-type="submit">新增制作版本</el-button></el-form>
 <h3>角色与岗位</h3><div v-for="r in roles" :key="r.id" class="detail-row"><span>{{editions.find(e=>e.id===r.edition)?.name}}</span><el-input v-model="r.name" :disabled="!editable"/><el-select v-model="r.kind" :disabled="!editable"><el-option label="演员角色" value="actor"/><el-option label="工作人员" value="crew"/></el-select><el-button v-if="editable" @click="editRole(r)">保存角色</el-button></div>
 <el-form v-if="editable" label-position="top" @submit.prevent="addRole"><el-form-item label="制作版本"><el-select aria-label="角色所属版本" v-model="stage.edition"><el-option v-for="e in editions" :key="e.id" :label="e.name" :value="e.id"/></el-select></el-form-item><el-form-item label="角色 / 岗位名称"><el-input aria-label="角色名称" v-model="stage.name"/></el-form-item><el-radio-group v-model="stage.kind"><el-radio value="actor">演员角色</el-radio><el-radio value="crew">工作人员</el-radio></el-radio-group><el-button native-type="submit">新增角色</el-button></el-form>
 </template>
 <template v-if="kind==='performances'"><h3>计划阵容与实际阵容</h3><p class="muted">人员先在“演职人员”中建立；角色在所属剧目的制作版本中建立。</p>
 <div v-for="c in cast" :key="c.id" class="cast-row"><el-select v-model="c.phase" :disabled="!editable"><el-option label="计划" value="planned"/><el-option label="实际" value="actual"/></el-select><el-select v-model="c.person" :disabled="!editable" filterable><el-option v-for="p in people" :key="p.id" :label="p.name" :value="p.id"/></el-select><el-select v-model="c.stage_role" :disabled="!editable"><el-option v-for="r in roles" :key="r.id" :label="r.name" :value="r.id"/></el-select><el-input v-model="c.note" :disabled="!editable" placeholder="替补 / 变更说明"/><el-button v-if="editable" @click="editCast(c)">保存阵容</el-button><el-popconfirm v-if="editable" title="删除此条阵容记录？" @confirm="removeCast(c.id)"><template #reference><el-button type="danger" text>删除</el-button></template></el-popconfirm></div>
 <el-empty v-if="!cast.length" description="尚未录入阵容"/>
 <el-form v-if="editable" label-position="top" @submit.prevent="addCast"><el-form-item label="记录类型"><el-radio-group v-model="assignment.phase"><el-radio value="planned">计划阵容</el-radio><el-radio value="actual">实际阵容</el-radio></el-radio-group></el-form-item><el-form-item label="人员"><el-select aria-label="阵容人员" v-model="assignment.person" filterable><el-option v-for="p in people" :key="p.id" :label="p.name+' / '+p.specialty" :value="p.id"/></el-select></el-form-item><el-form-item label="角色 / 岗位"><el-select aria-label="阵容角色" v-model="assignment.stage_role"><el-option v-for="r in roles" :key="r.id" :label="r.name" :value="r.id"/></el-select></el-form-item><el-form-item label="变更说明"><el-input v-model="assignment.note"/></el-form-item><el-button native-type="submit">添加阵容记录</el-button></el-form>
 </template>
 <template v-if="kind==='assets'"><h3>文件历史版本 · 当前 V{{record.version_number}}</h3><p class="muted">原文件始终保留。已有分享固定指向创建时选择的版本。</p>
 <el-table :data="versions"><el-table-column label="版本" width="70"><template #default="{row}">V{{row.number}}</template></el-table-column><el-table-column prop="original_name" label="原始文件名"/><el-table-column prop="note" label="版本说明"/><el-table-column prop="uploaded_by_name" label="上传人"/><el-table-column label="操作" width="160"><template #default="{row}"><a v-if="previewable(row.original_name)" :href="`/api/assets/${id}/preview/?version=${row.id}`" target="_blank" rel="noopener">预览</a> <a v-if="user.can_download" :href="`/api/assets/${id}/content/?version=${row.id}`">下载</a> <el-button v-if="record.can_share" link type="primary" @click="emit('share',{...record,version:row.id,version_number:row.number})">分享</el-button></template></el-table-column><el-table-column type="expand"><template #default="{row}"><p>上传时间：{{new Date(row.created_at).toLocaleString('zh-CN')}}</p><p class="hash">SHA-256：{{row.sha256}}</p></template></el-table-column></el-table>
 <el-form v-if="editable" label-position="top" @submit.prevent="upload"><h3>上传新版本</h3><el-form-item label="版本说明（必填）"><el-input aria-label="版本说明" v-model="note" maxlength="1000" type="textarea"/></el-form-item><el-form-item label="新文件（最大100MB）"><input aria-label="新版本文件" type="file" @change="file=($event.target as HTMLInputElement).files?.[0]??null"/></el-form-item><el-button type="primary" native-type="submit">上传新版本</el-button></el-form>
 </template>
</div>
</template>
<style scoped>
.details h3{margin-top:32px}.detail-row,.cast-row{display:flex;gap:8px;align-items:center;margin:12px 0;flex-wrap:wrap}.detail-row .el-input{flex:1;min-width:130px}.detail-row .el-select{width:140px}.cast-row .el-select{width:135px}.cast-row .el-input{width:160px}.details .el-form{margin-top:18px}.hash{overflow-wrap:anywhere}a{margin-right:8px}
</style>
