<script setup>
import { ArrowLeft, Flame, Heart, Search, SlidersHorizontal, X } from "lucide-vue-next"
import { ref } from "vue"

defineProps({
  filteredBases: { type: Array, default: () => [] },
  provinces: { type: Array, default: () => [] },
  selectedProvince: { type: String, default: "" },
  loading: Boolean,
  isFavorite: { type: Function, required: true }
})

const searchText = defineModel("searchText", { type: String, default: "" })
const emit = defineEmits(["go", "applyFilter", "openDetail", "toggleFavorite"])
const filtersOpen = ref(false)

function go(target) { emit("go", target) }
function applyFilter(province = "") {
  emit("applyFilter", { keyword: searchText.value, province })
}
function chooseProvince(province = "") {
  applyFilter(province)
  filtersOpen.value = false
}
function resetFilters() {
  searchText.value = ""
  chooseProvince("")
}
function openDetail(base) { emit("openDetail", base) }
function toggleFavorite(base) { emit("toggleFavorite", base) }
</script>

<template>
          <header class="page-header"><button @click="go('home')"><ArrowLeft/></button><h1>基地列表</h1><button :class="{ 'filter-active': filtersOpen }" aria-label="打开筛选" :aria-expanded="filtersOpen" @click="filtersOpen = true"><SlidersHorizontal/></button></header>
          <div class="list-search"><Search :size="18"/><input v-model="searchText" placeholder="搜索基地名称或地区" @keyup.enter="applyFilter()"></div>
          <div class="chip-row">
            <button :class="{ active: !selectedProvince }" @click="applyFilter('')">全部</button>
            <button
              v-for="item in provinces"
              :key="item.province"
              :class="{ active: selectedProvince === item.province }"
              @click="applyFilter(item.province)"
            >{{ item.province }}<small>{{ item.count }}</small></button>
          </div>
          <section class="base-list">
            <p v-if="loading" class="filter-loading">正在筛选基地...</p>
            <article v-for="base in filteredBases" :key="base.id" class="base-card" @click="openDetail(base)">
              <img :src="base.image" :alt="base.name">
              <div class="base-card-content"><h3>{{ base.name }}</h3><p class="muted">{{ base.area }}</p><p class="rating"><Flame :size="14"/> 热度 {{ base.viewCount }}</p><div class="tags"><span v-for="tag in base.tags.slice(0, 3)" :key="tag">{{ tag }}</span></div></div>
              <button class="heart" :class="{ active: isFavorite(base.id) }" @click.stop="toggleFavorite(base)"><Heart :size="19" :fill="isFavorite(base.id) ? 'currentColor' : 'none'"/></button>
            </article>
            <p v-if="!loading && !filteredBases.length" class="filter-empty">没有找到符合条件的基地</p>
          </section>
          <div v-if="filtersOpen" class="base-filter-mask" @click.self="filtersOpen = false">
            <section class="base-filter-sheet" aria-label="基地筛选">
              <header><h2>筛选基地</h2><button aria-label="关闭筛选" @click="filtersOpen = false"><X/></button></header>
              <p class="filter-label">所在省份</p>
              <div class="filter-province-grid">
                <button :class="{ active: !selectedProvince }" @click="chooseProvince('')">全部</button>
                <button
                  v-for="item in provinces"
                  :key="item.province"
                  :class="{ active: selectedProvince === item.province }"
                  @click="chooseProvince(item.province)"
                >{{ item.province }}<small>{{ item.count }}</small></button>
              </div>
              <div class="filter-sheet-actions"><button class="filter-reset" @click="resetFilters">重置</button><button class="filter-done" @click="filtersOpen = false">完成</button></div>
            </section>
          </div>
        </template>
