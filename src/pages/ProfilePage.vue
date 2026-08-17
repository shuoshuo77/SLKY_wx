<script setup>
import { Bell, CalendarDays, ChevronRight, CircleUserRound, Heart, MapPinned, MessageCircle, Settings, UserRound } from "lucide-vue-next"

defineProps({
  profileUser: { type: Object, required: true },
  stats: { type: Object, required: true }
})

const emit = defineEmits(["go"])
function go(target) { emit("go", target) }
</script>

<template>
          <header class="profile-head"><div class="profile-avatar"><UserRound/></div><div><h1>{{ profileUser.real_name || profileUser.username || '森林爱好者' }}</h1><p>ID: {{ profileUser.id || '游客' }}</p></div><Bell/><Settings/></header>
          <section class="profile-stats"><div class="stat-cell" @click="go('favorites')"><b>{{ stats.favorites }}</b><span>我的收藏</span></div><div class="stat-cell" @click="go('appointments')"><b>{{ stats.appointments }}</b><span>我的预约</span></div><div class="stat-cell" @click="go('history')"><b>{{ stats.history }}</b><span>浏览记录</span></div></section>
          <section class="profile-menu"><h2>我的服务</h2><div class="menu-grid"><button @click="go('favorites')"><Heart/><span>我的收藏</span></button><button @click="go('appointments')"><CalendarDays/><span>我的预约</span></button><button @click="go('history')"><MapPinned/><span>浏览记录</span></button><button><MessageCircle/><span>我的评价</span></button></div></section>
          <section class="settings-list"><button><Bell/>消息通知<ChevronRight/></button><button><MessageCircle/>意见反馈<ChevronRight/></button><button><CircleUserRound/>关于我们<ChevronRight/></button><button><Settings/>设置<ChevronRight/></button></section>

</template>
