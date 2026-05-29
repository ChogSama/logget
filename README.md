# Project Name

_**logget**_: React (Vite) + FastAPI.

## Prerequisites

- Node.js
- Python 3.x

## Setup

```bash
node setup.js     # install uv (if missing) + uv sync + npm install
```

Hoặc sau khi đã có node_modules:

```bash
npm run setup
```

## Development

```bash
npm run dev          # run both frontend and backend
npm run dev:web      # frontend only  (http://localhost:5173)
npm run dev:server   # backend only   (http://localhost:8000)
```

## Build & Lint

```bash
npm run build:web    # build frontend
npm run lint:web     # lint frontend
npm run lint:server  # lint backend
```

## Dependencies

### Frontend (npm)

Luôn chạy từ **root**, không phải từ bên trong `web/`:

```bash
npm install <pkg>          # runtime dep  → "dependencies" trong package.json
npm install -D <pkg>       # dev dep      → "devDependencies" trong package.json
npm uninstall <pkg>
npm update <pkg>
```

### Backend (uv)

```bash
uv add <pkg>               # thêm vào pyproject.toml + cập nhật uv.lock
uv add --dev <pkg>         # dev dep (linting, testing, ...)
uv remove <pkg>
uv sync                    # đồng bộ .venv theo pyproject.toml + uv.lock
uv lock --upgrade-package <pkg>   # upgrade 1 package
```

> Không dùng `pip install` trực tiếp — sẽ không cập nhật `pyproject.toml` và `uv.lock`.

## Project Structure

```
├── server/              # FastAPI backend
│   └── main.py
├── web/                 # React + Vite frontend
│   ├── src/
│   └── vite.config.ts
├── package.json         # Node.js deps (npm)
├── pyproject.toml       # Python deps (uv)
└── setup.js             # cross-platform setup helper
```

## Contributing

### Issues

Tiêu đề ngắn gọn, mô tả rõ vấn đề hoặc tính năng. Gắn label phù hợp:

| Label | Ý nghĩa |
|---|---|
| `bug` | Lỗi cần sửa |
| `feature` | Tính năng mới |
| `docs` | Tài liệu |
| `refactor` | Cải thiện code, không thay đổi behavior |
| `chore` | Config, dependencies, build |

### Branches

Cú pháp: `<prefix>/<short-description>` — dùng kebab-case, ngắn gọn.

| Prefix | Dùng khi |
|---|---|
| `feat` | Thêm tính năng mới |
| `fix` | Sửa bug |
| `docs` | Chỉ thay đổi tài liệu |
| `refactor` | Refactor, không thêm tính năng hay sửa bug |
| `chore` | Config, dependencies, build |
| `hotfix` | Sửa lỗi khẩn trên production |

Ví dụ:
```
feat/user-authentication
fix/login-redirect-bug
docs/update-api-reference
chore/upgrade-vite
```

### Commits & Pull Requests

Theo chuẩn [Conventional Commits](https://www.conventionalcommits.org).

```
feat: add user authentication
fix: correct validation logic
refactor: simplify token parsing
```

**Quy định bổ sung đối với Pull Request:**
* Merge Pull Requests theo tùy chọn **Squash and Merge**.
* Có thể viết PR tittle chi tiết hơn theo cú pháp: `<type>(<scope>): <description>`.
* Nếu braches chưa hoàn thiện hoặc chưa sẵn sàng nhưng cần review, có thể tạo PR dưới dạng **Draft Pull Request**.

---

Xem thêm: [NOTES.md](./NOTES.md)