// 森氧康养小程序 API 客户端
// 默认走 Vite 代理（/api -> 后端），需要直连时可在浏览器控制台设置：
//   localStorage.setItem("syk_api_base", "http://127.0.0.1:8000/api")

const TOKEN_KEY = "syk_token"
const USER_KEY = "syk_user"
const STORE_KEY = "syk_mock_store"
export const AUTH_REQUIRED = "AUTH_REQUIRED"

// 本地 Mock 基地数据：在没有后端或开启 VITE_USE_MOCK_API=true 时用于页面演示。
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

// 从 localStorage 读取 Mock 模式下的用户收藏、浏览记录和预约记录。
function readStore() {
  try {
    return JSON.parse(localStorage.getItem(STORE_KEY) || "{}")
  } catch {
    return {}
  }
}

// 写入 Mock 模式下的本地状态，模拟后端数据持久化。
function writeStore(store) {
  localStorage.setItem(STORE_KEY, JSON.stringify(store))
}

// 统一补齐 Mock 状态结构，避免某个字段不存在时页面报错。
function getStore() {
  const store = readStore()
  return {
    favorites: store.favorites || [],
    history: store.history || [],
    appointments: store.appointments || []
  }
}

// 列表接口只返回公开字段，去掉详情页才需要的资源、经营、资质等嵌套数据。
function publicBase(base) {
  const { resources, business, qualifications, ...item } = base
  return item
}

// 把省、市、区拼成人类可读的区域文案。
function areaText(base) {
  return [base.province, base.city, base.district].filter(Boolean).join(" · ")
}

// 根据收藏的 baseId 生成“我的收藏”页面需要的基地卡片数据。
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

// 把 Mock 预约记录补充为前端页面展示所需的字段。
function appointmentView(item) {
  const base = mockBases.find((baseItem) => baseItem.id === Number(item.base_id))
  return {
    ...item,
    base_name: base?.name || "康养基地",
    base_image: base?.primary_image || "",
    status_label: item.status === "cancelled" ? "已取消" : "待确认"
  }
}

// Mock 登录成功后返回的用户信息。
function mockUser(username = "mock-user") {
  return { id: 1, username, real_name: "森林爱好者" }
}

// Mock 模式下如果访问了未实现的接口，直接抛出明确错误。
function notFound(path) {
  throw new Error(`本地模拟接口未实现：${path}`)
}

// 读取 API 基础地址。优先使用 Vite 环境变量，其次使用浏览器 localStorage 覆盖值。
function configuredBaseURL() {
  const envValue = import.meta.env.VITE_API_BASE_URL
  const browserValue = typeof localStorage === "undefined" ? "" : localStorage.getItem("syk_api_base")
  return (envValue || browserValue || "").replace(/\/+$/, "")
}

// 默认使用 Vite 代理的 /api；直连后端时可以配置完整地址。
function baseURL() {
  return configuredBaseURL() || "/api"
}

// 是否启用前端 Mock 接口。配置为 mock 或 VITE_USE_MOCK_API=true 时启用。
function useMockApi() {
  const configured = configuredBaseURL()
  return configured === "mock" || import.meta.env.VITE_USE_MOCK_API === "true"
}

// 处理后端返回的资源路径：相对路径转为当前 API 服务下的可访问地址。
export function resolveApiAsset(url) {
  if (!url || url.startsWith("/assets/") || /^(?:https?:|data:)/.test(url)) return url

  const path = url.startsWith("/") ? url : `/${url}`
  const configured = configuredBaseURL()
  if (/^https?:\/\//.test(configured)) {
    return `${configured.replace(/\/api\/?$/, "")}${path}`
  }
  return path
}

// 深拷贝 Mock 响应，避免页面直接修改 mockBases 原始数据。
function mockResponse(data) {
  return Promise.resolve(JSON.parse(JSON.stringify(data)))
}

