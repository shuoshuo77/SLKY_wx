<script setup>
import { computed, onMounted, ref, watch } from "vue"
import {
  Bot, Home, Leaf, MapPinned, Mountain, ThermometerSun, Trees, UserRound
} from "lucide-vue-next"
import {
  apiRequest,
  AUTH_REQUIRED,
  clearSession,
  currentUser,
  ensureLogin,
  isAuthenticated,
  login,
  miniappChat,
  refreshCurrentUser,
  register,
  resolveApiAsset
} from "./api"
import HomePage from "./pages/HomePage.vue"
import BasesPage from "./pages/BasesPage.vue"
import DetailPage from "./pages/DetailPage.vue"
import MapPage from "./pages/MapPage.vue"
import MonitorPage from "./pages/MonitorPage.vue"
import AssistantPage from "./pages/AssistantPage.vue"
import FavoritesPage from "./pages/FavoritesPage.vue"
import AppointmentsPage from "./pages/AppointmentsPage.vue"
import HistoryPage from "./pages/HistoryPage.vue"
import ProfilePage from "./pages/ProfilePage.vue"
import { usePageNavigation } from "./navigation/usePageNavigation"
import { useRoute } from "vue-router"

const images = {
  hero: "/assets/images/07-首页轮播-森林.jpg",
  lake: "/assets/images/03-森林湖泊山景.jpg",
  lakeside: "/assets/images/04-湖畔山林.jpg",
  dense: "/assets/images/05-密林自然景观.jpg",
  retreat: "/assets/images/02-山地康养度假.jpg"
}

const bases = ref([])
const hotBases = ref([])
const mapBases = ref([])
const recommendBases = ref([])
const provinceOptions = ref([])
const selectedProvince = ref("")
const serverFilteredBases = ref(null)
const filteringBases = ref(false)
const favoriteItems = ref([])
const heroImage = ref(images.hero)
const selected = ref(null)
const mapSelected = ref(null)
const loading = ref(true)
const loadError = ref("")
const ready = computed(() => !loading.value && !loadError.value)
const searchText = ref("")
const chatText = ref("")
const assistantConversationId = ref("")
const assistantSending = ref(false)
const assistantError = ref("")
const messages = ref([
  { role: "bot", text: "你好！我是森氧康养智能助手，很高兴为你服务。" },
  { role: "user", text: "推荐适合夏季避暑的基地" },
  { role: "bot", text: "为你推荐青城山康养基地和庐山康养基地，它们气温舒适、空气质量优秀。" }
])

/* ---------- 后端数据：收藏 / 浏览记录 / 预约 ---------- */
const favorites = ref([])
const history = ref([])
const appointments = ref([])
const stats = ref({ favorites: 0, appointments: 0, history: 0 })
const profileUser = ref(currentUser() || {})
const toast = ref("")
let toastTimer = null
const authDialog = ref(false)
const authMode = ref("login")
const authSubmitting = ref(false)
const authError = ref("")
const authForm = ref({ username: "", password: "", confirmPassword: "", phone: "", realName: "" })
const feedbackDialog = ref(false)
const feedbackText = ref("")
const feedbackSubmitting = ref(false)
const infoDialog = ref(null)
const settingsDialog = ref(false)

function showToast(text) {
  toast.value = text
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ""), 2200)
}

async function withAuth(fn) {
  try {
    await ensureLogin()
    profileUser.value = currentUser() || {}
    return await fn()
  } catch (err) {
    if (err.code === AUTH_REQUIRED) openAuth("login")
    showToast(err.message || "操作失败")
    throw err
  }
}

function openAuth(mode = "login") {
  authMode.value = mode
  authError.value = ""
  authForm.value.password = ""
  authForm.value.confirmPassword = ""
  authDialog.value = true
}

function switchAuthMode(mode) {
  authMode.value = mode
  authError.value = ""
  authForm.value.password = ""
  authForm.value.confirmPassword = ""
}

