<script setup>
import { ArrowLeft, CalendarDays, UserRound } from "lucide-vue-next"

defineProps({
  appointments: { type: Array, default: () => [] },
  sortedAppointments: { type: Array, default: () => [] }
})

const emit = defineEmits(["go", "openBaseById", "cancelAppointment"])

function go(target) { emit("go", target) }
function openBaseById(id) { emit("openBaseById", id) }
function cancelAppointment(item) { emit("cancelAppointment", item) }
</script>

<template>
          <header class="page-header"><button @click="go('profile')"><ArrowLeft/></button><h1>我的预约</h1><button @click="go('bases')">去预约</button></header>
          <section v-if="appointments.length" class="record-list">
            <article v-for="item in sortedAppointments" :key="item.id" class="appoint-card" @click="openBaseById(item.baseId)">
              <img :src="item.baseImage" :alt="item.baseName">
              <div><h3>{{ item.baseName }}</h3><p><CalendarDays :size="14"/> {{ item.date }} · {{ item.time }}</p><p><UserRound :size="14"/> {{ item.people }}人 · {{ item.name }}</p></div>
              <div class="appoint-side">
                <span class="status" :class="item.status">{{ item.status }}</span>
                <button v-if="item.status !== '已取消'" @click.stop="cancelAppointment(item)">取消预约</button>
              </div>
            </article>
          </section>
          <section v-else class="empty-state">
            <div class="empty-icon"><CalendarDays/></div>
            <h3>还没有预约</h3><p>挑选一个心仪的康养基地，预约属于你的自然之旅</p>
            <button @click="go('bases')">去预约</button>
          </section>
        </template>
