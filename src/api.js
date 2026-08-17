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

export async function apiRequest(path, { method = "GET", body } = {}) {
  const url = new URL(path, "http://local.mock")
  const pathname = url.pathname
  const store = getStore()

  if (pathname === "/auth/login" || pathname === "/auth/register") {
    return {
      access_token: "mock-token",
      token_type: "bearer",
      user: mockUser(body?.username)
    }
  }

  if (pathname === "/bases" && method === "GET") {
    const page = Number(url.searchParams.get("page") || 1)
    const pageSize = Number(url.searchParams.get("page_size") || mockBases.length)
    const sorted = [...mockBases].sort((a, b) => b.view_count - a.view_count)
    const start = (page - 1) * pageSize
    return {
      items: sorted.slice(start, start + pageSize).map(publicBase),
      total: sorted.length,
      page,
      page_size: pageSize
    }
  }

  const baseMatch = pathname.match(/^\/bases\/(\d+)$/)
  if (baseMatch && method === "GET") {
    const base = mockBases.find((item) => item.id === Number(baseMatch[1]))
    if (!base) notFound(path)
    return base
  }

  if (pathname === "/miniapp/me/favorites" && method === "GET") {
    return { items: store.favorites.map(favoriteItem).filter(Boolean) }
  }

  const favoriteMatch = pathname.match(/^\/miniapp\/me\/favorites\/(\d+)$/)
  if (favoriteMatch) {
    const baseId = Number(favoriteMatch[1])
    if (method === "PUT" && !store.favorites.includes(baseId)) {
      store.favorites.push(baseId)
    }
    if (method === "DELETE") {
      store.favorites = store.favorites.filter((id) => id !== baseId)
    }
    writeStore(store)
    return { ok: true }
  }

  if (pathname === "/miniapp/me/history" && method === "GET") {
    return { items: store.history }
  }

  if (pathname === "/miniapp/me/history" && method === "DELETE") {
    store.history = []
    writeStore(store)
    return { ok: true }
  }

  const viewMatch = pathname.match(/^\/miniapp\/bases\/(\d+)\/view$/)
  if (viewMatch && method === "POST") {
    const item = favoriteItem(Number(viewMatch[1]))
    if (item) {
      store.history = [
        { ...item, viewed_at: new Date().toISOString() },
        ...store.history.filter((historyItem) => historyItem.base_id !== item.base_id)
      ].slice(0, 50)
      writeStore(store)
    }
    return { ok: true }
  }

  if (pathname === "/miniapp/me/appointments" && method === "GET") {
    return { items: store.appointments.map(appointmentView) }
  }

  if (pathname === "/miniapp/me/appointments" && method === "POST") {
    const item = {
      id: Date.now(),
      status: "pending",
      created_at: new Date().toISOString(),
      ...body
    }
    store.appointments.unshift(item)
    writeStore(store)
    return appointmentView(item)
  }

  const cancelMatch = pathname.match(/^\/miniapp\/me\/appointments\/(\d+)\/cancel$/)
  if (cancelMatch && method === "POST") {
    const item = store.appointments.find((appointment) => appointment.id === Number(cancelMatch[1]))
    if (!item) notFound(path)
    item.status = "cancelled"
    writeStore(store)
    return appointmentView(item)
  }

  if (pathname === "/miniapp/me/stats" && method === "GET") {
    return {
      favorites: store.favorites.length,
      appointments: store.appointments.filter((item) => item.status !== "cancelled").length,
      history: store.history.length
    }
  }

  notFound(path)
}

export async function ensureLogin() {
  const current = localStorage.getItem(TOKEN_KEY)
  if (current) return current

  const res = await apiRequest("/auth/login", {
    method: "POST",
    body: { username: DEMO_USERNAME, password: DEMO_PASSWORD }
  })

  localStorage.setItem(TOKEN_KEY, res.access_token)
  localStorage.setItem(USER_KEY, JSON.stringify(res.user || mockUser()))
  return res.access_token
}

export function currentUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || "null")
  } catch {
    return null
  }
}
