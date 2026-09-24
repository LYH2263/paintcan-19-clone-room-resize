<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getJSON, postJSON } from '../api'
const route = useRoute()
const detail = ref(null)
const est = ref(null)
const newLength = ref(null)
const newWidth = ref(null)
const cloneErr = ref('')
const clone = ref(null)
const cloneEst = ref(null)
const savedRuns = ref(null)
const load = async () => {
  detail.value = await getJSON(`/api/rooms/${route.params.id}`)
  est.value = await postJSON('/api/estimate', { room_id: +route.params.id, persist: false })
  newLength.value = detail.value.room.length
  newWidth.value = detail.value.room.width
  clone.value = null; cloneEst.value = null; savedRuns.value = null; cloneErr.value = ''
}
onMounted(load); watch(() => route.params.id, load)
const doClone = async () => {
  cloneErr.value = ''
  try {
    clone.value = await postJSON(`/api/rooms/${route.params.id}/clone`, { new_length: +newLength.value, new_width: +newWidth.value })
    cloneEst.value = await postJSON('/api/estimate', { room_id: clone.value.room.id, persist: false })
    savedRuns.value = null
  } catch (e) { cloneErr.value = `克隆失败：${e.message}` }
}
const persistBoth = async () => {
  const a = await postJSON('/api/estimate', { room_id: detail.value.room.id, persist: true })
  const b = await postJSON('/api/estimate', { room_id: clone.value.room.id, persist: true })
  savedRuns.value = [a.run_id, b.run_id]
}
</script>
<template><div class="page" v-if="detail"><h1>{{ detail.room.name }}</h1>
<p>净面积 {{ est?.net_m2 }} m² · 需漆 <span class="hero-num">{{ est?.liters }} L</span></p>
<ul><li v-for="o in detail.openings" :key="o.id">{{ o.kind }} {{ o.w }}×{{ o.h }}</li></ul>
<h2>克隆改尺寸</h2>
<div class="clone-form">
<label>新长 <input type="number" step="0.1" v-model.number="newLength" /></label>
<label>新宽 <input type="number" step="0.1" v-model.number="newWidth" /></label>
<button @click="doClone">克隆</button>
</div>
<p v-if="cloneErr" class="err">{{ cloneErr }}</p>
<div v-if="clone && cloneEst">
<h3>升数对照</h3>
<table>
<tr><th>档案</th><th>尺寸(长×宽×高)</th><th>净面积 m²</th><th>需漆 L</th><th></th></tr>
<tr><td>源房 {{ detail.room.name }}</td><td>{{ detail.room.length }}×{{ detail.room.width }}×{{ detail.room.height }}</td><td>{{ est?.net_m2 }}</td><td>{{ est?.liters }}</td><td></td></tr>
<tr><td>克隆 {{ clone.room.name }}</td><td>{{ clone.room.length }}×{{ clone.room.width }}×{{ clone.room.height }}</td><td>{{ cloneEst.net_m2 }}</td><td>{{ cloneEst.liters }}</td><td><router-link :to="`/rooms/${clone.room.id}`">详情</router-link></td></tr>
</table>
<button @click="persistBoth">分别保存估算记录</button>
<p v-if="savedRuns">已保存：源房 run #{{ savedRuns[0] }} · 克隆房 run #{{ savedRuns[1] }}（各写各的 calc_runs）</p>
</div>
</div></template>