async function submitAuth() {
  const username = authForm.value.username.trim()
  const password = authForm.value.password
  if (!username || !password) {
    authError.value = "请填写用户名和密码"
    return
  }
  if (authMode.value === "register") {
    if (password !== authForm.value.confirmPassword) {
      authError.value = "两次输入的密码不一致"
      return
    }
    if (password.length < 10 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) {
      authError.value = "密码至少 10 位，并同时包含字母和数字"
      return
    }
  }
  authSubmitting.value = true
  authError.value = ""
  try {
    if (authMode.value === "login") {
      await login({ username, password })
      profileUser.value = await refreshCurrentUser()
      authDialog.value = false
      showToast("登录成功")
      await Promise.all([loadStats(), loadFavorites(), loadAppointments(), loadHistory()])
    } else {
      await register({
        username,
        password,
        phone: authForm.value.phone.trim() || undefined,
        real_name: authForm.value.realName.trim() || undefined
      })
      authForm.value.password = ""
      authForm.value.confirmPassword = ""
      authForm.value.phone = ""
      authForm.value.realName = ""
      switchAuthMode("login")
      showToast("注册成功，请使用新账号登录")
    }
  } catch (err) {
    authError.value = err.message || (authMode.value === "login" ? "登录失败" : "注册失败")
  } finally {
    authSubmitting.value = false
  }
}

function logout() {
  clearSession()
  settingsDialog.value = false
  profileUser.value = {}
  favorites.value = []
  favoriteItems.value = []
  history.value = []
  appointments.value = []
  stats.value = { favorites: 0, appointments: 0, history: 0 }
  showToast("已退出登录")
}

function showNotifications() {
  showToast("暂无未读消息")
}

function openFeedback() {
  if (!isAuthenticated()) {
    showToast("登录后可以提交意见反馈")
    openAuth("login")
    return
  }
  feedbackDialog.value = true
}

async function submitFeedback() {
  const content = feedbackText.value.trim()
  if (content.length < 5) {
    showToast("请至少填写 5 个字")
    return
  }
  feedbackSubmitting.value = true
  try {
    await withAuth(() => apiRequest("/demands", { method: "POST", body: { feedback: content } }))
    feedbackText.value = ""
    feedbackDialog.value = false
    showToast("反馈已提交，感谢你的建议")
  } catch (err) {
    if (err.code === AUTH_REQUIRED) feedbackDialog.value = false
  } finally {
    feedbackSubmitting.value = false
  }
}

function openAbout() {
  infoDialog.value = {
    title: "关于森氧康养",
    text: "森氧康养帮助你查找森林康养基地、查看环境信息并提交参访预约。"
  }
}

function openReviews() {
  infoDialog.value = {
    title: "我的评价",
    text: "暂时还没有可展示的评价。你可以通过“意见反馈”告诉我们使用感受。",
    action: "feedback"
  }
}

function handleInfoAction() {
  const action = infoDialog.value?.action
  infoDialog.value = null
  if (action === "feedback") openFeedback()
}

function openSettings() {
  if (!isAuthenticated()) {
    openAuth("login")
    return
  }
  settingsDialog.value = true
}

function normalizeHistoryItem(item) {
  return {
    id: item.base_id,
    name: item.base_name,
    area: item.area || "",
    image: item.base_image || "",
    ts: item.viewed_at ? new Date(item.viewed_at).getTime() : Date.now()
  }
}

function normalizeAppointment(item) {
  return {
    id: item.id,
    baseId: item.base_id,
    baseName: item.base_name,
    baseImage: item.base_image || "",
    date: item.visit_date,
    time: item.time_slot,
    people: item.people_count,
    name: item.contact_name,
    phone: item.contact_phone,
    status: item.status_label || item.status,
    createdAt: item.created_at ? new Date(item.created_at).getTime() : Date.now()
  }
}

/* ---------- 我的收藏 ---------- */
function isFavorite(id) {
  return favorites.value.includes(id)
}

async function toggleFavorite(base) {
  const idx = favorites.value.indexOf(base.id)
  const before = [...favorites.value]
  if (idx >= 0) favorites.value.splice(idx, 1)
  else favorites.value.push(base.id)
  try {
    await withAuth(() =>
      idx >= 0
        ? apiRequest(`/miniapp/me/favorites/${base.id}`, { method: "DELETE" })
        : apiRequest(`/miniapp/me/favorites/${base.id}`, { method: "PUT" })
    )
    showToast(idx >= 0 ? "已取消收藏" : "收藏成功")
    if (idx >= 0) favoriteItems.value = favoriteItems.value.filter((item) => item.id !== base.id)
  } catch {
    favorites.value = before
  }
}

