<script setup>
import { ArrowLeft, Flame, Heart, Search, SlidersHorizontal } from "lucide-vue-next"

defineProps({
  filteredBases: { type: Array, default: () => [] },
  isFavorite: { type: Function, required: true }
})

const searchText = defineModel("searchText", { type: String, default: "" })
const emit = defineEmits(["go", "openDetail", "toggleFavorite"])

function go(target) { emit("go", target) }
function openDetail(base) { emit("openDetail", base) }
function toggleFavorite(base) { emit("toggleFavorite", base) }
</script>

<template>
          <header class="page-header"><button @click="go('home')"><ArrowLeft/></button><h1>基地列表</h1><button><SlidersHorizontal/></button></header>
          <div class="list-search"><Search :size="18"/><input v-model="searchText" placeholder="搜索基地名称或地区"></div>
          <div class="chip-row"><button class="active">全部</button><button>康养</button><button>徒步</button><button>研学</button><button>生态</button></div>
          <section class="base-list">
            <article v-for="base in filteredBases" :key="base.id" class="base-card" @click="openDetail(base)">
              <img :src="base.image" :alt="base.name">
              <div class="base-card-content"><h3>{{ base.name }}</h3><p class="muted">{{ base.area }}</p><p class="rating"><Flame :size="14"/> 热度 {{ base.viewCount }}</p><div class="tags"><span v-for="tag in base.tags.slice(0, 3)" :key="tag">{{ tag }}</span></div></div>
              <button class="heart" :class="{ active: isFavorite(base.id) }" @click.stop="toggleFavorite(base)"><Heart :size="19" :fill="isFavorite(base.id) ? 'currentColor' : 'none'"/></button>
            </article>
          </section>
        </template>