// 前端本地模拟接口：接口路径尽量和真实后端保持一致，便于无后端演示。
async function mockRequest(path, { method = "GET", body } = {}) {
  const url = new URL(path, "http://mock.local")
  const pathname = url.pathname
  const requestMethod = method.toUpperCase()
  const store = getStore()

  // 基地列表：模拟分页和按浏览量排序。
  if (requestMethod === "GET" && (pathname === "/bases" || pathname === "/bases/")) {
    const page = Number(url.searchParams.get("page") || 1)
    const pageSize = Number(url.searchParams.get("page_size") || 20)
    const items = mockBases.map(publicBase).sort((a, b) => (b.view_count || 0) - (a.view_count || 0))
    const start = (page - 1) * pageSize
    return mockResponse({ items: items.slice(start, start + pageSize), total: items.length, page, page_size: pageSize })
  }

  // 小程序首页聚合数据：轮播图、热门基地、功能入口和统计数据。
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

  // 地图页面基地标记：为 Mock 数据补充经纬度，模拟地图点位。
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

  // 推荐列表：Mock 模式固定返回热门推荐。
  if (requestMethod === "GET" && pathname === "/miniapp/recommendations") {
    const limit = Number(url.searchParams.get("limit") || 10)
    return mockResponse({ items: mockBases.slice(0, limit).map((base) => ({ ...publicBase(base), tags: base.tags, reason: "热门推荐", distance_km: null })), recommendation_mode: "popular", location_used: false, radius_km: null })
  }

  // 省份筛选项：按 Mock 基地数据统计各省数量。
  if (requestMethod === "GET" && pathname === "/bases/provinces") {
    const counts = new Map()
    mockBases.forEach((base) => counts.set(base.province, (counts.get(base.province) || 0) + 1))
    return mockResponse([...counts.entries()].map(([province, count]) => ({ province, count })))
  }

  // 基地详情：根据 URL 里的基地 ID 查找完整 Mock 数据。
  const baseMatch = pathname.match(/^\/bases\/(\d+)$/)
  if (requestMethod === "GET" && baseMatch) {
    const base = mockBases.find((item) => item.id === Number(baseMatch[1]))
    if (!base) notFound(path)
    return mockResponse(base)
  }

  // 登录和注册：Mock 模式不校验密码，只返回本地 token 和用户信息。
  if (requestMethod === "POST" && pathname === "/auth/login") {
    return mockResponse({ access_token: "mock-token", token_type: "bearer", user: mockUser(body?.username) })
  }

  if (requestMethod === "POST" && pathname === "/auth/register") {
    return mockResponse({ access_token: "mock-token", token_type: "bearer", user: mockUser(body?.username) })
  }

  if (requestMethod === "GET" && pathname === "/users/me") {
    return mockResponse(currentUser() || mockUser())
  }

  // 收藏列表：从 localStorage 中读取收藏 ID，再转换成页面展示数据。
  if (requestMethod === "GET" && pathname === "/miniapp/me/favorites") {
    return mockResponse({ items: store.favorites.map(favoriteItem).filter(Boolean) })
  }

  // 收藏/取消收藏：用 PUT 和 DELETE 分别模拟后端的新增、删除收藏。
  const favoriteMatch = pathname.match(/^\/miniapp\/me\/favorites\/(\d+)$/)
  if (favoriteMatch && (requestMethod === "PUT" || requestMethod === "DELETE")) {
    const baseId = Number(favoriteMatch[1])
    const favorites = new Set(store.favorites)
    if (requestMethod === "PUT") favorites.add(baseId)
    else favorites.delete(baseId)
    writeStore({ ...store, favorites: [...favorites] })
    return mockResponse({ favorited: requestMethod === "PUT" })
  }

  // 浏览记录：每次进入详情页时记录，最多保留最近 50 条。
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

  // 我的浏览记录：把本地记录转换成页面可展示的基地信息。
  if (requestMethod === "GET" && pathname === "/miniapp/me/history") {
    const items = store.history
      .map((item) => ({ ...favoriteItem(item.base_id), viewed_at: item.viewed_at }))
      .filter((item) => item.base_id)
    return mockResponse({ items })
  }

  // 清空浏览记录。
  if (requestMethod === "DELETE" && pathname === "/miniapp/me/history") {
    writeStore({ ...store, history: [] })
    return mockResponse({ cleared: store.history.length })
  }

  // 我的预约列表。
  if (requestMethod === "GET" && pathname === "/miniapp/me/appointments") {
    return mockResponse({ items: store.appointments.map(appointmentView), total: store.appointments.length, page: 1, page_size: 20 })
  }

  // 创建预约：生成本地 ID，状态默认为待确认。
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

  // 取消预约：只更新本地预约状态，不删除记录。
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

  // 个人中心统计：收藏数、有效预约数、浏览记录数。
  if (requestMethod === "GET" && pathname === "/miniapp/me/stats") {
    return mockResponse({
      favorites: store.favorites.length,
      appointments: store.appointments.filter((item) => item.status !== "cancelled").length,
      history: store.history.length
    })
  }

  // 智能体 Mock 回复：真实扣子/DeepSeek 调用在后端完成，前端 Mock 只提示连接后端。
  if (requestMethod === "POST" && pathname === "/miniapp/chat") {
    return mockResponse({
      session_id: body?.session_id || "mock-session",
      reply: "这是离线演示回复。请连接项目后端以使用智能咨询。",
      provider: "deepseek",
      suggestions: [],
      disclaimer: "健康建议仅供参考，不替代医生诊断或治疗。"
    })
  }

  // 意见反馈/需求提交 Mock。
  if (requestMethod === "POST" && pathname === "/demands") {
    return mockResponse({ message: "需求已提交", id: Date.now() })
  }

  notFound(path)
}

