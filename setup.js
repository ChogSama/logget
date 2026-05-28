/**
 * Cross-platform helper (Windows / macOS / Linux).
 *
 * Usage:
 * node setup.js               → create .env + venv + pip install + npm install
 * node setup.js <bin> [args]  → run a binary inside venv, e.g. node setup.js fastapi dev server/main.py
 */

import { execSync } from 'child_process'
import { existsSync, copyFileSync } from 'fs'
import { join } from 'path'

const binDir = process.platform === 'win32' ? 'Scripts' : 'bin'
const venvBin = (name) => join('venv', binDir, name)
const [,, cmd, ...args] = process.argv

if (!cmd) {
  if (!existsSync('.env') && existsSync('.env.example')) {
    copyFileSync('.env.example', '.env')
  }
  if (!existsSync('venv')) execSync('python -m venv venv', { stdio: 'inherit' })
  execSync(`${venvBin('pip')} install -r requirements.txt`, { stdio: 'inherit' })
  execSync('npm install', { stdio: 'inherit' })
} else {
  execSync(`${venvBin(cmd)} ${args.join(' ')}`, { stdio: 'inherit' })
}