const favoriteBases = favoriteItems

async function loadFavorites() {
  if (!isAuthenticated()) {
    favoriteItems.value = []
    favorites.value = []
    return
  }
  const data = await withAuth(() => apiRequest("/miniapp/me/favorites"))
  favoriteItems.value = (data.items || []).map((item) => ({
    id: item.base_id,
    name: item.base_name,
    area: item.area || "",
    image: item.base_image || fallbackImage(item.base_id),
    tags: item.tags || [],
    viewCount: item.view_count || 0
  }))
  favorites.value = favoriteItems.value.map((item) => item.id)
}

/* ---------- 浏览记录 ---------- */
async function recordView(base) {
  if (!isAuthenticated()) return
  try {
    await withAuth(() => apiRequest(`/miniapp/bases/${base.id}/view`, { method: "POST" }))
    history.value = [
      { id: base.id, name: base.name, area: base.area, image: base.image, ts: Date.now() },
      ...history.value.filter((h) => h.id !== base.id)
    ].slice(0, 50)
  } catch {
    /* 浏览记录失败不影响浏览 */
  }
}

function timeText(ts) {
  const diff = Date.now() - ts
  const min = Math.floor(diff / 60000)
  if (min < 1) return "刚刚"
  if (min < 60) return `${min}分钟前`
  const hour = Math.floor(min / 60)
  if (hour < 24) return `${hour}小时前`
  const d = new Date(ts)
  const pad = (n) => String(n).padStart(2, "0")
  return `${d.getMonth() + 1}月${d.getDate()}日 ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function loadHistory() {
  if (!isAuthenticated()) {
    history.value = []
    return
  }
  const data = await withAuth(() => apiRequest("/miniapp/me/history"))
  history.value = (data.items || []).map(normalizeHistoryItem)
}

async function clearHistory() {
  await withAuth(() => apiRequest("/miniapp/me/history", { method: "DELETE" }))
  history.value = []
  showToast("浏览记录已清空")
}

/* ---------- 我的预约 ---------- */
const timeSlots = ["09:00-10:00", "10:30-11:30", "14:00-15:00", "15:30-16:30"]
const showBooking = ref(false)
const bookingError = ref("")
const booking = ref({ date: "", time: "", people: 1, name: "", phone: "" })
const cancelTarget = ref(null)
const bookingSubmitting = ref(false)
const appointmentRequestKey = ref("")

const today = computed(() => {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
})

const activeAppointmentCount = computed(
  () => appointments.value.filter((a) => a.status !== "已取消").length
)

const sortedAppointments = computed(() =>
  [...appointments.value].sort((a, b) => b.createdAt - a.createdAt)
)

function activeBooking(baseId) {
  return appointments.value.find((a) => a.baseId === baseId && a.status !== "已取消")
}

function openBookingSheet() {
  booking.value = { date: today.value, time: "", people: 1, name: "", phone: "" }
  appointmentRequestKey.value = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`
  bookingError.value = ""
  showBooking.value = true
}

async function confirmBooking() {
  if (bookingSubmitting.value) return
  if (!booking.value.date || !booking.value.time) {
    bookingError.value = "请选择参访日期和时间段"
    return
  }
  if (!booking.value.name.trim() || !booking.value.phone.trim()) {
    bookingError.value = "请填写联系人和联系电话"
    return
  }
  bookingSubmitting.value = true
  try {
    const item = await withAuth(() =>
      apiRequest("/miniapp/me/appointments", {
        method: "POST",
        body: {
          base_id: selected.value.id,
          visit_date: booking.value.date,
          time_slot: booking.value.time,
          people_count: booking.value.people,
          contact_name: booking.value.name.trim(),
          contact_phone: booking.value.phone.trim()
        },
        headers: { "Idempotency-Key": appointmentRequestKey.value }
      })
    )
    appointments.value.unshift(normalizeAppointment(item))
    showBooking.value = false
    showToast("预约提交成功，待基地确认")
  } catch {
    /* 错误提示已由 withAuth 处理 */
  } finally {
    bookingSubmitting.value = false
  }
}

