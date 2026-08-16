<script setup>
import { computed, onMounted, ref } from "vue"
import {
  ArrowLeft, Bell, Bot, CalendarDays, ChevronRight, CircleUserRound,
  CloudSun, Flame, Heart, Home, Leaf, LocateFixed, MapPinned, MessageCircle,
  Mic, Mountain, Search, Send, Settings, SlidersHorizontal, Sparkles,
  ThermometerSun, Trash2, Trees, UserRound, Wind
} from "lucide-vue-next"
import { apiRequest, ensureLogin, currentUser } from "./api"

const images = {
  hero: "/assets/images/07-首页轮播-森林.jpg",
  lake: "/assets/images/03-森林湖泊山景.jpg",
  lakeside: "/assets/images/04-湖畔山林.jpg",
  dense: "/assets/images/05-密林自然景观.jpg",
  retreat: "/assets/images/02-山地康养度假.jpg"
}

const page = ref("home")
const bases = ref([])
const hotBases = ref([])
const mapBases = ref([])
const favoriteItems = ref([])
const heroImage = ref(images.hero)
const selected = ref(null)
const mapSelected = ref(null)
const loading = ref(true)
const loadError = ref("")
const ready = computed(() => !loading.value && !loadError.value)
const searchText = ref("")
const chatText = ref("")
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
const profileUser = ref(currentUser())
const toast = ref("")
let toastTimer = null

function showToast(text) {
  toast.value = text
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ""), 2200)
}

async function withAuth(fn) {
  await ensureLogin()
  profileUser.value = currentUser()
  try {
    return await fn()
  } catch (err) {
    showToast(err.message || "操作失败")
    throw err
  }
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
  try {
    await ensureLogin()
    await apiRequest(`/miniapp/bases/${base.id}/view`, { method: "POST" })
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
  bookingError.value = ""
  showBooking.value = true
}

async function confirmBooking() {
  if (!booking.value.date || !booking.value.time) {
    bookingError.value = "请选择参访日期和时间段"
    return
  }
  if (!booking.value.name.trim() || !booking.value.phone.trim()) {
    bookingError.value = "请填写联系人和联系电话"
    return
  }
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
        }
      })
    )
    appointments.value.unshift(normalizeAppointment(item))
    showBooking.value = false
    showToast("预约提交成功，待基地确认")
  } catch {
    /* 错误提示已由 withAuth 处理 */
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
  const data = await withAuth(() => apiRequest("/miniapp/me/appointments"))
  appointments.value = (data.items || []).map(normalizeAppointment)
}

async function loadStats() {
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
  return (primary || fallback)?.file_url || null
}

function mapCard(item) {
  return {
    id: item.id,
    name: item.name,
    area: areaText(item),
    image: item.primary_image || item.base_image || item.image || fallbackImage(item.id),
    tags: parseTags(item),
    viewCount: item.view_count || 0,
    distance: item.distance_km != null ? `${item.distance_km}km` : "",
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
    const [homeData, mapData] = await Promise.all([
      apiRequest("/miniapp/home?limit=10"),
      apiRequest("/map/bases?limit=200")
    ])
    if (homeData.banners?.length) {
      heroImage.value = homeData.banners[0].image_url || images.hero
    }
    hotBases.value = (homeData.hot_bases || []).map(mapCard)
    mapBases.value = (mapData.items || []).map((item) => ({
      id: item.id,
      name: item.name,
      area: areaText(item),
      address: item.address || "",
      image: item.primary_image || fallbackImage(item.id)
    }))
    bases.value = await loadAllBases()
  } catch (err) {
    loadError.value = err.message || "数据加载失败，请确认后端已启动"
  } finally {
    loading.value = false
  }
}

