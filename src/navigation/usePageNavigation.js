import { computed, watch } from "vue"
import { useRoute, useRouter } from "vue-router"

export const PAGES = {
  // 首页，对应路由 /home
  home: "home",
  // 基地列表页，对应路由 /bases
  bases: "bases",
  // 基地详情页，对应路由 /detail/:id
  detail: "detail",
  // 地图页，对应路由 /map
  map: "map",
  // 环境监测页，对应路由 /monitor
  monitor: "monitor",
  // 智能助手页，对应路由 /assistant
  assistant: "assistant",
  // 我的收藏页，对应路由 /favorites
  favorites: "favorites",
  // 我的预约页，对应路由 /appointments
  appointments: "appointments",
  // 浏览记录页，对应路由 /history
  history: "history",
  // 我的页，对应路由 /profile
  profile: "profile"
}

export function usePageNavigation({
  loadStats,
  loadFavorites,
  loadAppointments,
  loadHistory
} = {}) {
  const route = useRoute()
  const router = useRouter()
  const page = computed(() => route.name || PAGES.home)

  // 进入某些页面时，顺手加载该页面需要的本地数据。
  function loadPageData(target) {
    if (target === PAGES.profile) {
      loadStats?.()
      Promise.all([
        loadFavorites?.(),
        loadAppointments?.(),
        loadHistory?.()
      ]).catch(() => {})
    } else if (target === PAGES.favorites) {
      loadFavorites?.().catch(() => {})
    } else if (target === PAGES.appointments) {
      loadAppointments?.().catch(() => {})
    } else if (target === PAGES.history) {
      loadHistory?.().catch(() => {})
    }
  }

  // 页面跳转统一走这里：go("map") -> /map，go("detail", { id: 1 }) -> /detail/1。
  async function go(target, params = {}) {
    await router.push({ name: target, params })
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  watch(page, loadPageData, { immediate: true })

  return { page, go }
}
