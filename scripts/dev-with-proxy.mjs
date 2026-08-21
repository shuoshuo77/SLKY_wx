import { spawn } from "node:child_process"
import { resolve } from "node:path"

const children = []
const node = process.execPath
const viteBin = resolve("node_modules", "vite", "bin", "vite.js")

function run(name, command, args) {
  const child = spawn(command, args, {
    cwd: process.cwd(),
    env: process.env,
    stdio: "inherit",
    shell: false
  })

  children.push(child)

  child.on("exit", (code, signal) => {
    if (signal) return
    if (code && code !== 0) {
      console.error(`${name} exited with code ${code}`)
      shutdown(code)
    }
  })
}

function shutdown(code = 0) {
  for (const child of children) {
    if (!child.killed) child.kill()
  }
  process.exit(code)
}

process.on("SIGINT", () => shutdown(0))
process.on("SIGTERM", () => shutdown(0))

run("assistant proxy", node, ["server/dify-proxy.mjs"])
run("vite", node, [viteBin])
