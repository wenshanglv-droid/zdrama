<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { api, all } from './api'
import ArchiveDetails from './ArchiveDetails.vue'
import DirectoryPanel from './DirectoryPanel.vue'
const detail=ref<any>(null),editions=ref<any[]>([])
const labels:Record<string,string>={assets:'资料库',productions:'剧目档案',performances:'演出场次',shares:'对外分享',people:'演职人员',accounts:'账号权限'}
const catalogEditor=computed(()=>['admin','archivist','business'].includes(user.value?.role))
const user=ref<any>(null), ready=ref(false), busy=ref(false), tab=ref('assets')
const productions=ref<any[]>([]), performances=ref<any[]>([]), assets=ref<any[]>([]), shares=ref<any[]>([])
const credentials=ref({username:'',password:''}), q=ref(''), category=ref('')
const categories=['剧本','照片','录像','音频','票房','其他']
const dialog=ref(''), link=ref(''), shared=ref<any>(null)
const production=ref({title:'',genre:'',description:''})
const performance=ref({edition:undefined as number|undefined,production:undefined as number|undefined,title:'',starts_at:'',venue:'',cast_notes:''})
const asset=ref({title:'',performance:undefined as number|undefined,category:'剧本'})
const file=ref<File|null>(null)
const share=ref({version:undefined as number|undefined,asset:0,recipient_username:'',expires_at:'',allow_download:false})
const token=location.pathname.startsWith('/share/')?location.pathname.split('/')[2]:''
async function run(fn:()=>Promise<void>) {busy.value=true;try{await fn()}catch(e){ElMessage.error((e as Error).message)}finally{busy.value=false}}
async function load(){
 if(token){shared.value=await api('shared/'+token+'/');return}
 if(user.value?.internal){[productions.value,performances.value,assets.value,shares.value,editions.value]=await Promise.all([all('productions/'),all('performances/'),all('assets/?q='+encodeURIComponent(q.value)+'&category='+encodeURIComponent(category.value)),all('shares/'),all('editions/')])}
}
async function initialize(){user.value=(await api('session/')).user;if(user.value)await load()}
onMounted(()=>run(async()=>{try{await initialize()}finally{ready.value=true}}))
function login(){run(async()=>{await api('session/');await api('login/',credentials.value);credentials.value.password='';await initialize()})}
function logout(){run(async()=>{await api('logout/',{});user.value=null;shared.value=null;assets.value=[];tab.value='assets';detail.value=null;dialog.value='';await api('session/')})}
function newRecord(){
 const kind=tab.value==='assets'?'asset':tab.value==='productions'?'production':'performance'
 production.value={title:'',genre:'',description:''}
 performance.value={edition:undefined,production:undefined,title:'',starts_at:'',venue:'',cast_notes:''}
 asset.value={title:'',performance:undefined,category:user.value.role==='finance'?'票房':'剧本'};file.value=null;dialog.value=kind
}
function openShare(row:any){share.value={version:row.version,asset:row.id,recipient_username:'',expires_at:new Date(Date.now()+7*86400000).toISOString(),allow_download:false};link.value='';dialog.value='share'}
function save(){run(async()=>{
 if(dialog.value==='production') await api('productions/',production.value)
 else if(dialog.value==='performance') await api('performances/',performance.value)
 else if(dialog.value==='asset'){
  if(!file.value)throw new Error('请选择文件')
  const f=new FormData();Object.entries(asset.value).forEach(([k,v])=>f.append(k,String(v??'')));f.append('file',file.value);await api('assets/',f,true)
 }else if(dialog.value==='share'){const r=await api('shares/',share.value);link.value=location.origin+r.url;await load();return}
 dialog.value='';await load();ElMessage.success('已保存')
})}
function revoke(row:any){run(async()=>{await api('shares/'+row.id+'/revoke/',{});await load();ElMessage.success('分享已撤销')})}
function selectFile(event:Event){file.value=(event.target as HTMLInputElement).files?.[0]??null;if(file.value&&!asset.value.title)asset.value.title=file.value.name}
function size(n:number){return n>=1048576?(n/1048576).toFixed(1)+' MB':(n/1024).toFixed(1)+' KB'}
function date(v:string){return new Date(v).toLocaleString('zh-CN')}
function shareStatus(row:any){return row.revoked_at?'已撤销':new Date(row.expires_at)<new Date()?'已过期':row.effective_active===false?'权限失效':'有效'}
</script>
<template>
<div v-if="!ready" class="loading">正在连接档案服务…</div>
<div v-else-if="!user" class="login-page">
 <div class="login-intro"><div class="brand">剧藏 <small>ZDRAMA</small></div><span class="eyebrow">院团数字档案</span><h1>让每一次演出，<br>留下完整的记忆。</h1><p>剧目、场次、剧本与影像，在这里有序相连。</p></div>
 <el-card class="login-card"><h2>{{token?'验证接收人身份':'登录档案工作台'}}</h2><p class="muted">{{token?'请使用分享指定的接收账号登录。':'使用管理员为你创建的院团账号。'}}</p><el-form @submit.prevent="login" label-position="top"><el-form-item label="账号"><el-input aria-label="账号" v-model="credentials.username" autocomplete="username" /></el-form-item><el-form-item label="密码"><el-input aria-label="密码" v-model="credentials.password" type="password" show-password autocomplete="current-password" /></el-form-item><el-button native-type="submit" type="primary" :loading="busy" style="width:100%">登录</el-button></el-form></el-card>
