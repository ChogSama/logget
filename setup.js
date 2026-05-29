import { execSync } from 'node:child_process'
import { existsSync, copyFileSync } from 'node:fs'
import { join } from 'node:path'
import os from 'node:os'

const run = (cmd, env = process.env) =>
  execSync(cmd, { stdio: 'inherit', env })

const isWin = process.platform === 'win32'
const uvDir = join(os.homedir(), '.local', 'bin')
const uv = join(uvDir, isWin ? 'uv.exe' : 'uv')

if (!existsSync(uv)) {
  if (isWin) {
    run(
      'powershell -NoP -C "irm https://astral.sh/uv/install.ps1 | iex"',
      { ...process.env, UV_INSTALL_DIR: uvDir, UV_NO_MODIFY_PATH: '1' }
    )
  }
}

if (existsSync('.env.example') && !existsSync('.env')) {
  copyFileSync('.env.example', '.env')
}

if (existsSync('pyproject.toml')) run(`"${uv}" sync`)

if (existsSync('package.json')) {
  try { run('npm ci') } catch { run('npm install') }
}