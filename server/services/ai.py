"""
server/services/ai.py

Orchestration layer: Gemini API + State Machine + Batch Processing for Sleep Hours.
"""
import asyncio
import json
import logging
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from uuid import UUID

from google.genai.errors import APIError
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.models.log import ActivityLog, AIInsight, DailySummary, InsightType
from server.services import lbs as lbs_service

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_MODEL = "gemini-2.0-flash"


@lru_cache(maxsize=None)
def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


# --- Gemini Adapter ---

async def _call_gemini_with_handling(client, prompt: str) -> tuple[str | None, str]:
    """
    Trả về: (raw_text_nếu_thành_công, mã_lỗi_nếu_thất_bại)
    Mã lỗi: "SUCCESS", "RATE_LIMIT", "API_ERROR"
    """
    for attempt in range(2):
        try:
            resp = await client.aio.models.generate_content(model=_MODEL, contents=prompt)
            return resp.text, "SUCCESS"
        except APIError as e:
            # Mã 429 hoặc các lỗi chỉ định kiệt tài nguyên từ Google API
            if e.code == 429:
                return None, "RATE_LIMIT"
            if attempt == 1:
                return None, "API_ERROR"
            await asyncio.sleep(1.0)
        except Exception:
            if attempt == 1:
                return None, "API_ERROR"
            await asyncio.sleep(1.0)
    return None, "API_ERROR"


# --- DB helpers ---

async def _get_ewma_state(
    db: AsyncSession, user_id: UUID, before_date: date
) -> tuple[float, float, int]:
    count_result = await db.execute(
        select(func.count(DailySummary.id)).where(
            and_(
                DailySummary.user_id == user_id,
                DailySummary.date < before_date,
                DailySummary.status == "SUCCESS",
            )
        )
    )
    prev_count = count_result.scalar() or 0

    prev_result = await db.execute(
        select(DailySummary)
        .where(
            and_(
                DailySummary.user_id == user_id,
                DailySummary.date < before_date,
                DailySummary.status == "SUCCESS",
            )
        )
        .order_by(DailySummary.date.desc())
        .limit(1)
    )
    prev = prev_result.scalar_one_or_none()

    prev_aw = prev.acute_workload if (prev and prev.acute_workload is not None) else 0.0
    prev_cw = prev.chronic_workload if (prev and prev.chronic_workload is not None) else 0.0
    return prev_aw, prev_cw, prev_count + 1


# --- Main Pipeline & State Machine ---

