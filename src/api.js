// 森氧康养小程序 API 客户端
// 默认走 Vite 代理（/api -> 后端），需要直连时可在浏览器控制台设置：
//   localStorage.setItem("syk_api_base", "http://127.0.0.1:8000/api")

const TOKEN_KEY = "syk_token"
const USER_KEY = "syk_user"
const STORE_KEY = "syk_mock_store"
export const AUTH_REQUIRED = "AUTH_REQUIRED"

const mockBases = [
  {
    id: 1,
    name: "青城山康养基地",
    province: "四川省",
    city: "成都市",
    district: "都江堰市",
    address: "四川省成都市都江堰市青城山景区",
    forest_coverage: 92,
    description: "依托青城山森林资源，适合避暑休闲、森林步道、康养度假和亲子研学。",
    tags: ["森林康养", "避暑", "徒步"],
    view_count: 1286,
    primary_image: "/assets/images/07-首页轮播-森林.jpg",
    resources: {
      negative_oxygen_ions: 3200,
      average_temperature: 22,
      altitude_min: 900,
      altitude_max: 1260,
      hot_spring: false
    },
    business: {
      has_accommodation: true,
      has_dining: true,
      has_medical: true,
      has_parking: true
    },
    qualifications: [{ qual_name: "国家森林康养基地", qual_level: "优质基地" }]
  },
  {
    id: 2,
    name: "庐山森林康养基地",
    province: "江西省",
    city: "九江市",
    district: "庐山市",
    address: "江西省九江市庐山市",
    forest_coverage: 88,
    description: "山地气候清凉，适合夏季避暑、慢行游览和康养旅居。",
    tags: ["山地度假", "避暑", "旅居"],
    view_count: 1058,
    primary_image: "/assets/images/03-森林湖泊山景.jpg",
    resources: {
      negative_oxygen_ions: 2800,
      average_temperature: 21,
      altitude_min: 800,
      altitude_max: 1474,
      hot_spring: false
    },
    business: {
      has_accommodation: true,
      has_dining: true,
      has_medical: false,
      has_parking: true
    },
    qualifications: [{ qual_name: "森林康养试点基地", qual_level: "示范基地" }]
  },
  {
    id: 3,
    name: "莫干山康养度假基地",
    province: "浙江省",
    city: "湖州市",
    district: "德清县",
    address: "浙江省湖州市德清县莫干山镇",
    forest_coverage: 86,
    description: "竹林、山谷和民宿资源丰富，适合周末康养、轻徒步和团建休闲。",
    tags: ["竹林", "民宿", "轻徒步"],
    view_count: 936,
    primary_image: "/assets/images/05-密林自然景观.jpg",
    resources: {
      negative_oxygen_ions: 2600,
      average_temperature: 23,
      altitude_min: 300,
      altitude_max: 720,
      hot_spring: false
    },
    business: {
      has_accommodation: true,
      has_dining: true,
      has_medical: false,
      has_parking: true
    },
    qualifications: [{ qual_name: "生态康养基地", qual_level: "特色基地" }]
  },
  {
    id: 4,
    name: "武夷山森林康养基地",
    province: "福建省",
    city: "南平市",
    district: "武夷山市",
    address: "福建省南平市武夷山市",
    forest_coverage: 90,
    description: "生态环境稳定，适合森林浴、茶文化体验和自然教育活动。",
    tags: ["森林浴", "茶旅", "自然教育"],
    view_count: 884,
    primary_image: "/assets/images/04-湖畔山林.jpg",
    resources: {
      negative_oxygen_ions: 3000,
      average_temperature: 24,
      altitude_min: 200,
      altitude_max: 900,
      hot_spring: false
    },
    business: {
      has_accommodation: true,
      has_dining: true,
      has_medical: true,
      has_parking: true
    },
    qualifications: [{ qual_name: "森林康养基地", qual_level: "生态基地" }]
  },
  {
    id: 5,
    name: "长白山温泉康养基地",
    province: "吉林省",
    city: "白山市",
    district: "抚松县",
    address: "吉林省白山市抚松县长白山保护开发区",
    forest_coverage: 87,
    description: "森林、温泉和山地资源结合，适合疗休养和冬夏两季度假。",
    tags: ["温泉", "山地", "疗休养"],
    view_count: 812,
    primary_image: "/assets/images/02-山地康养度假.jpg",
    resources: {
      negative_oxygen_ions: 2900,
      average_temperature: 18,
      altitude_min: 700,
      altitude_max: 1100,
      hot_spring: true
    },
    business: {
      has_accommodation: true,
      has_dining: true,
      has_medical: true,
      has_parking: true
    },
    qualifications: [{ qual_name: "温泉康养基地", qual_level: "特色基地" }]
  }
]

