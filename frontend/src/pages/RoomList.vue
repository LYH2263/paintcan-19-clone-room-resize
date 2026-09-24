<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const items = ref([])
const error = ref('')
const drafts = ref({})
const busy = ref({})
const load = async () => { items.value = (await getJSON('/api/rooms')).items }
onMounted(load)
const draftFor = (r) => {
  if (!(r.id in drafts.value)) drafts.value[r.id] = { length: String(r.length), width: String(r.width) }
  return drafts.value[r.id]
}
const clone = async (r) => {
  error.value = ''
  const d = draftFor(r)
  const body = {}
  if (d.length !== '') body.length = Number(d.length)
  if (d.width !== '') body.width = Number(d.width)
  if ((d.length !== '' && !(body.length > 0)) || (d.width !== '' && !(body.width > 0))) {
    error.value = `「${r.name}」克隆失败：新的长和宽必须为正数`
    return
  }
  busy.value[r.id] = true
  try {
    const created = await postJSON(`/api/rooms/${r.id}/clone`, body)
    await load()
    error.value = `已克隆「${r.name}」→「${created.room.name}」(房间 #${created.room.id})，可到详情页对照升数`
  } catch (e) {
    error.value = `「${r.name}」克隆失败：${e.message}`
  } finally {
    busy.value[r.id] = false
  }
}
</script>
<template><div class="page"><h1>房间</h1>
<p v-if="error" class="note">{{ error }}</p>
<table><tr><th>名称</th><th>长×宽×高</th><th>克隆改尺寸（留空沿用源房）</th><th></th></tr>
<tr v-for="r in items" :key="r.id">
  <td>{{ r.name }} <span class="rid">#{{ r.id }}</span></td>
  <td>{{ r.length }}×{{ r.width }}×{{ r.height }}</td>
  <td>
    <label class="clone-field">长 <input v-model="draftFor(r).length" type="number" step="0.1" :placeholder="r.length"></label>
    <label class="clone-field">宽 <input v-model="draftFor(r).width" type="number" step="0.1" :placeholder="r.width"></label>
  </td>
  <td>
    <router-link :to="`/rooms/${r.id}`">详情</router-link>
    <button :disabled="busy[r.id]" @click="clone(r)">克隆</button>
  </td>
</tr></table></div></template>
<style scoped>
.rid { color:#7a9aae; font-size:0.85em; }
.clone-field { white-space:nowrap; margin-right:0.5rem; }
.clone-field input { width:5rem; }
.note { background:#fff3cd; border:1px solid #d9b44a; padding:0.4rem 0.6rem; }
</style>
