# Project Name

_**logget**_: React (Vite) + FastAPI.

## Prerequisites

- Node.js
- Python 3.x

## Setup

```bash
node setup.js     # create venv + pip install + npm install
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

## Project Structure

```
├── server/          # FastAPI backend
│   └── main.py
├── web/             # React frontend
│   └── src/
├── setup.js         # cross-platform setup helper
├── requirements.txt
└── package.json
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

### Commits

Theo chuẩn [Conventional Commits](https://www.conventionalcommits.org). Prefix của commit độc lập với branch — branch `feat/user-auth` có thể chứa các commit `fix:` hoặc `refactor:` trong quá trình làm:

```
feat: add user authentication
fix: correct validation logic
refactor: simplify token parsing
```