function cancelAppointment(item) {
  cancelTarget.value = item
}

async function doCancel() {
  const item = cancelTarget.value
  if (!item) return
  try {
    const updated = await withAuth(() =>
      apiRequest(`/miniapp/me/appointments/${item.id}/cancel`, { method: "POST" })
    )
    Object.assign(item, normalizeAppointment(updated))
    cancelTarget.value = null
    showToast("预约已取消")
  } catch {
    /* 错误提示已由 withAuth 处理 */
  }
}

async function loadAppointments() {
  if (!isAuthenticated()) {
    appointments.value = []
    return
  }
  const data = await withAuth(() => apiRequest("/miniapp/me/appointments"))
  appointments.value = (data.items || []).map(normalizeAppointment)
}

async function loadStats() {
  if (!isAuthenticated()) {
    stats.value = { favorites: 0, appointments: 0, history: 0 }
    return
  }
  try {
    const data = await withAuth(() => apiRequest("/miniapp/me/stats"))
    stats.value = data
  } catch {
    /* 保持已有统计 */
  }
}

/* ---------- 基地数据（后端接口） ---------- */
function fallbackImage(id) {
  return [images.lake, images.lakeside, images.dense, images.retreat][(id - 1) % 4] || images.hero
}

function areaText(item) {
  return [item.province, item.city, item.district].filter(Boolean).join(" · ") || item.area || ""
}

function parseTags(item) {
  if (Array.isArray(item.tags) && item.tags.length) return item.tags
  if (typeof item.tags === "string" && item.tags.trim()) {
    return item.tags.split(/[,，]/).map((tag) => tag.trim()).filter(Boolean)
  }
  return []
}

function primaryImage(detail) {
  const ordered = [...(detail.media || [])].sort((a, b) => a.sort_order - b.sort_order)
  const primary = ordered.find((item) => item.is_primary)
  const fallback = ordered.find((item) => item.media_type === "image")
  return resolveApiAsset((primary || fallback)?.file_url || null)
}

function mapCard(item) {
  return {
    id: item.id,
    name: item.name,
    area: areaText(item),
    address: item.address || "",
    image: resolveApiAsset(item.primary_image || item.base_image || item.image) || fallbackImage(item.id),
    tags: parseTags(item),
    viewCount: item.view_count || 0,
    distance: item.distance_km != null ? `${item.distance_km}km` : "",
    reason: item.reason || "",
    desc: item.description || ""
  }
}

function detailTags(detail) {
  const quals = (detail.qualifications || []).map((q) => q.qual_level || q.qual_name).filter(Boolean)
  return [...new Set([...quals, ...parseTags(detail)])].slice(0, 6)
}

function buildMetrics(detail) {
  const res = detail.resources || {}
  const altitude = [res.altitude_min, res.altitude_max].filter((v) => v != null)
  return [
    {
      icon: Leaf,
      label: "负氧离子",
      value: res.negative_oxygen_ions != null ? res.negative_oxygen_ions : "暂无",
      unit: res.negative_oxygen_ions != null ? "个/cm³" : ""
    },
    {
      icon: ThermometerSun,
      label: "平均气温",
      value: res.average_temperature != null ? `${res.average_temperature}℃` : "暂无",
      unit: res.average_temperature != null ? "舒适" : ""
    },
    {
      icon: Trees,
      label: "森林覆盖率",
      value: detail.forest_coverage != null ? `${detail.forest_coverage}%` : "暂无",
      unit: detail.forest_coverage != null ? "高覆盖" : ""
    },
    {
      icon: Mountain,
      label: "海拔",
      value: altitude.length ? altitude.join("~") + "m" : "暂无",
      unit: altitude.length ? "米" : ""
    }
  ]
}

function buildServices(detail) {
  const b = detail.business || {}
  const list = []
  if (b.has_accommodation) list.push("住宿")
  if (b.has_dining) list.push("餐饮")
  if (b.has_medical) list.push("医疗服务")
  if (b.has_parking) list.push("停车")
  if (detail.resources?.hot_spring) list.push("温泉")
  return list.length ? list : ["森林步道", "导览服务"]
}

