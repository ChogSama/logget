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
* **Cơ chế kiểm tra giao diện:** Lỗi xảy ra khi file `.jsx` / `.tsx` vừa xuất cấu trúc React Component vừa xuất hàm hoặc hằng số. Dự án yêu cầu tách riêng các thành phần này để tránh lỗi tải lại trang khi lập trình. Hiện tại, một số file đang dùng tạm các comment sau để ẩn cảnh báo.
```
// eslint-disable-next-line
// eslint-disable-next-line react-refresh/only-export-components
```

* **Environment variables:** Do Vite chạy từ `web/`, cấu hình trong `web/vite.config.ts` bắt buộc dùng `envDir: '..'` và `loadEnv(mode, '..', 'VITE_')` để ép hệ thống đọc tệp `.env` từ root cho cả config lẫn mã nguồn React (`import.meta.env.VITE_*`).
* **Dev proxy:** Mọi request dạng `/api/*` được Vite tự động proxy sang FastAPI theo cấu hình từ biến môi trường, tránh lỗi CORS trong môi trường dev và không hardcode URL.

## Python Backend Operation (`server/`)

* **Environment management:** Sử dụng `uv`. Lệnh `uv sync` đọc `pyproject.toml` để tạo `.venv/` tại root. Các script gọi qua `uv run` để chạy trực tiếp trong context của môi trường ảo, không cần kích hoạt (activate) thủ công.
* **Namespace Package:** Dự án ứng dụng Python 3.3+, không sử dụng các tệp `__init__.py` trống để import.

## Quy chuẩn Cấu hình & Import Backend

### Tiền tố `cross-env PYTHONPATH=.`

* **Bắt buộc:** Thêm vào trước tất cả các lệnh thực thi runtime, kiểm thử hoặc di cư dữ liệu (`uv run fastapi dev`, `uv run python check_core.py`, `uv run alembic...`) từ root. Tiền tố này đưa root vào `sys.path` để Python nhận diện gói `server.*`, công cụ `cross-env` giúp đồng nhất cú pháp trên Windows/macOS/Linux.
* **Môi trường Windows:** Nếu hệ thống báo lỗi không nhận diện lệnh `cross-env`, thay thế bằng tiền tố `npx cross-env PYTHONPATH=.` để sử dụng trực tiếp công cụ có sẵn trong `node_modules` ở root.
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


## Google OAuth — Code Exchange Flow

Thay vì trả token trực tiếp từ callback (không an toàn khi token lộ trên URL), BE dùng luồng 3 bước:

```
React                     FastAPI                    Google
  │                          │                           │
  ├─ GET /auth/google ──────►│                           │
  │                          ├─ redirect ───────────────►│
  │                          │                           │ (user đăng nhập)
  │                          │◄─── redirect + code ──────┤
  │                          │                           │
  │                          │ exchange_google_code(code)│
  │                          │ → upsert User vào DB      │
  │                          │ → create_oauth_code()     │
  │◄─── redirect /auth/callback?code=<oauth_code> ───────┤
  │                          │                           │
  ├── POST /auth/google/token {code} ──────────────────► │
  │◄─── {access_token, refresh_token} ───────────────────┤
```

**oauth_code**: JWT loại `type="oauth_code"`, TTL 5 phút, ký bằng `SECRET_KEY`. Không có cơ chế invalidate sau dùng ở MVP (acceptable vì TTL ngắn). Nếu cần strict one-time: lưu code đã dùng vào Redis/DB.

**Frontend cần làm**: Khi React nhận được redirect tới `/auth/callback?code=...`, parse query param `code` rồi gọi `POST /auth/google/token` để lấy JWT.

## JWT — Phân biệt `type`

| `type`       | TTL   | Dùng ở đâu                              |
|---|---|---|
| `access`     | 30min | Bearer token mọi endpoint               |
| `refresh`    | 7d    | POST /auth/refresh                      |
| `oauth_code` | 5min  | POST /auth/google/token (Google flow)   |

`decode_token(token, expected_type)` — kiểm tra `type` trước khi trả `sub`. `dependencies.py` gọi mặc định `expected_type="access"`.


## Google OAuth với React PWA & Capacitor (Android App)

### Vấn đề (The Issue)
- Luồng Google OAuth hiện tại sử dụng Web Client ID (`server.config`).
- Khi đóng gói bằng Capacitor lên Android, ứng dụng chạy dưới scheme `capacitor://localhost` hoặc `http://localhost`. 
- Google Cloud Console **chặn** không cho phép cấu hình `Redirect URI` với các scheme của ứng dụng hybrid này, dẫn đến lỗi đá hướng (Redirect) trên thiết bị di động.

### Hướng giải quyết (Resolution)
- **Kiến trúc:** Tách biệt luồng đăng nhập giữa Web (PWA) và Native App (Capacitor).
- **Google Cloud Console:** Tạo thêm một **OAuth Client ID** với Application type là **Android** (cần SHA-1 fingerprint từ keystore).
- **Frontend (Capacitor):** Sử dụng plugin native `@codetrix-studio/capacitor-google-auth` để gọi gọi hộp thoại đăng nhập của hệ thống Android.
- **Backend (FastAPI):** Bổ sung logic hoặc endpoint chấp nhận verify `id_token` trực tiếp từ Android Client gửi lên, thay vì chỉ nhận `code` từ luồng Web.

## Server Log & Cloudinary Storage

