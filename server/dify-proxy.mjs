import { createServer } from "node:http"
import { readFileSync, existsSync } from "node:fs"
import { resolve } from "node:path"

loadEnvFile()

const PORT = Number(process.env.PORT || 3001)
const DIFY_API_URL = (process.env.DIFY_API_URL || "http://localhost/v1").replace(/\/+$/, "")
const DIFY_API_KEY = process.env.DIFY_API_KEY || ""
const COZE_API_URL = (process.env.COZE_API_URL || "https://api.coze.cn/v3/chat").replace(/\/+$/, "")
const COZE_API_TOKEN = process.env.COZE_API_TOKEN || ""
const COZE_BOT_ID = process.env.COZE_BOT_ID || "7661162618937622591"
const COZE_USER_ID = process.env.COZE_USER_ID || "senyang-web-user"
const COZE_POLL_INTERVAL_MS = Number(process.env.COZE_POLL_INTERVAL_MS || 400)
const COZE_MAX_POLLS = Number(process.env.COZE_MAX_POLLS || 75)
const PROJECT_CONTEXT = [
  "你正在为“森氧康养小程序”网页项目提供智能助手服务。",
  "项目用于展示森林康养基地，支持首页推荐、基地列表、基地详情、地图找基地、环境监测、收藏、浏览记录和预约参访。",
  "当前内置示例基地包括：青城山康养基地、庐山森林康养基地、莫干山康养度假基地、武夷山森林康养基地、长白山温泉康养基地。",
  "用户问“这个项目”时，默认指森氧康养小程序。回答要围绕项目功能和康养基地，简洁、直接、适合移动端阅读。"
].join("\n")

function loadEnvFile() {
  const envPath = resolve(process.cwd(), ".env")
  if (!existsSync(envPath)) return

  const content = readFileSync(envPath, "utf8")
  for (const line of content.split(/\r?\n/)) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith("#")) continue
    const eqIndex = trimmed.indexOf("=")
    if (eqIndex === -1) continue
    const key = trimmed.slice(0, eqIndex).trim()
    const value = trimmed.slice(eqIndex + 1).trim().replace(/^["']|["']$/g, "")
    if (!process.env[key]) process.env[key] = value
  }
}

function sendJson(res, statusCode, data) {
  res.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,Authorization"
  })
  res.end(JSON.stringify(data))
}

async function readJson(req) {
  const chunks = []
  for await (const chunk of req) chunks.push(chunk)
  const text = Buffer.concat(chunks).toString("utf8")
  return text ? JSON.parse(text) : {}
}

async function handleDifyChat(req, res) {
  if (!DIFY_API_KEY) {
    sendJson(res, 500, { error: "缺少 DIFY_API_KEY，请在 .env 中配置 Dify API 密钥。" })
    return
  }

  const body = await readJson(req)
  const query = String(body.query || "").trim()
  if (!query) {
    sendJson(res, 400, { error: "query 不能为空。" })
    return
  }

  const difyRes = await fetch(`${DIFY_API_URL}/chat-messages`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${DIFY_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      inputs: body.inputs || {},
      query,
      response_mode: "blocking",
      conversation_id: body.conversation_id || undefined,
      user: body.user || "senyang-web-user"
    })
  })

  const data = await difyRes.json().catch(() => ({}))
  if (!difyRes.ok) {
    sendJson(res, difyRes.status, {
      error: data.message || data.error || `Dify 请求失败（${difyRes.status}）`,
      detail: data
    })
    return
  }

  sendJson(res, 200, {
    answer: data.answer || "",
    conversation_id: data.conversation_id || body.conversation_id || "",
    raw: data
  })
}

function cozeBaseURL() {
  return COZE_API_URL.endsWith("/v3/chat") ? COZE_API_URL.slice(0, -8) : COZE_API_URL.replace(/\/v3$/, "")
}

async function readCozeJson(url, options) {
  const cozeRes = await fetch(url, {
    ...options,
    headers: {
      "Authorization": `Bearer ${COZE_API_TOKEN}`,
      "Content-Type": "application/json",
      ...(options?.headers || {})
    }
  })
  const data = await cozeRes.json().catch(() => ({}))
  if (!cozeRes.ok || (data.code && data.code !== 0)) {
    const message = data.msg || data.message || data.error || `Coze request failed (${cozeRes.status})`
    const err = new Error(message)
    err.statusCode = cozeRes.status || 500
    err.detail = data
    throw err
  }
  return data
}

function answerFromMessages(data) {
  const messages = Array.isArray(data.data) ? data.data : []
  const answer = messages.find((item) => item.role === "assistant" && item.type === "answer")
    || messages.find((item) => item.role === "assistant")
  return answer?.content || ""
}

function normalizeQuestion(query) {
  return query.replace(/\s+/g, "").replace(/[？?。！!，,、]/g, "")
}