</div>
<div v-else-if="token" class="shared-page"><header><div class="brand">剧藏 <small>资料分享</small></div><el-button @click="logout">退出 {{user.username}}</el-button></header><el-card v-if="shared"><el-tag>已验证接收账号</el-tag><h1>{{shared.title}}</h1><p>{{shared.original_name}}</p><p class="muted">有效期至 {{date(shared.expires_at)}}</p><a class="action-link" :href="'/api/shared/'+token+'/content/'" target="_blank" rel="noopener">打开预览</a><a v-if="shared.allow_download" class="action-link" :href="'/api/shared/'+token+'/content/?download=1'">下载文件</a><p class="muted">请按授权范围使用资料。预览内容仍可能被接收人保存或截图。</p></el-card><el-empty v-else description="分享不可用、已失效，或当前账号不是指定接收人" /></div>
<div v-else-if="!user.internal" class="shared-page"><h1>接收账号已登录</h1><p>请打开发送给你的分享链接访问资料。</p><el-button @click="logout">退出登录</el-button></div>
<div v-else class="shell">
 <aside><div class="brand">剧藏 <small>ZDRAMA</small></div><div class="workspace-label">院团数字档案</div><nav><button v-for="item in Object.entries(labels).filter(([id])=>id!=='accounts'||user.role==='admin').map(([id,label])=>({id,label}))" :key="item.id" :class="{active:tab===item.id}" @click="tab=item.id">{{item.label}}</button></nav><div class="aside-bottom">开发试用版 · 0.2<br>每份资料，都有来处。</div></aside>
 <main><header><span>工作空间 / {{ labels[tab] }}</span><el-button text @click="logout">{{user.username}} · 退出</el-button></header>
 <section class="page-title"><div><span class="eyebrow">演出记忆 · 有序留存</span><h1>{{ labels[tab] }}</h1><p class="muted">{{tab==='assets'?'按剧目和场次整理资料，快速找到需要的版本。':tab==='shares'?'查看授权范围与有效期，随时撤销分享。':'建立业务档案，让资料关联到真实演出。'}}</p></div><el-button v-if="(tab==='assets'&&user.can_download)||(catalogEditor&&['productions','performances'].includes(tab))" type="primary" size="large" @click="newRecord">＋ {{tab==='assets'?'上传资料':tab==='productions'?'新建剧目':'新建场次'}}</el-button></section>
 <div class="stats"><div><span>剧目档案</span><strong>{{productions.length}}</strong></div><div><span>演出场次</span><strong>{{performances.length}}</strong></div><div><span>可访问资料</span><strong>{{assets.length}}</strong></div><div><span>有效分享</span><strong>{{shares.filter(s=>shareStatus(s)==='有效').length}}</strong></div></div>
 <el-card shadow="never" v-loading="busy">
 <template v-if="tab==='assets'"><div class="filters"><el-input v-model="q" placeholder="搜索资料名、剧目或场次" clearable @keyup.enter="run(load)"/><el-select v-model="category" placeholder="全部资料类型" clearable><el-option v-for="c in categories" :key="c" :label="c" :value="c"/></el-select><el-button @click="run(load)">检索</el-button></div><el-table :data="assets" empty-text="还没有资料，请先创建剧目和场次，再上传资料。"><el-table-column prop="title" label="资料名称" min-width="220"/><el-table-column prop="category" label="类型" width="80"/><el-table-column prop="production_title" label="所属剧目" min-width="130"/><el-table-column prop="performance_title" label="演出场次" min-width="130"/><el-table-column label="大小" width="100"><template #default="{row}">{{size(row.size)}}</template></el-table-column><el-table-column label="操作" width="240"><template #default="{row}"><el-button link type="primary" @click="detail={kind:'assets',id:row.id}">详情</el-button><a v-if="/\.(pdf|jpe?g|png)$/i.test(row.original_name)" :href="'/api/assets/'+row.id+'/preview/'" target="_blank" rel="noopener">预览</a><a v-if="user.can_download" :href="'/api/assets/'+row.id+'/content/'">下载</a><el-button v-if="row.can_share" link type="primary" @click="openShare(row)">分享</el-button></template></el-table-column></el-table></template>
 <el-table v-if="tab==='productions'" :data="productions" empty-text="建立第一个剧目档案"><el-table-column prop="title" label="剧目名称"/><el-table-column prop="genre" label="剧种 / 类型"/><el-table-column prop="description" label="简介"/><el-table-column label="操作"><template #default="{row}"><el-button link type="primary" @click="detail={kind:'productions',id:row.id}">详情</el-button></template></el-table-column></el-table>
 <el-table v-if="tab==='performances'" :data="performances" empty-text="请先建立剧目，再添加演出场次"><el-table-column prop="title" label="场次名称"/><el-table-column prop="production_title" label="剧目"/><el-table-column prop="edition_name" label="制作版本"/><el-table-column prop="venue" label="演出地点"/><el-table-column label="演出时间"><template #default="{row}">{{date(row.starts_at)}}</template></el-table-column><el-table-column label="操作"><template #default="{row}"><el-button link type="primary" @click="detail={kind:'performances',id:row.id}">详情</el-button></template></el-table-column></el-table>
 <el-table v-if="tab==='shares'" :data="shares" empty-text="从资料库选择资料，创建接收账号专属分享"><el-table-column prop="asset_title" label="资料"/><el-table-column label="固定版本"><template #default="{row}">V{{row.version_number}}</template></el-table-column><el-table-column prop="recipient_name" label="接收账号"/><el-table-column label="有效期"><template #default="{row}">{{date(row.expires_at)}}</template></el-table-column><el-table-column label="权限"><template #default="{row}">{{row.allow_download?'允许下载':'仅预览'}}</template></el-table-column><el-table-column label="状态"><template #default="{row}"><el-tag :type="shareStatus(row)==='有效'?'success':'info'">{{shareStatus(row)}}</el-tag></template></el-table-column><el-table-column label="操作"><template #default="{row}"><el-popconfirm title="撤销后接收人将无法继续访问，确定吗？" @confirm="revoke(row)"><template #reference><el-button v-if="!row.revoked_at" link type="danger">撤销</el-button></template></el-popconfirm></template></el-table-column></el-table>
 <DirectoryPanel v-if="['people','accounts'].includes(tab)" :accounts="tab==='accounts'" :user="user" :productions="productions"/></el-card><p class="footnote">当前版本：资料上传上限100MB；原件保留；PDF、JPG、PNG支持分享预览。</p>
 </main>
