<script setup>
import { ArrowLeft, ChevronRight, MapPinned, SlidersHorizontal } from "lucide-vue-next"

defineProps({
  mapBases: { type: Array, default: () => [] }
})

const mapSelected = defineModel("mapSelected", { type: Object, default: null })
const emit = defineEmits(["go", "openDetail", "openFilter"])

function go(target) { emit("go", target) }
function openDetail(base) { emit("openDetail", base) }
</script>

<template>
          <header class="page-header"><button @click="go('home')"><ArrowLeft/></button><h1>地图找基地</h1><button aria-label="筛选基地" @click="emit('openFilter')"><SlidersHorizontal/></button></header>
          <section class="map-panel">
            <div class="map-grid"></div>
            <button v-for="(base, index) in mapBases.slice(0, 12)" :key="base.id" class="pin" :style="{ left: `${15 + (index % 4) * 24}%`, top: `${22 + Math.floor(index / 4) * 28}%` }" @click="mapSelected = base"><MapPinned/></button>
          </section>
          <article v-if="mapSelected" class="map-result" @click="openDetail(mapSelected)"><img :src="mapSelected.image"><div><h3>{{ mapSelected.name }}</h3><p>{{ mapSelected.area }}</p><p>{{ mapSelected.address }}</p></div><ChevronRight/></article>
          <article v-else class="map-result placeholder"><div><h3>点击地图标记查看基地</h3><p>地图数据来自后端接口</p></div></article>
        </template>