async function loadAllBases() {
  const first = await apiRequest("/bases?page=1&page_size=100&sort_by=view_count&sort_order=desc")
  const items = [...(first.items || [])]
  const totalPages = Math.ceil((first.total || 0) / 100)
  if (totalPages > 1) {
    const rest = await Promise.all(
      Array.from({ length: totalPages - 1 }, (_, i) =>
        apiRequest(`/bases?page=${i + 2}&page_size=100&sort_by=view_count&sort_order=desc`)
      )
    )
    for (const page of rest) items.push(...(page.items || []))
  }
  return items.map(mapCard)
}

onMounted(loadAll)

/* ---------- 通用 ---------- */
const filteredBases = computed(() => {
  const keyword = searchText.value.trim()
  if (!keyword) return bases.value
  return bases.value.filter((item) => `${item.name}${item.area}${(item.tags || []).join("")}`.includes(keyword))
})

function go(target) {
  page.value = target
  window.scrollTo({ top: 0, behavior: "smooth" })
  if (target === "profile") {
    loadStats()
    Promise.all([loadFavorites(), loadAppointments(), loadHistory()]).catch(() => {})
  } else if (target === "favorites") {
    loadFavorites().catch(() => {})
  } else if (target === "appointments") {
    loadAppointments().catch(() => {})
  } else if (target === "history") {
    loadHistory().catch(() => {})
  }
}

async function openDetail(base) {
  if (!base || !base.id) return
  try {
    const detail = await apiRequest(`/bases/${base.id}`)
    const mapped = mapDetail(detail)
    selected.value = mapped
    recordView({ id: mapped.id, name: mapped.name, area: mapped.area, image: mapped.image })
    go("detail")
  } catch (err) {
    showToast(err.message || "加载基地详情失败")
  }
}

function openBaseById(id) {
  openDetail(bases.value.find((b) => b.id === id) || { id })
}

function sendMessage(text = chatText.value) {
  const value = text.trim()
  if (!value) return
  messages.value.push({ role: "user", text: value })
  chatText.value = ""
  setTimeout(() => messages.value.push({ role: "bot", text: "根据你的需求，青城山康养基地匹配度最高。空气质量优，夏季平均气温舒适，距离也更近。" }), 350)
}
</script>