</div>
<el-dialog :model-value="!!dialog" @close="dialog=''" :title="{production:'新建剧目',performance:'新建场次',asset:'上传资料',share:'创建受控分享'}[dialog]" width="min(560px,94vw)">
 <el-form label-position="top" @submit.prevent="save">
 <template v-if="dialog==='production'"><el-form-item label="剧目名称"><el-input v-model="production.title"/></el-form-item><el-form-item label="剧种 / 类型"><el-input v-model="production.genre"/></el-form-item><el-form-item label="简介"><el-input v-model="production.description" type="textarea"/></el-form-item></template>
 <template v-if="dialog==='performance'"><el-form-item label="所属剧目"><el-select v-model="performance.production" @change="performance.edition=undefined"><el-option v-for="p in productions" :key="p.id" :value="p.id" :label="p.title"/></el-select></el-form-item><el-form-item label="制作版本"><el-select aria-label="场次制作版本" v-model="performance.edition" placeholder="留空使用默认版"><el-option v-for="e in editions.filter(e=>e.production===performance.production)" :key="e.id" :value="e.id" :label="e.name"/></el-select></el-form-item><el-form-item label="场次名称"><el-input aria-label="场次名称" v-model="performance.title"/></el-form-item><el-form-item label="演出时间"><el-date-picker aria-label="演出时间" v-model="performance.starts_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ssZ"/></el-form-item><el-form-item label="地点"><el-input aria-label="地点" v-model="performance.venue"/></el-form-item><el-form-item label="演职人员备注"><el-input v-model="performance.cast_notes" type="textarea"/></el-form-item></template>
 <template v-if="dialog==='asset'"><el-form-item label="资料名称"><el-input v-model="asset.title"/></el-form-item><el-form-item label="所属场次"><el-select v-model="asset.performance"><el-option v-for="p in performances" :key="p.id" :value="p.id" :label="p.production_title+' / '+p.title"/></el-select></el-form-item><el-form-item label="资料类型"><el-select v-model="asset.category"><el-option v-for="c in categories" :key="c" :value="c" :label="c"/></el-select></el-form-item><el-form-item label="文件（最大100MB）"><input type="file" @change="selectFile"/></el-form-item></template>
 <template v-if="dialog==='share'"><p class="muted">{{share.version?'分享指定历史版本':'分享当前文件版本'}}；后续上传新版本不会改变此链接。</p><el-alert title="接收人必须使用指定账号登录；当前不发送邮件或短信。" :closable="false"/><el-form-item label="接收账号"><el-input aria-label="接收账号" v-model="share.recipient_username"/></el-form-item><el-form-item label="有效期（最长30天）"><el-date-picker v-model="share.expires_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ssZ"/></el-form-item><el-checkbox v-model="share.allow_download">允许下载原件</el-checkbox><p class="muted">仅预览支持PDF、JPG、PNG；预览不能阻止截图或另行保存。</p><el-input v-if="link" :model-value="link" readonly/><p v-if="link">分享链接已生成，请复制保存。链接只在创建时返回。</p></template>
 <div class="dialog-actions"><el-button @click="dialog=''">关闭</el-button><el-button v-if="!link||dialog!=='share'" type="primary" native-type="submit" :loading="busy">{{dialog==='share'?'生成分享链接':'保存'}}</el-button></div>
 </el-form>
</el-dialog>
<el-drawer :model-value="!!detail" @close="detail=null" title="档案详情" size="min(900px,96vw)"><ArchiveDetails v-if="detail" :key="detail.kind+detail.id" :kind="detail.kind" :id="detail.id" :user="user" @updated="run(load)" @share="openShare"/></el-drawer>
</template>
