# Architecture & Technical Notes

> Tài liệu hướng dẫn cấu hình và xử lý edge case dành cho Contributor và AI Assistant để đảm bảo tính đồng nhất hệ thống, tránh lỗi môi trường.

## Monorepo Structure

Dự án dùng **single root `package.json**` thay vì tách riêng cấu hình ở các thư mục con:

* `node_modules/`, `.venv/`, `package.json`, `pyproject.toml`, `.env` đều nằm tại **root**.
* Không tạo `package.json` hoặc chạy `npm install` bên trong `web/`.

## Frontend Operation (`web/`)

* **Vite execution:** Khi chạy `npm run <script>`, npm tự động thêm `<root>/node_modules/.bin` vào `PATH`. Do đó, cụm lệnh `cd web && vite` vẫn tìm và chạy đúng binary từ root `node_modules`.
* **TypeScript resolution:** Root `tsconfig.json` sử dụng project references trỏ vào `web/tsconfig.json`. Trình biên dịch tự động quét ngược cây thư mục để tìm `node_modules` ở root. Tệp `web/tsconfig.app.json` trỏ tường minh:
```json
"tsBuildInfoFile": "../node_modules/.tmp/tsconfig.app.tsbuildinfo"

```


* **Environment variables:** Do Vite chạy từ `web/`, cấu hình trong `web/vite.config.ts` bắt buộc dùng `envDir: '..'` và `loadEnv(mode, '..', 'VITE_')` để ép hệ thống đọc tệp `.env` từ root cho cả config lẫn mã nguồn React (`import.meta.env.VITE_*`).
* **Dev proxy:** Mọi request dạng `/api/*` được Vite tự động proxy sang FastAPI theo cấu hình từ biến môi trường, tránh lỗi CORS trong môi trường dev và không hardcode URL.

## Python Backend Operation (`server/`)

* **Environment management:** Sử dụng `uv`. Lệnh `uv sync` đọc `pyproject.toml` để tạo `.venv/` tại root. Các script gọi qua `uv run` để chạy trực tiếp trong context của môi trường ảo, không cần kích hoạt (activate) thủ công.
* **Namespace Package:** Dự án ứng dụng Python 3.3+, không sử dụng các tệp `__init__.py` trống để import.

## Quy chuẩn Cấu hình & Import Backend

### Tiền tố `cross-env PYTHONPATH=.`

* **Bắt buộc:** Thêm vào trước tất cả các lệnh thực thi runtime, kiểm thử hoặc di cư dữ liệu (`uv run fastapi dev`, `uv run python check_core.py`, `uv run alembic...`) từ root. Tiền tố này đưa root vào `sys.path` để Python nhận diện gói `server.*`, công cụ `cross-env` giúp đồng nhất cú pháp trên Windows/macOS/Linux.
* **Ngoại lệ:** Các lệnh quản lý package của uv (`uv add`, `uv remove`, `uv sync`) không cần thêm tiền tố này.

### Quy chuẩn Import tuyệt đối

* **Chuẩn:** `from server.routers.auth import router as auth_router`
* **Nghiêm cấm:** `from server.routers import auth` (Import bắc cầu qua thư mục cha).
* **Mục đích:** Đảm bảo trình phân tích tĩnh của IDE hoạt động đúng, hỗ trợ điều hướng nhanh (Ctrl+Click), tìm kiếm chuỗi (Ctrl+Shift+F) và an toàn khi refactor.

### Hệ thống kiểm soát cấu hình

* **Alembic:** `alembic.ini` và thư mục `alembic/` đặt trong `server/`. Cấu hình trong `alembic.ini` phải có `prepend_sys_path = ..` để bổ sung root vào tầm vực. Tệp `alembic/env.py` bắt buộc phải import tường minh trực tiếp từng tệp model thực thể để tính năng `--autogenerate` hoạt động:
```python
import server.models.user
import server.models.log

```


* **Environment Config:** Tệp `server/config.py` là **Single Source of Truth** sử dụng `pydantic-settings` để tự động nạp `.env` từ root. Không sử dụng trực tiếp `os.getenv()` hoặc `load_dotenv()` ở các file khác. Toàn bộ hệ thống chỉ import đối tượng tập trung: `from server.config import settings`.

## Tối ưu hóa Khởi tạo & Edge Cases

* **Gemini Client:** Không khởi tạo lại client tại mỗi request. Khởi tạo duy nhất một lần trong sự kiện `lifespan` tại `main.py` và gắn vào trạng thái ứng dụng: `app.state.gemini = genai.Client(...)`. Truy cập ở tầng nghiệp vụ qua `request.app.state.gemini`.
* **Khởi tạo Router:** Để tránh lỗi dừng tiến trình (`AttributeError`) khi `main.py` thực hiện `app.include_router`, tất cả các tệp router mới tạo (dù chưa viết logic) bắt buộc phải khai báo sẵn thực thể trống:
```python
from fastapi import APIRouter
router = APIRouter()

```



## Những điều tuyệt đối KHÔNG làm

1. Không tạo tệp `package.json` hoặc thực thi lệnh `npm install` bên trong thư mục `web/`.
2. Không phân tách hoặc đặt tệp cấu hình `.env` cục bộ bên trong thư mục `web/`.
3. Không viết bình luận (comments) nội tuyến rải rác trong các khối lệnh backend; toàn bộ bình luận giải thích giải pháp hoặc tổng quan kiến trúc phải được đưa lên đầu tệp tin.

---

## Kế hoạch tách Repositories (Tương lai)

Nếu tách `web/` và `server/` thành 2 repo riêng độc lập:

### Kho lưu trữ Frontend (`web/` lên root)

* Xóa tiền tố `cd web &&` trong tất cả npm scripts.
* `vite.config.ts`: Đổi `envDir: '..'` $\rightarrow$ `envDir: '.'` và `loadEnv(mode, '..', ...)` $\rightarrow$ `loadEnv(mode, '.', ...)`.
* `tsconfig.app.json`: Đổi `"tsBuildInfoFile": "../node_modules/..."` $\rightarrow$ `"tsBuildInfoFile": "./node_modules/..."`.
* Loại bỏ thuộc tính `references` tại tệp cấu hình tổng.

### Kho lưu trữ Backend (`server/` và cấu hình Python lên root)

* Điều chỉnh script `dev:server` thành: `uv run fastapi dev main.py`.
* Đặt `.env` tại thư mục gốc của repo backend để Pydantic nạp trực tiếp.
* **Cấu hình CORS bắt buộc:** Thêm `CORSMiddleware` vào FastAPI và khai báo tường minh danh sách domain được phép (Origins) từ URL của repo Frontend do không còn Vite proxy.