// 统一解析后端错误响应，兼容 FastAPI 的字符串 detail 和校验错误数组。
function responseErrorMessage(data, status) {
  if (typeof data?.detail === "string") return data.detail
  if (Array.isArray(data?.detail)) {
    return data.detail.map((item) => item.msg || item.message).filter(Boolean).join("；") || `请求失败（${status}）`
  }

  return data?.message || `请求失败（${status}）`
}

// 项目统一请求入口：负责切换 Mock/真实接口、拼接 baseURL、附加 token、处理错误。
export async function apiRequest(path, { method = "GET", body, headers: customHeaders } = {}) {
  if (useMockApi()) {
    return mockRequest(path, { method, body })
  }

  // 默认按 JSON 请求；调用方可以通过 customHeaders 覆盖或追加请求头。
  const headers = { "Content-Type": "application/json", ...customHeaders }
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) headers.Authorization = `Bearer ${token}`

  const requestUrl = `${baseURL()}${path}`
  let res
  try {
    // body 为 undefined 时不传请求体，避免 GET 请求携带无意义 body。
    res = await fetch(requestUrl, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined
    })
  } catch (err) {
    throw new Error(`无法连接项目后端：${requestUrl}（${err.message || "网络请求失败"}）`)
  }

  // 登录过期时清理本地登录态，并用 AUTH_REQUIRED 让页面弹出登录框。
  if (res.status === 401) {
    clearSession()
    const error = new Error("登录已过期，请重新登录")
    error.code = AUTH_REQUIRED
    throw error
  }

  // 后端可能没有响应体，这里用空对象兜底。
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const error = new Error(responseErrorMessage(data, res.status))
    error.status = res.status
    throw error
  }
  return data
}

// 保存登录接口返回的 token 和用户信息。
function storeSession(data) {
  localStorage.setItem(TOKEN_KEY, data.access_token)
  localStorage.setItem(USER_KEY, JSON.stringify(data.user || {}))
  return data.access_token
}

// 清除登录态，用于退出登录或 401 过期处理。
export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

// 判断当前浏览器是否已有登录 token。
export function isAuthenticated() {
  return Boolean(localStorage.getItem(TOKEN_KEY))
}

// 登录成功后保存 token，后续 apiRequest 会自动携带 Authorization。
export async function login(credentials) {
  const data = await apiRequest("/auth/login", { method: "POST", body: credentials })
  storeSession(data)
  return data
}

// 注册只提交资料，不自动登录。
export async function register(profile) {
  return apiRequest("/auth/register", { method: "POST", body: profile })
}

// 重新拉取当前用户信息，并同步到 localStorage。
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

// 读取当前本地缓存的用户信息。
export function currentUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || "null")
  } catch {
    return null
  }
}

// 智能体对话接口：前端把当前问题、会话 ID 和最近历史消息发给后端。
// 后端再根据配置转发到扣子 Coze 或 DeepSeek，并返回模型回复。
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
