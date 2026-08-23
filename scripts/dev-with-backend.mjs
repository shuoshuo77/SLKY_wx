import { spawn } from "node:child_process"
import { resolve } from "node:path"

const node = process.execPath
const viteBin = resolve("node_modules", "vite", "bin", "vite.js")
const backendScript = resolve("server", "backend", "start.ps1")
const backendUrl = process.env.SLKY_BACKEND_URL || "http://127.0.0.1:8001"
const healthUrl = `${backendUrl}/health/ready`
const viteArgs = [viteBin, ...process.argv.slice(2)]

let backendChild
let viteChild
let shuttingDown = false

function sleep(milliseconds) {
  return new Promise((resolvePromise) => setTimeout(resolvePromise, milliseconds))
}

async function backendIsReady() {
  try {
    const response = await fetch(healthUrl, {
      signal: AbortSignal.timeout(1500)
    })
    return response.ok
  } catch {
    return false
  }
}

function startProcess(name, command, args) {
  const child = spawn(command, args, {
    cwd: process.cwd(),
    env: process.env,
    stdio: "inherit",
    shell: false,
    windowsHide: true
  })

  child.on("error", (error) => {
    if (!shuttingDown) {
      console.error(`${name} could not be started: ${error.message}`)
      shutdown(1)
    }
  })

  return child
}

async function waitForBackend(child) {
  let exitInfo
  child.once("exit", (code, signal) => {
    exitInfo = { code, signal }
  })

  const deadline = Date.now() + 30000
  while (Date.now() < deadline) {
    if (await backendIsReady()) return

    if (exitInfo) {
      const reason = exitInfo.signal
        ? `signal ${exitInfo.signal}`
        : `code ${exitInfo.code}`
      throw new Error(`backend exited before becoming ready (${reason})`)
    }

    await sleep(500)
  }

  throw new Error(`backend did not become ready within 30 seconds: ${healthUrl}`)
}

function terminateChild(child) {
  if (!child?.pid || child.killed) return

  if (process.platform === "win32") {
    spawn("taskkill.exe", ["/pid", String(child.pid), "/t", "/f"], {
      stdio: "ignore",
      windowsHide: true
    }).unref()
    return
  }

  child.kill("SIGTERM")
}

function shutdown(code = 0) {
  if (shuttingDown) return
  shuttingDown = true
  terminateChild(viteChild)
  terminateChild(backendChild)
  process.exitCode = code
}

process.on("SIGINT", () => shutdown(0))
process.on("SIGTERM", () => shutdown(0))

async function main() {
  console.log(`[startup] Checking backend readiness: ${healthUrl}`)

  if (await backendIsReady()) {
    console.log("[startup] Reusing the already running local backend.")
  } else {
    console.log("[startup] Starting local backend…")
    backendChild = startProcess("backend", "powershell.exe", [
      "-NoProfile",
      "-ExecutionPolicy",
      "Bypass",
      "-File",
      backendScript
    ])
    await waitForBackend(backendChild)
    console.log("[startup] Backend is ready.")
  }

  viteChild = startProcess("vite", node, viteArgs)
  viteChild.on("exit", (code, signal) => {
    if (shuttingDown) return
    if (signal) {
      console.error(`vite stopped with signal ${signal}`)
      shutdown(1)
      return
    }
    shutdown(code || 0)
  })

  if (backendChild) {
    backendChild.on("exit", (code, signal) => {
      if (shuttingDown) return
      const reason = signal ? `signal ${signal}` : `code ${code}`
      console.error(`backend stopped unexpectedly (${reason})`)
      shutdown(1)
    })
  }
}

main().catch((error) => {
  console.error(`[startup] ${error.message}`)
  shutdown(1)
})
