<script setup>
import { computed, onMounted, ref, watch } from "vue"
import {
  Bot, Home, Leaf, MapPinned, Mountain, ThermometerSun, Trees, UserRound
} from "lucide-vue-next"
import { apiRequest, ensureLogin, currentUser, cozeChat } from "./api"
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
  { role: "bot", text: "你好！我是森氧康养智能助手，很高兴为你服务。" }
])

/* ---------- 后端数据：收藏 / 浏览记录 / 预约 ---------- */
const favorites = ref([])
const history = ref([])
const appointments = ref([])
const stats = ref({ favorites: 0, appointments: 0, history: 0 })
const profileUser = ref(currentUser() || {})
const toast = ref("")
let toastTimer = null

function showToast(text) {
  toast.value = text
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ""), 2200)
}

async function withAuth(fn) {
  await ensureLogin()
  profileUser.value = currentUser() || {}
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
    address: item.address || "",
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
    const allBases = await loadAllBases()
    bases.value = allBases
    hotBases.value = allBases.slice(0, 10)
    mapBases.value = allBases.slice(0, 200)
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

const { page, go } = usePageNavigation({
  loadStats,
  loadFavorites,
  loadAppointments,
  loadHistory
})
const route = useRoute()

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
  messages.value.push({ role: "user", text: value })
  chatText.value = ""
  assistantSending.value = true
  assistantError.value = ""
  try {
    const data = await cozeChat(value, { conversationId: assistantConversationId.value })
    assistantConversationId.value = data.conversation_id || assistantConversationId.value
    messages.value.push({ role: "bot", text: data.answer || "智能助手暂时没有返回内容。" })
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
        />
        <BasesPage
          v-else-if="page === 'bases'"
          v-model:search-text="searchText"
          :filtered-bases="filteredBases"
          :is-favorite="isFavorite"
          @go="go"
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
        />
        <MonitorPage v-else-if="page === 'monitor'" @go="go" />
        <AssistantPage
          v-else-if="page === 'assistant'"
          v-model:chat-text="chatText"
          :messages="messages"
          :is-sending="assistantSending"
          :error="assistantError"
          @go="go"
          @send-message="sendMessage"
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
          @go="go"
        />
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
