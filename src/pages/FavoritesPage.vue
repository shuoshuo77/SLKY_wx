<script setup>
import { ArrowLeft, Flame, Heart } from "lucide-vue-next"

defineProps({
  favoriteBases: { type: Array, default: () => [] }
})

const emit = defineEmits(["go", "openDetail", "toggleFavorite"])

function go(target) { emit("go", target) }
function openDetail(base) { emit("openDetail", base) }
function toggleFavorite(base) { emit("toggleFavorite", base) }
</script>

<template>
          <header class="page-header"><button @click="go('profile')"><ArrowLeft/></button><h1>我的收藏</h1><button></button></header>
          <section v-if="favoriteBases.length" class="base-list">
            <article v-for="base in favoriteBases" :key="base.id" class="base-card" @click="openDetail(base)">
              <img :src="base.image" :alt="base.name">
              <div class="base-card-content"><h3>{{ base.name }}</h3><p class="muted">{{ base.area }}</p><p class="rating"><Flame :size="14"/> 热度 {{ base.viewCount }}</p><div class="tags"><span v-for="tag in base.tags.slice(0, 3)" :key="tag">{{ tag }}</span></div></div>
              <button class="heart active" @click.stop="toggleFavorite(base)"><Heart :size="19" fill="currentColor"/></button>
            </article>
          </section>
          <section v-else class="empty-state">
            <div class="empty-icon"><Heart/></div>
            <h3>还没有收藏</h3><p>在基地卡片上点一下小心心，喜欢的基地就会收藏到这里</p>
            <button @click="go('bases')">去逛逛</button>
          </section>
        </template>
