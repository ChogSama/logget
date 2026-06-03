# Project Name

_**logget**_: React (Vite) + FastAPI.

## Prerequisites

- Node.js
- Python 3.x

## Setup

```bash
node setup.js     # install uv (if missing) + uv sync + npm install
```

Hoặc sau khi đã có **node_modules**:

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

```bash
npm install <pkg>          # runtime dep  → "dependencies" trong package.json
npm install -D <pkg>       # dev dep      → "devDependencies" trong package.json
npm uninstall <pkg>
npm update <pkg>
```

### Backend (uv)

Cài đặt **uv** (nếu chưa có):

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Các lệnh quản lý gói **uv** - tương tự như npm nhưng dành cho python.

```bash
uv add <pkg>               # thêm vào pyproject.toml + cập nhật uv.lock
uv add --dev <pkg>         # dev dep (linting, testing, ...)
uv remove <pkg>
uv sync                    # đồng bộ .venv theo pyproject.toml + uv.lock
uv lock --upgrade-package <pkg>   # upgrade 1 package
```

> Không dùng `pip install` trực tiếp — sẽ không cập nhật `pyproject.toml` và `uv.lock`.

## Database (alembic)

Alembic quản lý lịch sử thay đổi schema DB — tương tự git nhưng cho bảng/cột.

```bash
npm run db:migrate                        # áp dụng tất cả migration chưa chạy
npm run db:revision "tên_migration"       # tạo file migration mới từ thay đổi models
```

> Tên migration dùng **snake_case**, ví dụ: `add_user_table`, `add_lbs_score_to_daily_summary`.

Lệnh dùng trực tiếp (nếu cần chạy trực tiếp qua `uv`):

```bash
npx cross-env PYTHONPATH=. uv run alembic -c server/alembic.ini upgrade head       # migrate lên mới nhất
npx cross-env PYTHONPATH=. uv run alembic -c server/alembic.ini downgrade -1       # rollback 1 bước
npx cross-env PYTHONPATH=. uv run alembic -c server/alembic.ini revision --autogenerate -m "tên_migration" # Tạo file migration mới
npx cross-env PYTHONPATH=. uv run alembic -c server/alembic.ini history            # xem lịch sử migration
```

> Việc có tiền tố `cross-env PYTHONPATH=.`, đặc biệt thêm cả `npx`, được giải thích ở [NOTES.md](./NOTES.md#tiền-tố-cross-env-pythonpath) *(Mục Tiền tố cross-env PYTHONPATH=.)*.

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

Theo chuẩn [Conventional Commits](https://www.conventionalcommits.org): `<type>[optional scope]: <description>`.

```
feat: add user authentication
fix: correct validation logic
feat(lang): add Polish language
```

> Các quy tắc chuẩn dành cho bot, tools. Devs cũng áp dụng theo nhưng có thể chấp nhận sai sót nhỏ lẻ.

**Ghi chú bổ sung cho Pull Requests:**

* PR phải được merge theo tùy chọn **Squash and Merge**.

* PR title & Merge message theo cú pháp: `<type>[scope]: <description> (#id)`. <br/>
  * *Trong đó, `#id` là số định danh duy nhất của Issue/PR trên GitHub (hoặc mã Ticket).*
  * *Ví dụ:* `feat(auth): add user authentication (#42)`

* Nếu branches chưa hoàn thiện hoặc chưa sẵn sàng nhưng cần review, có thể tạo PR dưới dạng **Draft Pull Request**.

---

Xem thêm: [NOTES.md](./NOTES.md)