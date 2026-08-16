// 森氧康养小程序 API 客户端
// 默认走 Vite 代理（/api -> 后端），需要直连时可在浏览器控制台设置：
//   localStorage.setItem("syk_api_base", "http://127.0.0.1:8001/api")

const TOKEN_KEY = "syk_token"
const USER_KEY = "syk_user"
const DEMO_USERNAME = "syk_demo"
const DEMO_PASSWORD = "syk123456"

function baseURL() {
  return (localStorage.getItem("syk_api_base") || "/api").replace(/\/+$/, "")
}

export async function apiRequest(path, { method = "GET", body } = {}) {
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
