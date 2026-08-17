import { createRouter, createWebHistory } from "vue-router"
import { PAGES } from "../navigation/usePageNavigation"

const EmptyView = { template: "<div />" }

// 路由表只负责 URL 和页面名的对应关系；实际页面组件仍由 App.vue 根据 route.name 渲染。
export const routes = [
  // 访问根路径时默认进入首页。
  { path: "/", redirect: "/home" },
  // 首页
  { path: "/home", name: PAGES.home, component: EmptyView },
  // 基地列表页
  { path: "/bases", name: PAGES.bases, component: EmptyView },
  // 基地详情页，id 是基地 ID，例如 /detail/1。
  { path: "/detail/:id?", name: PAGES.detail, component: EmptyView },
  // 地图页
  { path: "/map", name: PAGES.map, component: EmptyView },
  // 环境监测页
  { path: "/monitor", name: PAGES.monitor, component: EmptyView },
  // 智能助手页
  { path: "/assistant", name: PAGES.assistant, component: EmptyView },
  // 我的收藏页
  { path: "/favorites", name: PAGES.favorites, component: EmptyView },
  // 我的预约页
  { path: "/appointments", name: PAGES.appointments, component: EmptyView },
  // 浏览记录页
  { path: "/history", name: PAGES.history, component: EmptyView },
  // 我的页
  { path: "/profile", name: PAGES.profile, component: EmptyView },
  // 未匹配到的地址统一回首页。
  { path: "/:pathMatch(.*)*", redirect: "/home" }
]

export const router = createRouter({
  history: createWebHistory(),
  routes
})