function readStore() {
  try {
    return JSON.parse(localStorage.getItem(STORE_KEY) || "{}")
  } catch {
    return {}
  }
}

function writeStore(store) {
  localStorage.setItem(STORE_KEY, JSON.stringify(store))
}

function getStore() {
  const store = readStore()
  return {
    favorites: store.favorites || [],
    history: store.history || [],
    appointments: store.appointments || []
  }
}

function publicBase(base) {
  const { resources, business, qualifications, ...item } = base
  return item
}

function areaText(base) {
  return [base.province, base.city, base.district].filter(Boolean).join(" · ")
}

function favoriteItem(baseId) {
  const base = mockBases.find((item) => item.id === Number(baseId))
  if (!base) return null
  return {
    base_id: base.id,
    base_name: base.name,
    area: areaText(base),
    base_image: base.primary_image,
    tags: base.tags,
    view_count: base.view_count
  }
}

function appointmentView(item) {
  const base = mockBases.find((baseItem) => baseItem.id === Number(item.base_id))
  return {
    ...item,
    base_name: base?.name || "康养基地",
    base_image: base?.primary_image || "",
    status_label: item.status === "cancelled" ? "已取消" : "待确认"
  }
}

function mockUser(username = "mock-user") {
  return { id: 1, username, real_name: "森林爱好者" }
}

function notFound(path) {
  throw new Error(`本地模拟接口未实现：${path}`)
}

function configuredBaseURL() {
  const envValue = import.meta.env.VITE_API_BASE_URL
  const browserValue = typeof localStorage === "undefined" ? "" : localStorage.getItem("syk_api_base")
  return (envValue || browserValue || "").replace(/\/+$/, "")
}

function baseURL() {
  return configuredBaseURL() || "/api"
}

function useMockApi() {
  const configured = configuredBaseURL()
  return configured === "mock" || import.meta.env.VITE_USE_MOCK_API === "true"
}

export function resolveApiAsset(url) {
  if (!url || url.startsWith("/assets/") || /^(?:https?:|data:)/.test(url)) return url

  const path = url.startsWith("/") ? url : `/${url}`
  const configured = configuredBaseURL()
  if (/^https?:\/\//.test(configured)) {
    return `${configured.replace(/\/api\/?$/, "")}${path}`
  }
  return path
}

function mockResponse(data) {
  return Promise.resolve(JSON.parse(JSON.stringify(data)))
}