function mapDetail(detail) {
  return {
    id: detail.id,
    name: detail.name,
    area: areaText(detail),
    address: detail.address || "",
    image: primaryImage(detail) || fallbackImage(detail.id),
    tags: detailTags(detail),
    viewCount: detail.view_count || 0,
    desc: detail.description || "暂无详细介绍",
    metrics: buildMetrics(detail),
    services: buildServices(detail)
  }
}

async function loadAll() {
  loading.value = true
  loadError.value = ""
  try {
    const [allBases, home, map, recommendations, provinces] = await Promise.all([
      loadAllBases(),
      apiRequest("/miniapp/home?limit=10"),
      apiRequest("/miniapp/map/bases?page_size=200"),
      apiRequest("/miniapp/recommendations?limit=10"),
      apiRequest("/bases/provinces")
    ])
    bases.value = allBases
    hotBases.value = (home.hot_bases || []).map(mapCard)
    if (!hotBases.value.length) hotBases.value = allBases.slice(0, 10)
    mapBases.value = (map.items || []).map(mapCard)
    if (!mapBases.value.length) mapBases.value = allBases.slice(0, 200)
    recommendBases.value = (recommendations.items || []).map(mapCard)
    provinceOptions.value = provinces || []
    mapSelected.value ||= mapBases.value[0] || null
  } catch (err) {
    loadError.value = err.message || "数据加载失败，请确认后端已启动"
  } finally {
    loading.value = false
  }
}

async function loadAllBases({ keyword = "", province = "" } = {}) {
  const query = new URLSearchParams({ page: "1", page_size: "100", sort_by: "view_count", sort_order: "desc" })
  if (keyword.trim()) query.set("keyword", keyword.trim())
  if (province) query.set("province", province)
  const first = await apiRequest(`/bases/?${query}`)
  const items = [...(first.items || [])]
  const totalPages = Math.ceil((first.total || 0) / 100)
  if (totalPages > 1) {
    const rest = await Promise.all(
      Array.from({ length: totalPages - 1 }, (_, i) => {
        const pageQuery = new URLSearchParams(query)
        pageQuery.set("page", String(i + 2))
        return apiRequest(`/bases/?${pageQuery}`)
      })
    )
    for (const page of rest) items.push(...(page.items || []))
  }
  return items.map(mapCard)
}

async function restoreProfile() {
  if (!isAuthenticated()) return
  try {
    profileUser.value = await refreshCurrentUser()
  } catch (err) {
    if (err.code !== AUTH_REQUIRED) return
    clearSession()
    profileUser.value = {}
  }
}

onMounted(() => {
  loadAll()
  restoreProfile()
})

/* ---------- 通用 ---------- */
const filteredBases = computed(() => {
  if (serverFilteredBases.value) return serverFilteredBases.value
  const keyword = searchText.value.trim()
  if (!keyword) return bases.value
  return bases.value.filter((item) => `${item.name}${item.area}${(item.tags || []).join("")}`.includes(keyword))
})

async function applyBaseFilter({ keyword = searchText.value, province = selectedProvince.value } = {}) {
  searchText.value = keyword
  selectedProvince.value = province
  filteringBases.value = true
  try {
    serverFilteredBases.value = await loadAllBases({ keyword, province })
  } catch (err) {
    showToast(err.message || "筛选失败，请稍后重试")
  } finally {
    filteringBases.value = false
  }
}

const { page, go } = usePageNavigation({
  loadStats,
  loadFavorites,
  loadAppointments,
  loadHistory
})
const route = useRoute()

function openMapFilter() {
  go("bases")
  showToast("可按关键词和省份筛选基地")
}

function clearAssistantConversation() {
  if (assistantSending.value) {
    showToast("正在生成回复，请稍候")
    return
  }
  chatText.value = ""
  assistantConversationId.value = ""
  assistantError.value = ""
  messages.value = [{ role: "bot", text: "你好！我是森氧康养智能助手，很高兴为你服务。" }]
  showToast("已清空本次对话")
}