async def analyze_day(
    db: AsyncSession,
    user_uuid: UUID,
    target_date: date,
    logs: list[ActivityLog],
    gemini,
    summary: DailySummary,
) -> DailySummary:
    """
    Hệ thống phân tích có điều kiện trạng thái (State Machine):
    - Tránh Race Condition: Chặn trùng lặp khi đang PROCESSING.
    - Phục hồi tiến trình dở dang khi FAILED: Không tính lại từ đầu.
    - Quản lý Rate Limit: Đẩy vào luồng xử lý ban đêm (QUEUE_SLEEP_HOURS).
    """
    # Bước 1: Kiểm tra trạng thái đồng bộ tránh chạy trùng lặp
    if summary.status == "PROCESSING":
        # Trả về nguyên trạng để router bọc lỗi 425 Too Early bên ngoài
        return summary

    # Đưa vào trạng thái PROCESSING để khóa luồng
    summary.status = "PROCESSING"
    await db.commit()

    agg = lbs_service.aggregate_logs(logs)
    prelim = lbs_service.compute_scores(agg, lbs_service.DEFAULT_RECOVERY)
    prelim_lbs = lbs_service.compute_lbs(prelim)

    if not agg.notes.strip():
        # Không có note -> Không cần gọi AI, chạy thuần toán học trả SUCCESS ngay lập tức
        return await _execute_pure_math_pipeline(db, user_uuid, target_date, agg, lbs_service.DEFAULT_RECOVERY, "Hệ thống ghi nhận dữ liệu hoạt động chuẩn hóa (Không có ghi chú bổ sung).", summary)

    # Bước 2: Thiết lập Prompt
    base_prompt = _load_prompt("daily_summary.txt")
    user_data = (
        f"\n\n---\nDỮ LIỆU HOẠT ĐỘNG HÔM NAY:\n"
        f"- Làm việc: {round(agg.work_h, 2)} giờ\n"
        f"- Ngủ: {round(agg.sleep_h, 2)} giờ\n"
        f"- Giao tiếp xã hội: {round(agg.social_h, 2)} giờ\n"
        f"- Vận động: {round(agg.exercise_mpa_h + agg.exercise_vpa_h, 2)} giờ\n"
        f"- Điểm LBS sơ bộ: {prelim_lbs:.1f}\n\n"
        f"GHI CHÚ NGƯỜI DÙNG:\n{agg.notes}\n"
    )

    # Bước 3: Gọi AI và phân tách lỗi (Chống sập đổ toán học)
    raw_response, status_code = await _call_gemini_with_handling(gemini, base_prompt + user_data)

    if status_code == "RATE_LIMIT":
        # Đánh dấu đưa vào hàng đợi xử lý ban đêm khi người dùng ngủ
        summary.status = "QUEUE_SLEEP_HOURS"
        summary.ai_summary = "Yêu cầu đang được xếp hàng chờ xử lý tự động vào khung giờ thấp điểm (đêm nay). Trạng thái hiển thị sẽ tự động cập nhật sau."
        await db.commit()
        return summary

    if status_code == "API_ERROR" or not raw_response:
        # Giữ nguyên trạng thái FAILED để người dùng thực hiện Force re-analysis (Không mất dữ liệu toán học làm dở)
        summary.status = "FAILED"
        summary.ai_summary = "Hệ thống AI gặp sự cố kết nối vật lý. Tiến trình lưu trữ an toàn. Vui lòng bấm thử lại."
        await db.commit()
        return summary

    # Bước 4: Phân tách cấu trúc JSON an toàn
    try:
        raw_response = raw_response.strip()
        if "```" in raw_response:
            parts = raw_response.split("```")
            raw_response = parts[1] if len(parts) >= 2 else raw_response
            if raw_response.startswith("json"):
                raw_response = raw_response[4:]
        
        data = json.loads(raw_response.strip())
        r = data.get("recovery_score", {})
        x_r = float(r.get("psychological_detachment", 12)) + float(r.get("relaxation", 12)) + float(r.get("mastery", 13)) + float(r.get("control", 13))
        x_r = min(100.0, max(0.0, x_r))
        ai_summary = data.get("summary") or "Hoàn thành phân tích chỉ số hồi phục."
        
        return await _execute_pure_math_pipeline(db, user_uuid, target_date, agg, x_r, ai_summary, summary)
    except Exception:
        # Lỗi phân tách dữ liệu (Parsing Error) coi như FAILED tiến trình
        summary.status = "FAILED"
        summary.ai_summary = "Cấu trúc phản hồi AI không đồng nhất với bộ lọc hệ thống. Tiến trình được giữ lại để phân tích tiếp lần sau."
        await db.commit()
        return summary


async def _execute_pure_math_pipeline(
    db: AsyncSession, user_uuid: UUID, target_date: date, agg, recovery_score: float, ai_summary: str, summary: DailySummary
) -> DailySummary:
    scores = lbs_service.compute_scores(agg, recovery_score)
    lbs_score = lbs_service.compute_lbs(scores)
    imbalance = lbs_service.is_imbalance(scores)

    prev_aw, prev_cw, day_index = await _get_ewma_state(db, user_uuid, target_date)
    wl = 100.0 - lbs_score
    ewma = lbs_service.compute_ewma(wl, prev_aw, prev_cw, day_index)

    summary.lbs_score = lbs_score
    summary.work_score = scores.work
    summary.sleep_score = scores.sleep
    summary.exercise_score = scores.exercise
    summary.social_score = scores.social
    summary.recovery_score = scores.recovery
    summary.imbalance_risk = imbalance
    summary.ai_summary = ai_summary
    summary.acute_workload = ewma.raw_aw
    summary.chronic_workload = ewma.raw_cw
    summary.status = "SUCCESS"

    await db.commit()
    await db.refresh(summary)
    return summary


# --- Cơ chế gom nhóm nén Token ban đêm (Midnight Batch Processing) ---