async function mockRequest(path, { method = "GET", body } = {}) {
  const url = new URL(path, "http://mock.local")
  const pathname = url.pathname
  const requestMethod = method.toUpperCase()
  const store = getStore()

  if (requestMethod === "GET" && (pathname === "/bases" || pathname === "/bases/")) {
    const page = Number(url.searchParams.get("page") || 1)
    const pageSize = Number(url.searchParams.get("page_size") || 20)
    const items = mockBases.map(publicBase).sort((a, b) => (b.view_count || 0) - (a.view_count || 0))
    const start = (page - 1) * pageSize
    return mockResponse({ items: items.slice(start, start + pageSize), total: items.length, page, page_size: pageSize })
  }

  if (requestMethod === "GET" && pathname === "/miniapp/home") {
    const hotBases = mockBases.slice(0, Number(url.searchParams.get("limit") || 6)).map(publicBase)
    return mockResponse({
      banners: hotBases.slice(0, 3).map((base) => ({
        id: `base-${base.id}`,
        title: base.name,
        subtitle: areaText(base),
        image_url: base.primary_image,
        target_type: "base",
        target_id: base.id,
        target_url: `/detail/${base.id}`
      })),
      hot_bases: hotBases,
      feature_entries: [],
      stats: { bases_total: mockBases.length, policies_total: 0, resources_total: 0, experts_total: 0 }
    })
  }

  if (requestMethod === "GET" && pathname === "/miniapp/map/bases") {
    const page = Number(url.searchParams.get("page") || 1)
    const pageSize = Number(url.searchParams.get("page_size") || 200)
    const items = mockBases.map((base, index) => ({
      id: base.id,
      name: base.name,
      latitude: 30 + index,
      longitude: 104 + index,
      province: base.province,
      city: base.city,
      address: base.address,
      primary_image: base.primary_image
    }))
    return mockResponse({ items: items.slice((page - 1) * pageSize, page * pageSize), total: items.length, page, page_size: pageSize })
  }

  if (requestMethod === "GET" && pathname === "/miniapp/recommendations") {
    const limit = Number(url.searchParams.get("limit") || 10)
    return mockResponse({ items: mockBases.slice(0, limit).map((base) => ({ ...publicBase(base), tags: base.tags, reason: "热门推荐", distance_km: null })), recommendation_mode: "popular", location_used: false, radius_km: null })
  }

  if (requestMethod === "GET" && pathname === "/bases/provinces") {
    const counts = new Map()
    mockBases.forEach((base) => counts.set(base.province, (counts.get(base.province) || 0) + 1))
    return mockResponse([...counts.entries()].map(([province, count]) => ({ province, count })))
  }

  const baseMatch = pathname.match(/^\/bases\/(\d+)$/)
  if (requestMethod === "GET" && baseMatch) {
    const base = mockBases.find((item) => item.id === Number(baseMatch[1]))
    if (!base) notFound(path)
    return mockResponse(base)
  }

  if (requestMethod === "POST" && pathname === "/auth/login") {
    return mockResponse({ access_token: "mock-token", token_type: "bearer", user: mockUser(body?.username) })
  }

  if (requestMethod === "POST" && pathname === "/auth/register") {
    return mockResponse({ access_token: "mock-token", token_type: "bearer", user: mockUser(body?.username) })
  }

  if (requestMethod === "GET" && pathname === "/users/me") {
    return mockResponse(currentUser() || mockUser())
  }

  if (requestMethod === "GET" && pathname === "/miniapp/me/favorites") {
    return mockResponse({ items: store.favorites.map(favoriteItem).filter(Boolean) })
  }

  const favoriteMatch = pathname.match(/^\/miniapp\/me\/favorites\/(\d+)$/)
  if (favoriteMatch && (requestMethod === "PUT" || requestMethod === "DELETE")) {
    const baseId = Number(favoriteMatch[1])
    const favorites = new Set(store.favorites)
    if (requestMethod === "PUT") favorites.add(baseId)
    else favorites.delete(baseId)
    writeStore({ ...store, favorites: [...favorites] })
    return mockResponse({ favorited: requestMethod === "PUT" })
  }

  const viewMatch = pathname.match(/^\/miniapp\/bases\/(\d+)\/view$/)
  if (requestMethod === "POST" && viewMatch) {
    const baseId = Number(viewMatch[1])
    const history = [
      { base_id: baseId, viewed_at: new Date().toISOString() },
      ...store.history.filter((item) => Number(item.base_id) !== baseId)
    ].slice(0, 50)
    writeStore({ ...store, history })
    return mockResponse({ recorded: true })
  }

  if (requestMethod === "GET" && pathname === "/miniapp/me/history") {
    const items = store.history
      .map((item) => ({ ...favoriteItem(item.base_id), viewed_at: item.viewed_at }))
      .filter((item) => item.base_id)
    return mockResponse({ items })
  }

  if (requestMethod === "DELETE" && pathname === "/miniapp/me/history") {
    writeStore({ ...store, history: [] })
    return mockResponse({ cleared: store.history.length })
  }

  if (requestMethod === "GET" && pathname === "/miniapp/me/appointments") {
    return mockResponse({ items: store.appointments.map(appointmentView), total: store.appointments.length, page: 1, page_size: 20 })
  }

  if (requestMethod === "POST" && pathname === "/miniapp/me/appointments") {
    const item = {
      id: Date.now(),
      base_id: Number(body.base_id),
      visit_date: body.visit_date,
      time_slot: body.time_slot,
      people_count: body.people_count,
      contact_name: body.contact_name,
      contact_phone: body.contact_phone,
      status: "pending",
      created_at: new Date().toISOString()
    }
    const appointments = [item, ...store.appointments]
    writeStore({ ...store, appointments })
    return mockResponse(appointmentView(item))
  }

  const cancelMatch = pathname.match(/^\/miniapp\/me\/appointments\/(\d+)\/cancel$/)
  if (requestMethod === "POST" && cancelMatch) {
    const appointmentId = Number(cancelMatch[1])
    const appointments = store.appointments.map((item) =>
      Number(item.id) === appointmentId ? { ...item, status: "cancelled" } : item
    )
    writeStore({ ...store, appointments })
    const updated = appointments.find((item) => Number(item.id) === appointmentId)
    return mockResponse(appointmentView(updated))
  }

  if (requestMethod === "GET" && pathname === "/miniapp/me/stats") {
    return mockResponse({
      favorites: store.favorites.length,
      appointments: store.appointments.filter((item) => item.status !== "cancelled").length,
      history: store.history.length
    })
  }

  if (requestMethod === "POST" && pathname === "/miniapp/chat") {
    return mockResponse({
      session_id: body?.session_id || "mock-session",
      reply: "这是离线演示回复。请连接项目后端以使用智能咨询。",
      provider: "deepseek",
      suggestions: [],
      disclaimer: "健康建议仅供参考，不替代医生诊断或治疗。"
    })
  }

  if (requestMethod === "POST" && pathname === "/demands") {
    return mockResponse({ message: "需求已提交", id: Date.now() })
  }

  notFound(path)
}

