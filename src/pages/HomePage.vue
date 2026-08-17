<script setup>
import { Bell, Bot, ChevronRight, Flame, Heart, Leaf, MapPinned, Search, Settings, Sparkles, Trees } from "lucide-vue-next"

defineProps({
  loading: Boolean,
  loadError: String,
  heroImage: String,
  hotBases: { type: Array, default: () => [] },
  bases: { type: Array, default: () => [] },
  isFavorite: { type: Function, required: true }
})

const searchText = defineModel("searchText", { type: String, default: "" })
const emit = defineEmits(["loadAll", "go", "openDetail", "toggleFavorite"])

function loadAll() { emit("loadAll") }
function go(target) { emit("go", target) }
function openDetail(base) { emit("openDetail", base) }
function toggleFavorite(base) { emit("toggleFavorite", base) }
</script>

<template>
          <header class="brand-bar">
            <div class="brand"><Trees :size="25"/><strong>森氧康养</strong></div>
            <div class="header-actions"><Bell :size="19"/><Settings :size="19"/></div>
          </header>

          <section v-if="loading" class="empty-state">
            <div class="empty-icon"><Leaf/></div>
            <h3>正在加载基地数据...</h3><p>从云端拉取最新康养基地</p>
          </section>
          <section v-else-if="loadError" class="empty-state">
            <div class="empty-icon"><MapPinned/></div>
            <h3>数据加载失败</h3><p>{{ loadError }}</p>
            <button @click="loadAll">重试</button>
          </section>

          <template v-else>
          <section class="hero" :style="{ backgroundImage: `url(${heroImage})` }">
            <div class="hero-copy"><h1>呼吸自然<br>享受健康生活</h1><p>探索优质康养基地</p></div>
            <div class="search-box">
              <Search :size="18"/><input v-model="searchText" placeholder="搜索基地名称、位置、特色..." @keyup.enter="go('bases')"><button @click="go('bases')">搜索</button>
            </div>
          </section>

          <section class="service-grid">
            <button @click="go('bases')"><span><Search/></span><b>基地查询</b></button>
            <button @click="go('assistant')"><span><Bot/></span><b>智能推荐</b></button>
            <button @click="go('monitor')"><span><Leaf/></span><b>环境监测</b></button>
            <button @click="openDetail(hotBases[0] || bases[0])"><span><Sparkles/></span><b>健康指南</b></button>
          </section>

          <section class="section-block">
            <div class="section-heading"><h2>热门基地</h2><button @click="go('bases')">更多 <ChevronRight :size="15"/></button></div>
            <article v-for="base in hotBases.slice(0, 3)" :key="base.id" class="base-row" @click="openDetail(base)">
              <img :src="base.image" :alt="base.name">
              <div><h3>{{ base.name }}</h3><div class="tags"><span v-for="tag in base.tags.slice(0, 3)" :key="tag">{{ tag }}</span></div><p><Flame :size="14"/> 热度 {{ base.viewCount }}</p></div>
              <button class="heart" :class="{ active: isFavorite(base.id) }" @click.stop="toggleFavorite(base)"><Heart :size="20" :fill="isFavorite(base.id) ? 'currentColor' : 'none'"/></button>
            </article>
          </section>
          </template>
        </template>
