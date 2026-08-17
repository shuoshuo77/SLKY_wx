<script setup>
import { ArrowLeft, Flame, Heart, LocateFixed } from "lucide-vue-next"

defineProps({
  selected: { type: Object, required: true },
  isFavorite: { type: Function, required: true },
  activeBooking: { type: Function, required: true }
})

const emit = defineEmits(["go", "toggleFavorite", "openBookingSheet"])

function go(target) { emit("go", target) }
function toggleFavorite(base) { emit("toggleFavorite", base) }
function openBookingSheet() { emit("openBookingSheet") }
</script>

<template>
          <header class="page-header overlay"><button @click="go('bases')"><ArrowLeft/></button><h1>基地详情</h1><button class="heart" :class="{ active: isFavorite(selected.id) }" @click.stop="toggleFavorite(selected)"><Heart :fill="isFavorite(selected.id) ? 'currentColor' : 'none'"/></button></header>
          <img class="detail-cover" :src="selected.image" :alt="selected.name">
          <section class="detail-body">
            <h1>{{ selected.name }}</h1><p class="muted">{{ selected.area }}</p>
            <div class="tags"><span v-for="tag in selected.tags" :key="tag">{{ tag }}</span></div>
            <p class="detail-rating"><Flame :size="17"/> <b>{{ selected.viewCount }}</b> 次浏览<em>{{ selected.address }}</em></p>
            <div class="metric-grid">
              <div v-for="metric in selected.metrics" :key="metric.label">
                <component :is="metric.icon" :size="20"/>
                <small>{{ metric.label }}</small>
                <b>{{ metric.value }}</b>
                <span>{{ metric.unit }}</span>
              </div>
            </div>
            <h2>基地介绍</h2><p class="description">{{ selected.desc }}</p>
            <h2>康养服务</h2><div class="services"><span v-for="service in selected.services" :key="service">{{ service }}</span></div>
          </section>
          <div class="action-bar"><button class="ghost" @click="go('map')"><LocateFixed/>导航</button><button class="primary" v-if="activeBooking(selected.id)" @click="go('appointments')">查看预约</button><button class="primary" v-else @click="openBookingSheet">预约参访</button></div>
        </template>