function responseErrorMessage(data, status) {
  if (typeof data?.detail === "string") return data.detail
  if (Array.isArray(data?.detail)) {
    return data.detail.map((item) => item.msg || item.message).filter(Boolean).join("；") || `请求失败（${status}）`
  }

  return data?.message || `请求失败（${status}）`
}

export async function apiRequest(path, { method = "GET", body, headers: customHeaders } = {}) {
  if (useMockApi()) {
    return mockRequest(path, { method, body })
  }

  const headers = { "Content-Type": "application/json", ...customHeaders }
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) headers.Authorization = `Bearer ${token}`

  const requestUrl = `${baseURL()}${path}`
  let res
  try {
    res = await fetch(requestUrl, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined
    })
  } catch (err) {
    throw new Error(`无法连接项目后端：${requestUrl}（${err.message || "网络请求失败"}）`)
  }

  if (res.status === 401) {
    clearSession()
    const error = new Error("登录已过期，请重新登录")
    error.code = AUTH_REQUIRED
    throw error
  }

  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const error = new Error(responseErrorMessage(data, res.status))
    error.status = res.status
    throw error
  }
  return data
}

function storeSession(data) {
  localStorage.setItem(TOKEN_KEY, data.access_token)
  localStorage.setItem(USER_KEY, JSON.stringify(data.user || {}))
  return data.access_token
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function isAuthenticated() {
  return Boolean(localStorage.getItem(TOKEN_KEY))
}

export async function login(credentials) {
  const data = await apiRequest("/auth/login", { method: "POST", body: credentials })
  storeSession(data)
  return data
}

export async function register(profile) {
  return apiRequest("/auth/register", { method: "POST", body: profile })
}

export async function refreshCurrentUser() {
  const user = await apiRequest("/users/me")
  localStorage.setItem(USER_KEY, JSON.stringify(user || {}))
  return user
}

// 受保护功能必须由用户显式登录后才可访问；不再共享演示账号。
export async function ensureLogin() {
  const current = localStorage.getItem(TOKEN_KEY)
  if (current) return current
  const error = new Error("请先在“我的”页面登录后使用此功能")
  error.code = AUTH_REQUIRED
  throw error
}

export function currentUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || "null")
  } catch {
    return null
  }
}

export async function miniappChat(message, { sessionId, history = [] } = {}) {
  return apiRequest("/miniapp/chat", {
    method: "POST",
    body: {
      message,
      session_id: sessionId || undefined,
      history
    }
  })
}
