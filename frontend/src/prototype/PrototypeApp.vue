<script setup lang="ts">
import {ref,computed,onMounted,onUnmounted} from 'vue'
import {ElMessage,ElMessageBox} from 'element-plus'
import {pages,groups} from './catalog'
import {state,reset,downloadDemo} from './store'
import PageView from './PageView.vue'
import SpecialViews from './SpecialViews.vue'
import './prototype.css'
const current=ref(location.hash.slice(1)||'dashboard'),navQuery=ref(''),mobile=ref(false),persona=ref('档案管理员'),scenario=ref('正常'),guide=ref(false)
const page=computed(()=>pages.find(p=>p.id===current.value)||pages[0])
const completed=computed(()=>Object.values(state.reviews).filter(v=>v==='界面已确认').length)
const external=computed(()=>page.value.id.startsWith('external-'))
function navigate(id:string){location.hash=id;current.value=id;mobile.value=false;scenario.value='正常';window.scrollTo(0,0)}
function hash(){current.value=location.hash.slice(1)||'dashboard';scenario.value='正常'}
onMounted(()=>{window.addEventListener('hashchange',hash);document.title='剧藏 · 全阶段界面评审'})
onUnmounted(()=>window.removeEventListener('hashchange',hash))
async function clear(){try{await ElMessageBox.confirm('仅清除本浏览器中的演示修改、草稿和评审记录。现有业务档案不受影响。','重置演示');reset();ElMessage.success('演示数据已重置')}catch{}}
function exportReview(){downloadDemo('剧藏-界面评审记录.json',{说明:'仅为界面评审，不代表功能验收',时间:new Date().toISOString(),页面:pages.map(p=>({页面:p.title,需求:p.req,阶段:p.phase,状态:state.reviews[p.id]||'待评审',意见:state.notes[p.id]||''}))})}
</script>
<template>
<div class="proto" :class="{external}">
 <div class="review-ribbon"><span><b>界面评审版</b> · 全部为虚构演示数据，操作仅保存在当前浏览器</span><a href="/">返回已实现系统 ↗</a></div>
 <button v-if="mobile" class="nav-scrim" aria-label="关闭导航" @click="mobile=false"></button>
 <aside v-if="!external" class="proto-nav" :class="{mobile}"><a href="#dashboard" class="proto-logo" @click.prevent="navigate('dashboard')"><span class="logo-mark">藏</span><span>剧藏<small>ZDRAMA ARCHIVE</small></span></a><div class="nav-search"><el-input v-model="navQuery" placeholder="查找功能页面" clearable aria-label="查找功能页面"/></div><div class="nav-scroll"><div v-for="g in groups" :key="g" class="nav-group"><p v-if="pages.some(p=>p.group===g&&p.title.includes(navQuery))">{{g}}</p><button v-for="p in pages.filter(p=>p.group===g&&p.title.includes(navQuery))" :key="p.id" :class="{selected:current===p.id}" @click="navigate(p.id)"><span>{{p.title}}</span><small v-if="p.phase.includes('P2')">P2</small><small v-else-if="p.phase.includes('P1')">P1</small></button></div></div><div class="nav-review"><button @click="navigate('review')">界面确认 <b>{{completed}} / {{pages.length}}</b></button><el-progress :percentage="Math.round(completed/pages.length*100)" :show-text="false" :stroke-width="3" color="#c1a77a"/></div></aside>
 <div class="proto-main" :class="{'external-main':external}">
  <header class="proto-top"><div><el-button v-if="!external" class="mobile-toggle" text @click="mobile=!mobile" aria-label="打开导航">☰</el-button><span v-if="external" @click="navigate('dashboard')" class="clickable">剧藏 / 外部视角</span><span v-else>{{page.group}} <span class="separator">/</span> {{page.title}}</span></div><div class="top-actions"><el-select v-model="persona" aria-label="演示岗位" style="width:140px"><el-option v-for="r in ['档案管理员','项目负责人','宣传人员','财务人员','普通查看','系统管理员']" :key="r" :value="r" :label="r"/></el-select><el-button text @click="guide=true">体验说明</el-button><span class="avatar">林</span></div></header>
  <div class="proto-content">
   <div class="proto-heading"><div><div class="kicker">院团数字档案 <span>{{page.phase}}</span></div><h1>{{page.title}}</h1><p>{{page.description}}</p></div><div class="state-picker"><span>查看界面状态</span><el-select v-model="scenario" aria-label="查看界面状态" style="width:132px"><el-option v-for="s in ['正常','空数据','加载中','无权限','网络失败','存储不足','格式不支持','版本冲突','授权到期']" :key="s" :value="s" :label="s"/></el-select></div></div>
   <div v-if="scenario!=='正常'" class="surface state-panel">
    <template v-if="scenario==='加载中'"><el-skeleton :rows="7" animated/><p>正在读取演示档案…</p><el-button @click="scenario='正常'">结束加载演示</el-button></template>
    <template v-else><span class="state-symbol">{{scenario==='空数据'?'＋':'!'}}</span><h2>{{scenario==='空数据'?'这里还没有记录':scenario}}</h2><p>{{scenario==='无权限'?'当前岗位无权进行此操作，请联系业务负责人申请访问。':scenario==='版本冲突'?'这条资料已被他人修改。重新加载后对比差异，保留需要的内容。':scenario==='授权到期'?'授权已到期或被撤销，请联系发送人。':scenario==='存储不足'?'当前空间不足，已暂停新的普通上传，原有资料仍可查看。':scenario==='格式不支持'?'此文件尚不能生成预览，可在授权范围内下载原件或补充预览副本。':scenario==='空数据'?'从创建第一条记录开始，或清空筛选查看其他记录。':'暂时无法连接服务，已保留当前填写内容，请稍后重试。'}}</p><el-button type="primary" @click="scenario='正常'">{{scenario==='空数据'?'查看示例数据':scenario==='版本冲突'?'重新加载并对比':'返回正常界面'}}</el-button></template>
   </div>
   <SpecialViews v-else-if="['dashboard','review','external-share','external-submit','proofread','transcripts','assistant','similar'].includes(page.special||'')" :key="page.id" :page="page" :persona="persona" @navigate="navigate" @export="exportReview"/>
   <PageView v-else :key="page.id" :page="page" :persona="persona" @navigate="navigate"/>
   <footer class="proto-foot"><span>需求对应 {{page.req}}</span><button @click="navigate('review')">记录本页意见 →</button></footer>
  </div>
 </div>
 <el-dialog v-model="guide" title="这版如何体验" width="min(560px,94vw)"><p>本版先确认页面结构、字段、操作顺序和异常提示，覆盖需求书V2.0的P0、P1、P2。</p><ol><li>从工作概览的待办进入场次、资料、归档和分享。</li><li>点击列表详情、新建、编辑及各标签页，体验完整表单。</li><li>右上角切换岗位和状态，检查财务隐藏、空白页及异常提示。岗位切换仅为展示，不是实际权限校验。</li><li>在“界面评审清单”记录意见；可导出到本地后交给开发。</li></ol><el-alert title="本版不上传真实文件、不生成真实外链、不连接票务或AI服务；当前系统的已实现功能仍从首页访问。" :closable="false"/><div class="dialog-actions"><el-button @click="clear">重置演示</el-button><el-button @click="exportReview">导出评审记录</el-button><el-button type="primary" @click="guide=false">开始体验</el-button></div></el-dialog>
</div>
</template>