<template>
  <div class="stage">
    <div class="phone-shell">
      <main class="app-view">
        <template v-if="page === 'home'">
          <header class="brand-bar">
            <div class="brand"><Trees :size="25"/><strong>森氧康养</strong></div>
            <div class="header-actions"><Bell :size="19"/><Settings :size="19"/></div>
          </header>

          <section v-if="loading" class="empty-state">
            <div class="empty-icon"><Leaf/></div>
            <h3>正在加载基地数据...</h3><p>从云端拉取最新康养基地</p>
          </section>
          <section v-else-if="loadError" class="empty-state">
            <div class="empty-icon"><MapPinned/></div>
            <h3>数据加载失败</h3><p>{{ loadError }}</p>
            <button @click="loadAll">重试</button>
          </section>

          <template v-else>
          <section class="hero" :style="{ backgroundImage: `url(${heroImage})` }">
            <div class="hero-copy"><h1>呼吸自然<br>享受健康生活</h1><p>探索优质康养基地</p></div>
            <div class="search-box">
              <Search :size="18"/><input v-model="searchText" placeholder="搜索基地名称、位置、特色..." @keyup.enter="go('bases')"><button @click="go('bases')">搜索</button>
            </div>
          </section>

          <section class="service-grid">
            <button @click="go('bases')"><span><Search/></span><b>基地查询</b></button>
            <button @click="go('assistant')"><span><Bot/></span><b>智能推荐</b></button>
            <button @click="go('monitor')"><span><Leaf/></span><b>环境监测</b></button>
            <button @click="openDetail(hotBases[0] || bases[0])"><span><Sparkles/></span><b>健康指南</b></button>
          </section>

          <section class="section-block">
            <div class="section-heading"><h2>热门基地</h2><button @click="go('bases')">更多 <ChevronRight :size="15"/></button></div>
            <article v-for="base in hotBases.slice(0, 3)" :key="base.id" class="base-row" @click="openDetail(base)">
              <img :src="base.image" :alt="base.name">
              <div><h3>{{ base.name }}</h3><div class="tags"><span v-for="tag in base.tags.slice(0, 3)" :key="tag">{{ tag }}</span></div><p><Flame :size="14"/> 热度 {{ base.viewCount }}</p></div>
              <button class="heart" :class="{ active: isFavorite(base.id) }" @click.stop="toggleFavorite(base)"><Heart :size="20" :fill="isFavorite(base.id) ? 'currentColor' : 'none'"/></button>
            </article>
          </section>
          </template>
        </template>

        <template v-else-if="page === 'bases'">
          <header class="page-header"><button @click="go('home')"><ArrowLeft/></button><h1>基地列表</h1><button><SlidersHorizontal/></button></header>
          <div class="list-search"><Search :size="18"/><input v-model="searchText" placeholder="搜索基地名称或地区"></div>
          <div class="chip-row"><button class="active">全部</button><button>康养</button><button>徒步</button><button>研学</button><button>生态</button></div>
          <section class="base-list">
            <article v-for="base in filteredBases" :key="base.id" class="base-card" @click="openDetail(base)">
              <img :src="base.image" :alt="base.name">
              <div class="base-card-content"><h3>{{ base.name }}</h3><p class="muted">{{ base.area }}</p><p class="rating"><Flame :size="14"/> 热度 {{ base.viewCount }}</p><div class="tags"><span v-for="tag in base.tags.slice(0, 3)" :key="tag">{{ tag }}</span></div></div>
              <button class="heart" :class="{ active: isFavorite(base.id) }" @click.stop="toggleFavorite(base)"><Heart :size="19" :fill="isFavorite(base.id) ? 'currentColor' : 'none'"/></button>
            </article>
          </section>
        </template>

        <template v-else-if="page === 'detail'">
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

        <template v-else-if="page === 'map'">
          <header class="page-header"><button @click="go('home')"><ArrowLeft/></button><h1>地图找基地</h1><button><SlidersHorizontal/></button></header>
          <section class="map-panel">
            <div class="map-grid"></div>
            <button v-for="(base, index) in mapBases.slice(0, 12)" :key="base.id" class="pin" :style="{ left: `${15 + (index % 4) * 24}%`, top: `${22 + Math.floor(index / 4) * 28}%` }" @click="mapSelected = base"><MapPinned/></button>
          </section>
          <article v-if="mapSelected" class="map-result" @click="openDetail(mapSelected)"><img :src="mapSelected.image"><div><h3>{{ mapSelected.name }}</h3><p>{{ mapSelected.area }}</p><p>{{ mapSelected.address }}</p></div><ChevronRight/></article>
          <article v-else class="map-result placeholder"><div><h3>点击地图标记查看基地</h3><p>地图数据来自后端接口</p></div></article>
        </template>

        <template v-else-if="page === 'monitor'">
          <header class="page-header"><button @click="go('home')"><ArrowLeft/></button><h1>环境监测</h1><button><Settings/></button></header>
          <section class="monitor-body"><p class="location"><MapPinned/> 青城山康养基地</p><div class="time-tabs"><b>实时监测</b><span>7天趋势</span><span>30天趋势</span></div><div class="aqi-ring"><small>空气质量</small><strong>优</strong><span>AQI 28</span></div><div class="monitor-list"><p><Leaf/>负氧离子 <b>3200 <small>个/cm³</small></b></p><p><ThermometerSun/>温度 <b>22℃</b></p><p><CloudSun/>湿度 <b>68%</b></p><p><Wind/>PM2.5 <b>12 <small>μg/m³</small></b></p></div><p class="updated">数据更新时间：今天 10:30</p></section>
        </template>

        <template v-else-if="page === 'assistant'">
          <header class="page-header"><button @click="go('home')"><ArrowLeft/></button><h1>智能助手</h1><button><Settings/></button></header>
          <section class="chat-list"><div v-for="(message, index) in messages" :key="index" class="message" :class="message.role"><span v-if="message.role === 'bot'" class="avatar"><Bot/></span><p>{{ message.text }}</p></div><article v-if="hotBases[0]" class="recommend-card" @click="openDetail(hotBases[0])"><img :src="hotBases[0].image"><div><b>{{ hotBases[0].name }}</b><span>{{ hotBases[0].area }}</span><em><Flame :size="13"/> 热度 {{ hotBases[0].viewCount }}</em></div></article></section>
          <div class="quick-prompts"><button @click="sendMessage('环境怎么样？')">环境怎么样？</button><button @click="sendMessage('附近有什么基地？')">附近有什么基地？</button></div>
          <div class="chat-composer"><input v-model="chatText" placeholder="输入你的问题..." @keyup.enter="sendMessage()"><Mic/><button @click="sendMessage()"><Send/></button></div>
        </template>

        <template v-else-if="page === 'favorites'">
          <header class="page-header"><button @click="go('profile')"><ArrowLeft/></button><h1>我的收藏</h1><button></button></header>
          <section v-if="favoriteBases.length" class="base-list">
            <article v-for="base in favoriteBases" :key="base.id" class="base-card" @click="openDetail(base)">
              <img :src="base.image" :alt="base.name">
              <div class="base-card-content"><h3>{{ base.name }}</h3><p class="muted">{{ base.area }}</p><p class="rating"><Flame :size="14"/> 热度 {{ base.viewCount }}</p><div class="tags"><span v-for="tag in base.tags.slice(0, 3)" :key="tag">{{ tag }}</span></div></div>
              <button class="heart active" @click.stop="toggleFavorite(base)"><Heart :size="19" fill="currentColor"/></button>
            </article>
          </section>
          <section v-else class="empty-state">
            <div class="empty-icon"><Heart/></div>
            <h3>还没有收藏</h3><p>在基地卡片上点一下小心心，喜欢的基地就会收藏到这里</p>
            <button @click="go('bases')">去逛逛</button>
          </section>
        </template>

        <template v-else-if="page === 'appointments'">
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

        <template v-else-if="page === 'history'">
          <header class="page-header"><button @click="go('profile')"><ArrowLeft/></button><h1>浏览记录</h1><button v-if="history.length" @click="clearHistory"><Trash2/></button><button v-else></button></header>
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

        <template v-else-if="page === 'profile'">
          <header class="profile-head"><div class="profile-avatar"><UserRound/></div><div><h1>{{ profileUser.real_name || profileUser.username || '森林爱好者' }}</h1><p>ID: {{ profileUser.id || '游客' }}</p></div><Bell/><Settings/></header>
          <section class="profile-stats"><div class="stat-cell" @click="go('favorites')"><b>{{ stats.favorites }}</b><span>我的收藏</span></div><div class="stat-cell" @click="go('appointments')"><b>{{ stats.appointments }}</b><span>我的预约</span></div><div class="stat-cell" @click="go('history')"><b>{{ stats.history }}</b><span>浏览记录</span></div></section>
          <section class="profile-menu"><h2>我的服务</h2><div class="menu-grid"><button @click="go('favorites')"><Heart/><span>我的收藏</span></button><button @click="go('appointments')"><CalendarDays/><span>我的预约</span></button><button @click="go('history')"><MapPinned/><span>浏览记录</span></button><button><MessageCircle/><span>我的评价</span></button></div></section>
          <section class="settings-list"><button><Bell/>消息通知<ChevronRight/></button><button><MessageCircle/>意见反馈<ChevronRight/></button><button><CircleUserRound/>关于我们<ChevronRight/></button><button><Settings/>设置<ChevronRight/></button></section>
        </template>
      </main>

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
            <button class="sheet-confirm" @click="confirmBooking">确认预约</button>
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
