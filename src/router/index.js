import { createRouter, createWebHistory } from "vue-router"
import { PAGES } from "../navigation/usePageNavigation"

const EmptyView = { template: "<div />" }

export const routes = [
  { path: "/", redirect: "/home" },
  { path: "/home", name: PAGES.home, component: EmptyView },
  { path: "/bases", name: PAGES.bases, component: EmptyView },
  { path: "/detail/:id?", name: PAGES.detail, component: EmptyView },
  { path: "/map", name: PAGES.map, component: EmptyView },
  { path: "/monitor", name: PAGES.monitor, component: EmptyView },
  { path: "/assistant", name: PAGES.assistant, component: EmptyView },
  { path: "/favorites", name: PAGES.favorites, component: EmptyView },
  { path: "/appointments", name: PAGES.appointments, component: EmptyView },
  { path: "/history", name: PAGES.history, component: EmptyView },
  { path: "/profile", name: PAGES.profile, component: EmptyView },
  { path: "/:pathMatch(.*)*", redirect: "/home" }
]

export const router = createRouter({
  history: createWebHistory(),
  routes
})