async def process_midnight_batch(db: AsyncSession, gemini_client) -> None:
    """
    Cronjob kích hoạt định kỳ lúc 02:00 AM.
    Gom nhóm toàn bộ các yêu cầu lưu trữ trạng thái QUEUE_SLEEP_HOURS để xử lý trong 1 cuộc gọi duy nhất.
    Sử dụng kỹ thuật nén n-ngày vào 1 token payload. Càng dồn nhiều ngày độ phân tích sâu càng giảm.
    """
    result = await db.execute(
        select(DailySummary)
        .where(DailySummary.status == "QUEUE_SLEEP_HOURS")
        .order_by(DailySummary.user_id, DailySummary.date.asc())
    )
    queued_summaries = result.scalars().all()

    if not queued_summaries:
        return

    # Gom nhóm theo từng user_id để bảo mật dữ liệu chéo
    user_buckets = {}
    for s in queued_summaries:
        user_buckets.setdefault(s.user_id, []).append(s)

    for user_id, summaries in user_buckets.items():
        # Xây dựng Batch Prompt nén dữ liệu
        batch_prompt = _load_prompt("batch_sleep_summary.txt")
        bulk_data = []
        
        for s in summaries:
            # Truy vấn ngược nhật ký thô của ngày lỗi đó để đồng bộ
            logs_result = await db.execute(select(ActivityLog).where(and_(ActivityLog.user_id == user_id, func.date(ActivityLog.start_time) == s.date)))
            day_logs = logs_result.scalars().all()
            agg = lbs_service.aggregate_logs(day_logs)
            bulk_data.append({
                "date": str(s.date),
                "work_h": agg.work_h,
                "sleep_h": agg.sleep_h,
                "social_h": agg.social_h,
                "exercise_h": agg.exercise_mpa_h + agg.exercise_vpa_h,
                "notes": agg.notes
            })

        full_payload = batch_prompt + f"\n\nDATA_BATCH:\n{json.dumps(bulk_data, ensure_ascii=False)}"

        try:
            # Chạy nén dữ liệu bằng 1 request duy nhất cho toàn bộ chuỗi ngày bị dồn ứ
            raw_resp, status = await _call_gemini_with_handling(gemini_client, full_payload)
            if status != "SUCCESS" or not raw_resp:
                continue
                
            if "```" in raw_resp:
                raw_resp = raw_resp.split("```")[1]
                if raw_resp.startswith("json"):
                    raw_resp = raw_resp[4:]

            results_dict = json.loads(raw_resp.strip())  # Kỳ vọng định dạng: {"YYYY-MM-DD": {"psychological_detachment":... , "summary": "..."}}
            
            for s in summaries:
                date_str = str(s.date)
                if date_str in results_dict:
                    day_res = results_dict[date_str]
                    r = day_res.get("recovery_score", {})
                    x_r = float(r.get("psychological_detachment", 12)) + float(r.get("relaxation", 12)) + float(r.get("mastery", 13)) + float(r.get("control", 13))
                    x_r = min(100.0, max(0.0, x_r))
                    ai_summary = day_res.get("summary") or "Phân tích hoàn thiện trong chu kỳ nén dữ liệu đêm."
                    
                    # Chạy nốt toán học lưu DB
                    logs_result = await db.execute(select(ActivityLog).where(and_(ActivityLog.user_id == user_id, func.date(ActivityLog.start_time) == s.date)))
                    day_logs = logs_result.scalars().all()
                    agg = lbs_service.aggregate_logs(day_logs)
                    await _execute_pure_math_pipeline(db, user_id, s.date, agg, x_r, ai_summary, s)
        except Exception as e:
            logger.error(f"Batch processing failed for user {user_id}: {str(e)}")
            continue


# --- Pattern Insight ---
async def generate_pattern_insight(db: AsyncSession, user_uuid: UUID, days: int, gemini) -> AIInsight:
    cutoff = date.today() - timedelta(days=days)
    result = await db.execute(
        select(DailySummary)
        .where(and_(DailySummary.user_id == user_uuid, DailySummary.date >= cutoff, DailySummary.status == "SUCCESS"))
        .order_by(DailySummary.date.asc())
    )
    summaries = result.scalars().all()

    if len(summaries) < 3:
        content = "Chưa có đủ dữ liệu để phân tích xu hướng (cần ít nhất 3 ngày). Hãy tiếp tục ghi nhật ký hàng ngày!"
    else:
        base_prompt = _load_prompt("pattern_insight.txt")
        data_str = json.dumps(
            [
                {
                    "date": str(s.date), 
                    "lbs_score": s.lbs_score, 
                    "work_score": s.work_score, 
                    "sleep_score": s.sleep_score, 
                    "exercise_score": s.exercise_score, 
                    "social_score": s.social_score, 
                    "recovery_score": s.recovery_score, 
                    "imbalance_risk": s.imbalance_risk, 
                    "summary": s.ai_summary
                } 
                for s in summaries
            ], 
            ensure_ascii=False
        )
        user_data = f"\n\n---\nDỮ LIỆU {days} NGÀY GẦN NHẤT:\n{data_str}\n"
        try:
            content, status = await _call_gemini_with_handling(gemini, base_prompt + user_data)
            if status != "SUCCESS":
                content = "Hệ thống AI phân tích xu hướng tạm thời quá tải. Biểu đồ toán học của bạn vẫn hiển thị chính xác."
        except Exception:
            content = "Hệ thống AI tạm thời không khả dụng. Vui lòng thử lại sau."

    insight = AIInsight(user_id=user_uuid, insight_type=InsightType.pattern, content=content)
    db.add(insight)
    await db.commit()
    await db.refresh(insight)
    return insight