### Quy tắc xử lý thời gian & Múi giờ

* **Lưu trữ:** Mọi timestamp trong DB (`logged_at`) bắt buộc là timezone-naive UTC (loại bỏ `tzinfo` sau khi convert qua `_to_utc()`).
* **Truy vấn:** Khi lọc nhật ký theo ngày (`GET /logs?date=...`), bắt buộc quy đổi khoảng thời gian UTC tương ứng với ngày đó theo múi giờ cục bộ của client (`_day_utc_range()`).

### Ràng buộc đồng thời của trường thời gian (Atomic Updates)

* Trong `LogUpdate`, bộ 3 trường `start_time`, `end_time`, `timezone` phải được gửi đầy đủ cùng nhau hoặc không gửi trường nào nhằm bảo toàn logic tính toán thời lượng (`duration_hours`).

### Đồng nhất kiểu dữ liệu & Dependency

* **Enum:** Định nghĩa duy nhất `ActivityType` tại schema; model bắt buộc import lại để tránh lỗi xung đột thực thể của SQLAlchemy.
* **User ID:** Hàm phụ thuộc `get_current_user` trả về chuỗi/ID thô từ token. Tầng router phải ép kiểu tường minh sang `UUID` thông qua hàm bổ trợ `_ensure_uuid()` trước khi truyền xuống tầng service.

### Dọn dẹp tài nguyên Cloudinary

* Bất kỳ thao tác nào làm thay đổi hoặc xóa bỏ giá trị cũ của `media_url` (tại `PATCH` và `DELETE`) bắt buộc phải gọi hàm `delete_media` qua tác vụ chạy ngầm `BackgroundTasks` để giải phóng tài nguyên bất đồng bộ, tránh gây nghẽn luồng phản hồi API.

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
---

## Xử lý Ngoại lệ và Giao dịch (Database Transactions)

* **Quản lý trạng thái giao dịch khi thất bại:** Quy tắc bắt buộc thực hiện `db.rollback()` trước khi cập nhật trạng thái lỗi hoặc thực hiện bất kỳ lệnh `commit()` nào khác trong khối `except Exception`. Khi exception xuất phát từ tầng DB, transaction block đã bị đánh dấu aborted — gọi `commit()` trực tiếp sẽ kích hoạt `InvalidRequestError` lồng nhau. Pattern chuẩn tại `_run_analysis_safe` (`insights.py`):
  ```python
  except HTTPException:
      raise  # Không nuốt lỗi validation — để FastAPI xử lý
  except Exception as e:
      await db.rollback()
      summary.status = "FAILED"
      await db.commit()
  ```

## Xác thực và Chuẩn hóa Dữ liệu Đầu vào (Input Validation)

* **Kiểm soát chuỗi IANA Timezone:** Quy định validate định dạng múi giờ tại tầng schema để chặn sớm ngoại lệ `ZoneInfoNotFoundError`. Dùng `@field_validator("timezone")` gọi `ZoneInfo(v)` trong `LogCreate`, `LogUpdate`, `AnalyzeRequest` — trả 422 trước khi xuống service layer. `_parse_tz()` tại service vẫn giữ làm safety net.
* **Ràng buộc định dạng chuỗi ngày (Date String):** Quy chuẩn sử dụng kiểu dữ liệu `date` trực tiếp trong Pydantic request schema (`AnalyzeRequest.date: date`) thay vì `str` — Pydantic tự parse và validate ISO format, trả 422 nếu không đúng thay vì `ValueError` → 500 tại router. Với Query param dùng `pattern=r"^\d{4}-\d{2}-\d{2}$"`.

## Thiết kế Phương thức Cập nhật (PATCH Method Constraints)

* **Tính độc lập của cập nhật một phần:** Quy tắc thiết kế logic cập nhật thời gian trong phương thức PATCH, cho phép cập nhật độc lập các trường `start_time` hoặc `end_time` bằng cách đối chiếu dữ liệu hiện tại trong database thay vì bắt buộc truyền đồng thời cả hai. `timezone` vẫn bắt buộc khi gửi bất kỳ time field nào. `duration_hours` tính lại từ giá trị mới và giá trị DB hiện tại (`_naive_utc(log.logged_at) + timedelta(hours=log.duration_hours)`).

## Quy ước Chuỗi Tích lũy và Chỉ số Toán học

* **Đồng bộ thời gian tính Streak:** Quy tắc tính toán mốc ngày hiện tại dựa trên múi giờ cục bộ của người dùng thay vì sử dụng thời gian mặc định của server. Hàm `_local_today(timezone)` dùng `pytz` dùng chung cho `/overview`, `/streak`, `/lbs` — tránh lệch ngày với user Việt Nam (UTC+7) trong khung giờ 00:00–06:59. Không sử dụng `date.today()` trong bất kỳ endpoint nào phụ thuộc ngày địa phương của người dùng.
* **Kiểm soát tham số Scoring Engine:** Ràng buộc bất biến đối với các tham số hình học Plateau-Gaussian và trọng số EWMA/ACWR tại tầng service toán học (`services/lbs.py`). Các hằng số module-level (`_SIGMA_*`, `_LAMBDA_*`, `_WEIGHTS`) không được sửa đổi ngoài file — mọi thay đổi tham số chỉ thực hiện tại `lbs.py` và phải cập nhật đồng thời header comment để duy trì tính nhất quán tài liệu hóa.