function localQuickAnswer(query) {
  const normalized = normalizeQuestion(query)

  if (
    normalized.includes("项目主要是做什么") ||
    normalized.includes("小程序是做什么") ||
    normalized.includes("功能介绍")
  ) {
    return "森氧康养小程序主要用于展示和查询森林康养基地，支持首页推荐、基地列表、基地详情、地图找基地、环境监测、收藏、浏览记录和预约参访。"
  }

  if (
    normalized.includes("有哪些康养基地") ||
    normalized.includes("有哪些基地") ||
    normalized.includes("基地推荐")
  ) {
    return "当前项目内置推荐基地包括：青城山康养基地、庐山森林康养基地、莫干山康养度假基地、武夷山森林康养基地、长白山温泉康养基地。"
  }

  if (normalized.includes("预约") || normalized.includes("参访")) {
    return "可以预约参访。进入基地详情页后，点击“预约参访”，选择日期、时间段、人数并填写联系人信息即可提交预约。"
  }

  if (normalized.includes("避暑") || normalized.includes("夏季")) {
    return "适合夏季避暑的基地可以优先看青城山康养基地和庐山森林康养基地，它们气温较舒适，森林资源丰富，适合休闲康养和避暑出行。"
  }

  return ""
}

async function handleCozeChat(req, res) {
  if (!COZE_API_TOKEN) {
    sendJson(res, 500, { error: "缺少 COZE_API_TOKEN，请在 .env 中配置 Coze 个人访问令牌。" })
    return
  }

  const body = await readJson(req)
  const query = String(body.query || "").trim()
  if (!query) {
    sendJson(res, 400, { error: "query 不能为空。" })
    return
  }

  const quickAnswer = localQuickAnswer(query)
  if (quickAnswer) {
    sendJson(res, 200, {
      answer: quickAnswer,
      conversation_id: body.conversation_id || "",
      source: "local_quick_answer"
    })
    return
  }

  const createData = await readCozeJson(COZE_API_URL, {
    method: "POST",
    body: JSON.stringify({
      bot_id: body.bot_id || COZE_BOT_ID,
      user_id: body.user || COZE_USER_ID,
      stream: false,
      auto_save_history: true,
      conversation_id: body.conversation_id || undefined,
      additional_messages: [
        {
          role: "user",
          content: `${PROJECT_CONTEXT}\n\n用户问题：${query}`,
          content_type: "text"
        }
      ]
    })
  })

  const chat = createData.data || createData
  const chatId = chat.id || chat.chat_id
  const conversationId = chat.conversation_id || body.conversation_id || ""
  const base = cozeBaseURL()

  let status = chat.status || ""
  for (let i = 0; chatId && conversationId && i < COZE_MAX_POLLS && !["completed", "failed", "requires_action"].includes(status); i += 1) {
    await new Promise((resolveTimeout) => setTimeout(resolveTimeout, COZE_POLL_INTERVAL_MS))
    const retrieveUrl = `${base}/v3/chat/retrieve?conversation_id=${encodeURIComponent(conversationId)}&chat_id=${encodeURIComponent(chatId)}`
    const retrieveData = await readCozeJson(retrieveUrl, { method: "GET" })
    status = retrieveData.data?.status || retrieveData.status || status
    if (status === "failed") {
      const lastError = retrieveData.data?.last_error
      throw new Error(lastError?.msg || "Coze 智能体执行失败。")
    }
  }

  const messageUrl = `${base}/v3/chat/message/list?conversation_id=${encodeURIComponent(conversationId)}&chat_id=${encodeURIComponent(chatId)}`
  const messageData = await readCozeJson(messageUrl, { method: "GET" })
  sendJson(res, 200, {
    answer: answerFromMessages(messageData),
    conversation_id: conversationId,
    chat_id: chatId,
    raw: messageData
  })
}

const server = createServer(async (req, res) => {
  if (req.method === "OPTIONS") {
    sendJson(res, 204, {})
    return
  }

  try {
    const url = new URL(req.url, `http://${req.headers.host}`)
    if (req.method === "GET" && url.pathname === "/api/health") {
      sendJson(res, 200, { ok: true })
      return
    }

    if (req.method === "POST" && url.pathname === "/api/dify/chat") {
      await handleDifyChat(req, res)
      return
    }

    if (req.method === "POST" && url.pathname === "/api/coze/chat") {
      await handleCozeChat(req, res)
      return
    }

    sendJson(res, 404, { error: "接口不存在。" })
  } catch (err) {
    sendJson(res, 500, { error: err.message || "服务器内部错误。" })
  }
})

server.listen(PORT, () => {
  console.log(`Dify proxy server running at http://127.0.0.1:${PORT}`)
  console.log(`Dify API target: ${DIFY_API_URL}`)
})
