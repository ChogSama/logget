import { execSync } from 'node:child_process'
import { existsSync, copyFileSync, rmSync } from 'node:fs'
import { join } from 'node:path'
import os from 'node:os'

const run = (cmd, env = process.env) =>
  execSync(cmd, { stdio: 'inherit', env })

const isWin = process.platform === 'win32'
const uvDir = join(os.homedir(), '.local', 'bin')
const uv = join(uvDir, isWin ? 'uv.exe' : 'uv')

if (!existsSync(uv)) {
  if (isWin) {
    run('powershell -NoP -ExecutionPolicy Bypass -C "irm https://astral.sh/uv/install.ps1 | iex"')
  } else {
    run('curl -LsSf https://astral.sh/uv/install.sh | sh')
  }
}

if (existsSync(uvDir)) {
  const separator = isWin ? ';' : ':'
  process.env.PATH = `${uvDir}${separator}${process.env.PATH}`
}

if (existsSync('.env.example') && !existsSync('.env')) {
  copyFileSync('.env.example', '.env')
}

if (existsSync('pyproject.toml')) run(`"${uv}" sync`)

if (existsSync('package.json')) {
  try {
    run('npm ci')
  } catch {
    try {
      if (existsSync('node_modules'))
        rmSync('node_modules', { recursive: true, force: true })
    } catch { /* ignore locked files */ }
    run('npm install')
  }
}

const shell = isWin ? 'powershell' : (process.env.SHELL || 'bash')
run(shell, process.env)