<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const items = ref([])
const cloningId = ref(null)
const newLength = ref(null)
const newWidth = ref(null)
const err = ref('')
const load = async () => { items.value = (await getJSON('/api/rooms')).items }
onMounted(load)
const startClone = (r) => { cloningId.value = r.id; newLength.value = r.length; newWidth.value = r.width; err.value = '' }
const doClone = async (r) => {
  err.value = ''
  try {
    await postJSON(`/api/rooms/${r.id}/clone`, { new_length: +newLength.value, new_width: +newWidth.value })
    cloningId.value = null
    await load()
  } catch (e) { err.value = `克隆失败：${e.message}` }
}
</script>
<template><div class="page"><h1>房间</h1>
<p v-if="err" class="err">{{ err }}</p>
<table><template v-for="r in items" :key="r.id">
<tr><td>{{ r.name }}</td><td>{{ r.length }}×{{ r.width }}×{{ r.height }}</td>
<td><router-link :to="`/rooms/${r.id}`">详情</router-link></td>
<td><button @click="startClone(r)">克隆改尺寸</button></td></tr>
<tr v-if="cloningId === r.id"><td colspan="4"><div class="clone-form">
<label>新长 <input type="number" step="0.1" v-model.number="newLength" /></label>
<label>新宽 <input type="number" step="0.1" v-model.number="newWidth" /></label>
<button @click="doClone(r)">确认克隆</button>
<button @click="cloningId = null">取消</button>
</div></td></tr>
</template></table></div></template>
