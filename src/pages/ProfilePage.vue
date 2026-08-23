<script setup>
import { Bell, CalendarDays, ChevronRight, CircleUserRound, Heart, MapPinned, MessageCircle, Settings, UserRound } from "lucide-vue-next"

defineProps({
  profileUser: { type: Object, required: true },
  stats: { type: Object, required: true },
  isAuthenticated: { type: Boolean, default: false }
})

const emit = defineEmits(["go", "login", "logout", "notifications", "feedback", "about", "settings", "reviews"])
function go(target) { emit("go", target) }
</script>

<template>
          <header class="profile-head">
            <div class="profile-avatar"><UserRound/></div>
            <div class="profile-summary">
              <h1>{{ profileUser.real_name || profileUser.username || '未登录' }}</h1>
              <p>{{ isAuthenticated ? `ID: ${profileUser.id}` : '登录后可独立保存个人数据' }}</p>
            </div>
            <div class="profile-actions">
              <button class="profile-auth" @click="isAuthenticated ? emit('logout') : emit('login')">{{ isAuthenticated ? '退出' : '登录' }}</button>
              <button class="profile-icon" type="button" aria-label="消息通知" @click="emit('notifications')"><Bell/></button>
              <button class="profile-icon" type="button" aria-label="设置" @click="emit('settings')"><Settings/></button>
            </div>
          </header>
          <section class="profile-stats"><div class="stat-cell" @click="go('favorites')"><b>{{ stats.favorites }}</b><span>我的收藏</span></div><div class="stat-cell" @click="go('appointments')"><b>{{ stats.appointments }}</b><span>我的预约</span></div><div class="stat-cell" @click="go('history')"><b>{{ stats.history }}</b><span>浏览记录</span></div></section>
          <section class="profile-menu"><h2>我的服务</h2><div class="menu-grid"><button @click="go('favorites')"><Heart/><span>我的收藏</span></button><button @click="go('appointments')"><CalendarDays/><span>我的预约</span></button><button @click="go('history')"><MapPinned/><span>浏览记录</span></button><button @click="emit('reviews')"><MessageCircle/><span>我的评价</span></button></div></section>
          <section class="settings-list"><button @click="emit('notifications')"><Bell/>消息通知<ChevronRight/></button><button @click="emit('feedback')"><MessageCircle/>意见反馈<ChevronRight/></button><button @click="emit('about')"><CircleUserRound/>关于我们<ChevronRight/></button><button @click="emit('settings')"><Settings/>设置<ChevronRight/></button></section>

</template>
