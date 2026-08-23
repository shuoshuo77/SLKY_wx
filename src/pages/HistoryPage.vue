<script setup>
import { ArrowLeft, MapPinned, Trash2 } from "lucide-vue-next"

defineProps({
  history: { type: Array, default: () => [] },
  timeText: { type: Function, required: true }
})

const emit = defineEmits(["go", "clearHistory", "openBaseById"])

function go(target) { emit("go", target) }
function clearHistory() { emit("clearHistory") }
function openBaseById(id) { emit("openBaseById", id) }
</script>

<template>
          <header class="page-header"><button @click="go('profile')"><ArrowLeft/></button><h1>浏览记录</h1><button v-if="history.length" aria-label="清空浏览记录" @click="clearHistory"><Trash2/></button><span v-else class="header-spacer" aria-hidden="true"></span></header>
          <section v-if="history.length" class="record-list">
            <article v-for="item in history" :key="item.id" class="history-row" @click="openBaseById(item.id)">
              <img :src="item.image" :alt="item.name">
              <div><h3>{{ item.name }}</h3><p>{{ item.area }}</p></div>
              <span class="history-time">{{ timeText(item.ts) }}</span>
            </article>
          </section>
          <section v-else class="empty-state">
            <div class="empty-icon"><MapPinned/></div>
            <h3>还没有浏览记录</h3><p>去逛逛基地，最近看过的基地会出现在这里</p>
            <button @click="go('bases')">去逛逛</button>
          </section>
        </template>
