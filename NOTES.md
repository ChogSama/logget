# Architecture Notes

> Mô tả cách setup hoạt động — dành cho contributor và AI assistant để tránh hoặc sửa lỗi môi trường khi code.

## Monorepo structure

Dự án dùng **single root `package.json`** thay vì tách `web/package.json` riêng:

- `node_modules/` nằm ở **root**, không phải trong `web/`
- `package.json`, `setup.js`, `pyproject.toml`, `.env` đều ở **root**
- `.venv/` nằm ở **root**

## Tại sao `cd web && vite` hoạt động

Khi chạy `npm run <script>`, npm tự động thêm `<root>/node_modules/.bin` vào PATH. Nên dù đang ở trong `web/`, lệnh `vite` vẫn tìm được binary từ root `node_modules`.

## TypeScript resolution

Root `tsconfig.json` dùng project references trỏ vào `web/tsconfig.json`, rồi chain tiếp sang `web/tsconfig.app.json` và `web/tsconfig.node.json`. TypeScript tự walk up directory tree để tìm `node_modules` — nên dù config nằm trong `web/`, nó vẫn resolve được packages từ root.

`web/tsconfig.app.json` có:
```json
"tsBuildInfoFile": "../node_modules/.tmp/tsconfig.app.tsbuildinfo"
```
Trỏ thẳng vào root `node_modules` — tường minh, tránh nhầm lẫn.

## Environment variables

`.env` đặt ở root. `web/vite.config.ts` dùng:
```ts
envDir: '..',
loadEnv(mode, '..', 'VITE_')
```
Vì Vite chạy từ thư mục `web/` (do `cd web && vite`), cần `..` để đọc `.env` từ root.

- `loadEnv(...)` — load vào biến dùng trong `vite.config.ts`
- `envDir: '..'` — để `import.meta.env.VITE_*` trong React code cũng đọc từ root

## Dev proxy

Frontend gọi `/api/*`, Vite tự proxy sang FastAPI ở `http://localhost:8000` — không bị CORS trong dev, không hardcode URL trong code React.

## Python backend

`setup.js` dùng [uv](https://docs.astral.sh/uv/) để quản lý Python environment:

- `uv sync` đọc `pyproject.toml`, tạo `.venv/` tại root và cài đặt dependencies.
- Không cần activate `.venv/` thủ công — `dev:server` gọi `uv run` để chạy FastAPI trực tiếp trong context của `.venv/`, hoạt động đồng nhất trên Windows/macOS/Linux.

## Những điều KHÔNG làm

- Không tạo `package.json` riêng trong `web/`
- Không chạy `npm install` từ bên trong `web/`
- Không đặt `.env` trong `web/`

---

## Tách thành 2 repos (kế hoạch tương lai)

Nếu sau này tách `web/` và `server/` thành 2 repo riêng, cần điều chỉnh như sau.

**Frontend repo** — `web/` content lên root:

- Xóa tiền tố `cd web &&` trong tất cả npm scripts.
- `vite.config.ts`: đổi `envDir: '..'` → `envDir: '.'` và `loadEnv(mode, '..', ...)` → `loadEnv(mode, '.', ...)` vì `.env` lúc này nằm cùng cấp với Vite.
- `tsconfig.app.json` và `tsconfig.node.json`: đổi `"tsBuildInfoFile": "../node_modules/.tmp/..."` → `"tsBuildInfoFile": "./node_modules/.tmp/..."`.
- Root `tsconfig.json` không cần `references` nữa, hoặc trỏ thẳng vào `tsconfig.app.json`.

**Backend repo** — `server/` và `pyproject.toml`:

- Giữ nguyên `pyproject.toml` và `setup.js` (phần uv), bỏ phần npm.
- `dev:server` script đổi thành `uv run fastapi dev server/main.py` trực tiếp.
- `.env` đặt ở root repo backend, FastAPI đọc qua `python-dotenv` hoặc tương đương.
- CORS cần được bật tường minh vì không còn Vite proxy — thêm `CORSMiddleware` vào FastAPI với origin của frontend.