async function loadDetailById(id, shouldNavigate = false) {
  if (!id) return
  try {
    const detail = await apiRequest(`/bases/${id}`)
    const mapped = mapDetail(detail)
    selected.value = mapped
    recordView({ id: mapped.id, name: mapped.name, area: mapped.area, image: mapped.image })
    if (shouldNavigate) go("detail", { id: mapped.id })
  } catch (err) {
    showToast(err.message || "加载基地详情失败")
  }
}

async function openDetail(base) {
  if (!base || !base.id) return
  await loadDetailById(base.id, true)
}

function openBaseById(id) {
  openDetail(bases.value.find((b) => b.id === id) || { id })
}

watch(
  () => [page.value, route.params.id],
  ([currentPage, id]) => {
    if (currentPage === "detail" && id && Number(selected.value?.id) !== Number(id)) {
      loadDetailById(id)
    }
  },
  { immediate: true }
)

async function sendMessage(text = chatText.value) {
  const value = text.trim()
  if (!value || assistantSending.value) return
  if (!isAuthenticated()) {
    assistantError.value = "请先登录后使用智能咨询"
    openAuth("login")
    return
  }
  messages.value.push({ role: "user", text: value })
  chatText.value = ""
  assistantSending.value = true
  assistantError.value = ""
  try {
    const history = messages.value
      .slice(0, -1)
      .filter((message) => message.role === "user" || message.role === "bot")
      .slice(-20)
      .map((message) => ({
        role: message.role === "bot" ? "assistant" : "user",
        content: message.text
      }))
    const data = await withAuth(() => miniappChat(value, { sessionId: assistantConversationId.value, history }))
    assistantConversationId.value = data.session_id || assistantConversationId.value
    messages.value.push({ role: "bot", text: data.reply || "智能助手暂时没有返回内容。" })
  } catch (err) {
    assistantError.value = err.message || "智能助手请求失败"
    messages.value.push({ role: "bot", text: "智能助手暂时连接失败，请稍后再试。" })
  } finally {
    assistantSending.value = false
  }
}
</script>

