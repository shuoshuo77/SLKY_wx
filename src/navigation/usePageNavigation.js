import { computed, watch } from "vue"
import { useRoute, useRouter } from "vue-router"

export const PAGES = {
  home: "home",
  bases: "bases",
  detail: "detail",
  map: "map",
  monitor: "monitor",
  assistant: "assistant",
  favorites: "favorites",
  appointments: "appointments",
  history: "history",
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

  async function go(target, params = {}) {
    await router.push({ name: target, params })
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  watch(page, loadPageData, { immediate: true })

  return { page, go }
}
