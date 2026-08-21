// 森氧康养小程序 API 客户端
// 默认走 Vite 代理（/api -> 后端），需要直连时可在浏览器控制台设置：
//   localStorage.setItem("syk_api_base", "http://127.0.0.1:8000/api")

const TOKEN_KEY = "syk_token"
const USER_KEY = "syk_user"
const STORE_KEY = "syk_mock_store"
const DEMO_USERNAME = "syk_demo"
const DEMO_PASSWORD = "syk123456"

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

function mockUser(username = DEMO_USERNAME) {
  return { id: 1, username, real_name: "森林爱好者" }
}

function notFound(path) {
  throw new Error(`本地模拟接口未实现：${path}`)
}

function configuredBaseURL() {
  const localValue = localStorage.getItem("syk_api_base")
  const envValue = import.meta.env.VITE_API_BASE_URL
  return (localValue || envValue || "").replace(/\/+$/, "")
}

function baseURL() {
  return configuredBaseURL() || "/api"
}

function useMockApi() {
  const configured = configuredBaseURL()
  return !configured || configured === "mock"
}

function mockResponse(data) {
  return Promise.resolve(JSON.parse(JSON.stringify(data)))
}

async function mockRequest(path, { method = "GET", body } = {}) {
  const url = new URL(path, "http://mock.local")
  const pathname = url.pathname
  const requestMethod = method.toUpperCase()
  const store = getStore()

  if (requestMethod === "GET" && pathname === "/bases") {
    const page = Number(url.searchParams.get("page") || 1)
    const pageSize = Number(url.searchParams.get("page_size") || 20)
    const items = mockBases.map(publicBase).sort((a, b) => (b.view_count || 0) - (a.view_count || 0))
    const start = (page - 1) * pageSize
    return mockResponse({ items: items.slice(start, start + pageSize), total: items.length })
  }

  const baseMatch = pathname.match(/^\/bases\/(\d+)$/)
  if (requestMethod === "GET" && baseMatch) {
    const base = mockBases.find((item) => item.id === Number(baseMatch[1]))
    if (!base) notFound(path)
    return mockResponse(base)
  }

  if (requestMethod === "POST" && pathname === "/auth/login") {
    return mockResponse({ access_token: "mock-token", user: mockUser(body?.username) })
  }

  if (requestMethod === "POST" && pathname === "/auth/register") {
    return mockResponse({ ok: true, user: mockUser(body?.username) })
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
    return mockResponse({ ok: true })
  }

  const viewMatch = pathname.match(/^\/miniapp\/bases\/(\d+)\/view$/)
  if (requestMethod === "POST" && viewMatch) {
    const baseId = Number(viewMatch[1])
    const history = [
      { base_id: baseId, viewed_at: new Date().toISOString() },
      ...store.history.filter((item) => Number(item.base_id) !== baseId)
    ].slice(0, 50)
    writeStore({ ...store, history })
    return mockResponse({ ok: true })
  }

  if (requestMethod === "GET" && pathname === "/miniapp/me/history") {
    const items = store.history
      .map((item) => ({ ...favoriteItem(item.base_id), viewed_at: item.viewed_at }))
      .filter((item) => item.base_id)
    return mockResponse({ items })
  }

  if (requestMethod === "DELETE" && pathname === "/miniapp/me/history") {
    writeStore({ ...store, history: [] })
    return mockResponse({ ok: true })
  }

  if (requestMethod === "GET" && pathname === "/miniapp/me/appointments") {
    return mockResponse({ items: store.appointments.map(appointmentView) })
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

  notFound(path)
}

export async function apiRequest(path, { method = "GET", body } = {}) {
  if (useMockApi()) {
    return mockRequest(path, { method, body })
  }

  const headers = { "Content-Type": "application/json" }
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) headers.Authorization = `Bearer ${token}`

  let res
  try {
    res = await fetch(`${baseURL()}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined
    })
  } catch {
    throw new Error("无法连接服务器，请确认后端已启动")
  }

  if (res.status === 401) {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    throw new Error("登录已过期，请刷新页面重试")
  }

  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.detail || `请求失败（${res.status}）`)
  }
  return data
}

// 确保登录：优先用本地 token，失效则用演示账号重新登录，账号不存在时自动注册
export async function ensureLogin() {
  const current = localStorage.getItem(TOKEN_KEY)
  if (current) return current

  const credentials = { username: DEMO_USERNAME, password: DEMO_PASSWORD }
  let res
  try {
    res = await apiRequest("/auth/login", { method: "POST", body: credentials })
  } catch {
    try {
      await apiRequest("/auth/register", {
        method: "POST",
        body: { ...credentials, real_name: "森林爱好者" }
      })
    } catch {
      // 注册失败（例如已存在）时继续尝试登录
    }
    res = await apiRequest("/auth/login", { method: "POST", body: credentials })
  }

  localStorage.setItem(TOKEN_KEY, res.access_token)
  if (res.user) {
    localStorage.setItem(USER_KEY, JSON.stringify(res.user))
  }
  return res.access_token
}

export function currentUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || "null")
  } catch {
    return null
  }
}

function assistantBaseURL() {
  return ""
}

export async function cozeChat(query, { conversationId } = {}) {
  const res = await fetch(`${assistantBaseURL()}/api/coze/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      conversation_id: conversationId || undefined
    })
  })

  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.error || `智能助手请求失败（${res.status}）`)
  }
  return data
}