<template>
  <div class="stage">
    <div class="phone-shell">
      <main class="app-view">
        <HomePage
          v-if="page === 'home'"
          v-model:search-text="searchText"
          :loading="loading"
          :load-error="loadError"
          :hero-image="heroImage"
          :hot-bases="hotBases"
          :bases="bases"
          :is-favorite="isFavorite"
          @load-all="loadAll"
          @go="go"
          @open-detail="openDetail"
          @toggle-favorite="toggleFavorite"
          @notifications="showNotifications"
          @settings="openSettings"
        />
        <BasesPage
          v-else-if="page === 'bases'"
          v-model:search-text="searchText"
          :filtered-bases="filteredBases"
          :provinces="provinceOptions"
          :selected-province="selectedProvince"
          :loading="filteringBases"
          :is-favorite="isFavorite"
          @go="go"
          @apply-filter="applyBaseFilter"
          @open-detail="openDetail"
          @toggle-favorite="toggleFavorite"
        />
        <DetailPage
          v-else-if="page === 'detail' && selected"
          :selected="selected"
          :is-favorite="isFavorite"
          :active-booking="activeBooking"
          @go="go"
          @toggle-favorite="toggleFavorite"
          @open-booking-sheet="openBookingSheet"
        />
        <MapPage
          v-else-if="page === 'map'"
          v-model:map-selected="mapSelected"
          :map-bases="mapBases"
          @go="go"
          @open-detail="openDetail"
          @open-filter="openMapFilter"
        />
        <MonitorPage v-else-if="page === 'monitor'" @go="go" @notify="showToast" />
        <AssistantPage
          v-else-if="page === 'assistant'"
          v-model:chat-text="chatText"
          :messages="messages"
          :featured-base="recommendBases[0] || hotBases[0] || bases[0] || null"
          :is-sending="assistantSending"
          :error="assistantError"
          @go="go"
          @open-detail="openDetail"
          @send-message="sendMessage"
          @clear-chat="clearAssistantConversation"
          @notify="showToast"
        />
        <FavoritesPage
          v-else-if="page === 'favorites'"
          :favorite-bases="favoriteBases"
          @go="go"
          @open-detail="openDetail"
          @toggle-favorite="toggleFavorite"
        />
        <AppointmentsPage
          v-else-if="page === 'appointments'"
          :appointments="appointments"
          :sorted-appointments="sortedAppointments"
          @go="go"
          @open-base-by-id="openBaseById"
          @cancel-appointment="cancelAppointment"
        />
        <HistoryPage
          v-else-if="page === 'history'"
          :history="history"
          :time-text="timeText"
          @go="go"
          @clear-history="clearHistory"
          @open-base-by-id="openBaseById"
        />
        <ProfilePage
          v-else-if="page === 'profile'"
          :profile-user="profileUser"
          :stats="stats"
          :is-authenticated="isAuthenticated()"
          @go="go"
          @login="openAuth('login')"
          @logout="logout"
          @notifications="showNotifications"
          @feedback="openFeedback"
          @about="openAbout"
          @settings="openSettings"
          @reviews="openReviews"
        />
      </main>

      <div v-if="authDialog" class="sheet-mask" @click.self="authDialog = false">
        <form class="auth-sheet" novalidate @submit.prevent="submitAuth">
          <div class="sheet-handle"></div>
          <div class="auth-top">
            <div class="auth-welcome"><span><Leaf/></span><div><p>森氧康养</p><h2>{{ authMode === 'login' ? '欢迎回来' : '创建账号' }}</h2></div></div>
            <button class="auth-close" type="button" @click="authDialog = false">关闭</button>
          </div>
          <div class="auth-tabs" role="tablist" aria-label="认证方式">
            <button type="button" :class="{ active: authMode === 'login' }" @click="switchAuthMode('login')">登录</button>
            <button type="button" :class="{ active: authMode === 'register' }" @click="switchAuthMode('register')">注册</button>
          </div>
          <p class="sheet-sub">{{ authMode === 'login' ? '登录后可独立保存收藏、预约和浏览记录。' : '注册成功后，请使用新账号登录。' }}</p>
          <label class="field"><span>用户名</span><input v-model="authForm.username" autocomplete="username" minlength="3" maxlength="50" placeholder="3 至 50 个字符"></label>
          <label class="field"><span>密码</span><input v-model="authForm.password" type="password" :autocomplete="authMode === 'login' ? 'current-password' : 'new-password'" minlength="10" maxlength="100" placeholder="至少 10 位，含字母和数字"></label>
          <template v-if="authMode === 'register'">
            <label class="field"><span>确认密码</span><input v-model="authForm.confirmPassword" type="password" autocomplete="new-password" minlength="10" maxlength="100" placeholder="请再次输入密码"></label>
            <label class="field"><span>手机号（选填）</span><input v-model="authForm.phone" type="tel" autocomplete="tel" maxlength="20" placeholder="便于后续联系"></label>
            <label class="field"><span>昵称（选填）</span><input v-model="authForm.realName" autocomplete="name" maxlength="50" placeholder="在个人中心展示"></label>
          </template>
          <p v-if="authError" class="field-error">{{ authError }}</p>
          <button type="submit" class="auth-primary" :disabled="authSubmitting">{{ authSubmitting ? '请稍候…' : authMode === 'login' ? '登录' : '注册' }}</button>
          <p class="auth-switch">{{ authMode === 'login' ? '还没有账号？' : '已有账号？' }}<button type="button" @click="switchAuthMode(authMode === 'login' ? 'register' : 'login')">{{ authMode === 'login' ? '立即注册' : '立即登录' }}</button></p>
        </form>
      </div>

      <div v-if="feedbackDialog" class="sheet-mask" @click.self="feedbackDialog = false">
        <form class="booking-sheet feedback-sheet" @submit.prevent="submitFeedback">
          <div class="sheet-handle"></div>
          <h2>意见反馈</h2>
          <p class="sheet-sub">你的建议会提交到项目后台，帮助我们持续改进。</p>
          <label class="field"><span>反馈内容</span><textarea v-model="feedbackText" minlength="5" maxlength="1000" placeholder="请描述你遇到的问题或建议（至少 5 个字）"></textarea></label>
          <div class="sheet-actions">
            <button type="button" class="sheet-cancel" @click="feedbackDialog = false">取消</button>
            <button type="submit" class="sheet-confirm" :disabled="feedbackSubmitting">{{ feedbackSubmitting ? '提交中…' : '提交反馈' }}</button>
          </div>
        </form>
      </div>

      <div v-if="infoDialog" class="sheet-mask" @click.self="infoDialog = null">
        <div class="confirm-sheet">
          <h2>{{ infoDialog.title }}</h2>
          <p>{{ infoDialog.text }}</p>
          <div class="sheet-actions">
            <button class="sheet-cancel" @click="infoDialog = null">关闭</button>
            <button v-if="infoDialog.action" class="sheet-confirm" @click="handleInfoAction">去反馈</button>
          </div>
        </div>
      </div>

      <div v-if="settingsDialog" class="sheet-mask" @click.self="settingsDialog = false">
        <div class="confirm-sheet">
          <h2>设置</h2>
          <p>当前登录账号：{{ profileUser.real_name || profileUser.username }}。退出登录后，本机保存的登录状态会被清除。</p>
          <div class="sheet-actions">
            <button class="sheet-cancel" @click="settingsDialog = false">取消</button>
            <button class="sheet-danger" @click="logout">退出登录</button>
          </div>
        </div>
      </div>

      <div v-if="showBooking" class="sheet-mask" @click.self="showBooking = false">
        <div class="booking-sheet">
          <div class="sheet-handle"></div>
          <h2>预约参访</h2>
          <p class="sheet-sub">{{ selected.name }} · {{ selected.area }}</p>
          <div class="field"><span>参访日期</span><input type="date" v-model="booking.date" :min="today"></div>
          <div class="field">
            <span>时间段</span>
            <div class="slot-row">
              <button v-for="slot in timeSlots" :key="slot" :class="{ active: booking.time === slot }" @click="booking.time = slot">{{ slot }}</button>
            </div>
          </div>
          <div class="field">
            <span>参访人数</span>
            <div class="stepper">
              <button :disabled="booking.people <= 1" @click="booking.people = Math.max(1, booking.people - 1)">−</button>
              <b>{{ booking.people }} 人</b>
              <button :disabled="booking.people >= 10" @click="booking.people = Math.min(10, booking.people + 1)">＋</button>
            </div>
          </div>
          <label class="field"><span>联系人</span><input v-model="booking.name" placeholder="请输入姓名"></label>
          <label class="field"><span>联系电话</span><input v-model="booking.phone" type="tel" placeholder="请输入手机号"></label>
          <p v-if="bookingError" class="field-error">{{ bookingError }}</p>
          <div class="sheet-actions">
            <button class="sheet-cancel" @click="showBooking = false">取消</button>
            <button class="sheet-confirm" :disabled="bookingSubmitting" @click="confirmBooking">{{ bookingSubmitting ? '提交中…' : '确认预约' }}</button>
          </div>
        </div>
      </div>

      <div v-if="cancelTarget" class="sheet-mask" @click.self="cancelTarget = null">
        <div class="confirm-sheet">
          <h2>取消预约</h2>
          <p>确定取消「{{ cancelTarget.baseName }}」{{ cancelTarget.date }} {{ cancelTarget.time }} 的预约吗？取消后名额将自动释放。</p>
          <div class="sheet-actions">
            <button class="sheet-cancel" @click="cancelTarget = null">再想想</button>
            <button class="sheet-danger" @click="doCancel">确认取消</button>
          </div>
        </div>
      </div>

      <div v-if="toast" class="toast">{{ toast }}</div>

      <nav v-if="!['detail','monitor'].includes(page)" class="bottom-nav">
        <button :class="{ active: page === 'home' || page === 'bases' }" @click="go('home')"><Home/><span>首页</span></button>
        <button :class="{ active: page === 'map' }" @click="go('map')"><MapPinned/><span>地图</span></button>
        <button :class="{ active: page === 'assistant' }" @click="go('assistant')"><Bot/><span>智能助手</span></button>
        <button :class="{ active: page === 'profile' }" @click="go('profile')"><UserRound/><span>我的</span></button>
      </nav>
    </div>
  </div>
</template>
