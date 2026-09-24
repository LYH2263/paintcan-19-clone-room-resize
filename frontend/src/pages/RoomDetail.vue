<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getJSON, postJSON } from '../api'
const route = useRoute()
const detail = ref(null)
const est = ref(null)
const form = ref({ length: '', width: '' })
const error = ref('')
const message = ref('')
const busy = ref(false)
const compare = ref(null)
const load = async () => {
  compare.value = null; error.value = ''; message.value = ''
  detail.value = await getJSON(`/api/rooms/${route.params.id}`)
  est.value = await postJSON('/api/estimate', { room_id: +route.params.id, persist: false })
  form.value = { length: String(detail.value.room.length), width: String(detail.value.room.width) }
}
onMounted(load); watch(() => route.params.id, load)
const doClone = async () => {
  error.value = ''; message.value = ''
  const L = form.value.length === '' ? detail.value.room.length : Number(form.value.length)
  const W = form.value.width === '' ? detail.value.room.width : Number(form.value.width)
  if (!(L > 0) || !(W > 0)) {
    error.value = '新的长和宽必须为正数；整单失败，未创建任何房间或门窗'
    return
  }
  busy.value = true
  try {
    const created = await postJSON(`/api/rooms/${route.params.id}/clone`, { length: L, width: W })
    const srcEst = await postJSON('/api/estimate', { room_id: +route.params.id, persist: false })
    const cloneEst = await postJSON('/api/estimate', { room_id: created.room.id, persist: false })
    compare.value = {
      source: { ...detail.value.room, est: srcEst, savedRun: null },
      clone: { ...created.room, est: cloneEst, openingsCount: created.openings.length, savedRun: null },
    }
    message.value = `克隆成功：新房间 #${created.room.id}，门窗 ${created.openings.length} 个已一并复制；源房保持不变`
  } catch (e) {
    error.value = `克隆失败，房间与门窗已整体回滚：${e.message}`
  } finally {
    busy.value = false
  }
}
const persist = async (side) => {
  const t = compare.value[side]
  const r = await postJSON('/api/estimate', { room_id: t.id, persist: true })
  t.savedRun = r.run_id
}
</script>
<template><div class="page" v-if="detail"><h1>{{ detail.room.name }}</h1>
<p>净面积 {{ est?.net_m2 }} m² · 需漆 <span class="hero-num">{{ est?.liters }} L</span></p>
<ul><li v-for="o in detail.openings" :key="o.id">{{ o.kind }} {{ o.w }}×{{ o.h }}</li></ul>

<section class="clone-box">
  <h2>克隆改尺寸</h2>
  <p class="hint">复制为新档案并复制全部门窗；留空或保持原值则沿用源房尺寸。源房尺寸与门窗不会被修改。</p>
  <label>新长 <input v-model="form.length" type="number" step="0.1" :placeholder="detail.room.length"></label>
  <label>新宽 <input v-model="form.width" type="number" step="0.1" :placeholder="detail.room.width"></label>
  <button :disabled="busy" @click="doClone">{{ busy ? '克隆中…' : '克隆此房间' }}</button>
  <p v-if="error" class="note err">{{ error }}</p>
  <p v-if="message" class="note ok">{{ message }}</p>
</section>

<table v-if="compare" class="compare">
  <tr><th></th><th>源房（不变）</th><th>克隆房（新尺寸）</th></tr>
  <tr><td>房间</td>
    <td>{{ compare.source.name }} #{{ compare.source.id }}</td>
    <td><router-link :to="`/rooms/${compare.clone.id}`">{{ compare.clone.name }} #{{ compare.clone.id }}</router-link></td></tr>
  <tr><td>长×宽×高</td>
    <td>{{ compare.source.length }}×{{ compare.source.width }}×{{ compare.source.height }}</td>
    <td>{{ compare.clone.length }}×{{ compare.clone.width }}×{{ compare.clone.height }}</td></tr>
  <tr><td>墙面毛面积</td>
    <td>{{ compare.source.est.gross_m2 }} m²</td>
    <td>{{ compare.clone.est.gross_m2 }} m²</td></tr>
  <tr><td>扣洞后净面积</td>
    <td>{{ compare.source.est.net_m2 }} m²</td>
    <td>{{ compare.clone.est.net_m2 }} m²</td></tr>
  <tr><td>需漆</td>
    <td><strong>{{ compare.source.est.liters }} L</strong></td>
    <td><strong>{{ compare.clone.est.liters }} L</strong></td></tr>
  <tr><td>升差</td>
    <td colspan="2">{{ (compare.clone.est.liters - compare.source.est.liters).toFixed(2) }} L（克隆 − 源房）</td></tr>
  <tr><td>分别保存估算</td>
    <td><button @click="persist('source')" :disabled="compare.source.savedRun">
      {{ compare.source.savedRun ? `已存 run #${compare.source.savedRun}` : '为源房 persist' }}</button></td>
    <td><button @click="persist('clone')" :disabled="compare.clone.savedRun">
      {{ compare.clone.savedRun ? `已存 run #${compare.clone.savedRun}` : '为克隆房 persist' }}</button></td></tr>
</table>
</div></template>
<style scoped>
.clone-box { border:1px dashed #3a7ca5; padding:0.75rem; margin-top:1rem; }
.clone-box label { margin-right:0.75rem; }
.clone-box input { width:6rem; }
.hint { color:#5a7a8a; font-size:0.9em; }
.note { padding:0.4rem 0.6rem; }
.err { background:#fde2e2; border:1px solid #d96a6a; }
.ok { background:#e2f3e2; border:1px solid #6ab06a; }
.compare { margin-top:1rem; }
</style>
