"""
server/services/ai.py

Orchestration layer: Gemini API + State Machine + Batch Processing for Sleep Hours.
"""
import asyncio
import json
import logging
from datetime import date, datetime, time as time_type, timedelta
from functools import lru_cache
from pathlib import Path
from uuid import UUID
from zoneinfo import ZoneInfo

from google.genai.errors import APIError
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.models.log import ActivityLog, AIInsight, DailySummary, InsightType
from server.services import lbs as lbs_service

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_MODEL = "gemini-2.0-flash"
_UTC = ZoneInfo("UTC")
_DEFAULT_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


@lru_cache(maxsize=None)
def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


def _strip_code_fence(raw_text: str) -> str:
    cleaned = raw_text.strip()
    if "```" not in cleaned:
        return cleaned

    parts = cleaned.split("```")
    cleaned = parts[1] if len(parts) >= 2 else cleaned
    if cleaned.startswith("json"):
        cleaned = cleaned[4:]
    return cleaned.strip()


def _parse_json_response(raw_text: str | None) -> dict:
    if not raw_text:
        return {}

    try:
        return json.loads(_strip_code_fence(raw_text))
    except Exception:
        return {}


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
                DailySummary.lbs_score.is_not(None),
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
                DailySummary.lbs_score.is_not(None),
            )
        )
        .order_by(DailySummary.date.desc())
        .limit(1)
    )
    prev = prev_result.scalar_one_or_none()

    prev_aw = prev.acute_workload if (prev and prev.acute_workload is not None) else 0.0
    prev_cw = prev.chronic_workload if (prev and prev.chronic_workload is not None) else 0.0
    return prev_aw, prev_cw, prev_count + 1


async def get_daily_summary(
    db: AsyncSession, user_id: UUID, target_date: date
) -> DailySummary | None:
    result = await db.execute(
        select(DailySummary).where(
            and_(DailySummary.user_id == user_id, DailySummary.date == target_date)
        )
    )
    return result.scalar_one_or_none()


async def _get_logs_for_date_batch(
    db: AsyncSession, user_id: UUID, target_date: date
) -> list[ActivityLog]:
    """Query logs cho batch processor — dùng _DEFAULT_TZ (Asia/Ho_Chi_Minh) làm fallback."""
    start_utc = datetime.combine(target_date, time_type.min, tzinfo=_DEFAULT_TZ).astimezone(_UTC)
    end_utc = datetime.combine(target_date, time_type.max, tzinfo=_DEFAULT_TZ).astimezone(_UTC)
    result = await db.execute(
        select(ActivityLog).where(
            and_(
                ActivityLog.user_id == user_id,
                ActivityLog.logged_at >= start_utc,
                ActivityLog.logged_at <= end_utc,
            )
        )
    )
    return result.scalars().all()


async def _execute_rule_based_pipeline(
    db: AsyncSession,
    user_uuid: UUID,
    target_date: date,
    agg,
    recovery_score: float,
    summary: DailySummary,
    ai_summary: str = "Rule-based summary only.",
    summary_status: str = "INIT",
) -> DailySummary:
    return await _execute_pure_math_pipeline(
        db=db,
        user_uuid=user_uuid,
        target_date=target_date,
        agg=agg,
        recovery_score=recovery_score,
        ai_summary=ai_summary,
        summary=summary,
        summary_status=summary_status,
    )


async def refresh_daily_summary_rule_based(
    db: AsyncSession,
    user_uuid: UUID,
    target_date: date,
) -> DailySummary | None:
    logs = await _get_logs_for_date_batch(db, user_uuid, target_date)
    summary = await get_daily_summary(db, user_uuid, target_date)

    if not logs:
        if summary is not None:
            await db.delete(summary)
            await db.commit()
        return None

    agg = lbs_service.aggregate_logs(logs)

    if summary is None:
        summary = DailySummary(user_id=user_uuid, date=target_date, status="INIT")
        db.add(summary)
        await db.commit()
    else:
        summary.status = "INIT"

    return await _execute_rule_based_pipeline(
        db=db,
        user_uuid=user_uuid,
        target_date=target_date,
        agg=agg,
        recovery_score=lbs_service.DEFAULT_RECOVERY,
        summary=summary,
        ai_summary="Rule-based summary only.",
        summary_status="INIT",
    )


# --- Main Pipeline & State Machine ---

async def analyze_day(
    db: AsyncSession,
    user_uuid: UUID,
    target_date: date,
    logs: list[ActivityLog],
    gemini,
    summary: DailySummary,
) -> DailySummary:
    if summary.status == "PROCESSING" and summary.id is not None:
        return summary

    summary.status = "PROCESSING"
    await db.commit()

    try:
        agg = lbs_service.aggregate_logs(logs)
        prelim = lbs_service.compute_scores(agg, lbs_service.DEFAULT_RECOVERY)
        prelim_lbs = lbs_service.compute_lbs(prelim)

        base_summary = (
            "Hệ thống ghi nhận dữ liệu hoạt động chuẩn hóa (Không có ghi chú bổ sung)."
            if not agg.notes.strip()
            else "Hoàn thành phân tích chỉ số hồi phục."
        )

        recovery_score = lbs_service.DEFAULT_RECOVERY
        ai_summary = base_summary
        final_status = "SUCCESS"

        if agg.notes.strip():
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

            raw_response, status_code = await _call_gemini_with_handling(gemini, base_prompt + user_data)

            if status_code == "SUCCESS" and raw_response:
                parsed = _parse_json_response(raw_response)
                if parsed:
                    r = parsed.get("recovery_score", {})
                    try:
                        recovery_score = (
                            float(r.get("psychological_detachment", 12))
                            + float(r.get("relaxation", 12))
                            + float(r.get("mastery", 13))
                            + float(r.get("control", 13))
                        )
                    except Exception:
                        recovery_score = lbs_service.DEFAULT_RECOVERY
                    recovery_score = min(100.0, max(0.0, recovery_score))
                    ai_summary = parsed.get("summary") or base_summary
                else:
                    final_status = "FAILED"
                    ai_summary = (
                        "Hệ thống AI trả về dữ liệu không hợp lệ. "
                        "Tiến trình lưu trữ an toàn. Vui lòng bấm thử lại."
                    )
                    recovery_score = lbs_service.DEFAULT_RECOVERY
            elif status_code == "RATE_LIMIT":
                final_status = "QUEUE_SLEEP_HOURS"
                ai_summary = (
                    "Yêu cầu đang được xếp hàng chờ xử lý tự động vào khung giờ thấp điểm "
                    "(đêm nay). Trạng thái hiển thị sẽ tự động cập nhật sau."
                )
            else:
                final_status = "FAILED"
                ai_summary = (
                    "Hệ thống AI gặp sự cố kết nối vật lý. Tiến trình lưu trữ an toàn. "
                    "Vui lòng bấm thử lại."
                )

        return await _execute_pure_math_pipeline(
            db,
            user_uuid,
            target_date,
            agg,
            recovery_score,
            ai_summary,
            summary,
            summary_status=final_status,
        )

    except Exception as e:
        summary.status = "FAILED"
        summary.ai_summary = f"Hệ thống gặp sự cố xử lý nội bộ: {str(e)}. Tiến trình được bảo lưu an toàn."
        await db.commit()
        return summary


async def _execute_pure_math_pipeline(
    db: AsyncSession,
    user_uuid: UUID,
    target_date: date,
    agg,
    recovery_score: float,
    ai_summary: str,
    summary: DailySummary,
    summary_status: str = "SUCCESS",
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
    summary.status = summary_status

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

    user_buckets: dict[UUID, list[DailySummary]] = {}
    for s in queued_summaries:
        user_buckets.setdefault(s.user_id, []).append(s)

    for user_id, summaries in user_buckets.items():
        batch_prompt = _load_prompt("batch_sleep_summary.txt")
        bulk_data = []
        agg_cache: dict[str, lbs_service.DayAggregate] = {}

        for s in summaries:
            day_logs = await _get_logs_for_date_batch(db, user_id, s.date)
            agg = lbs_service.aggregate_logs(day_logs)
            agg_cache[str(s.date)] = agg
            bulk_data.append(
                {
                    "date": str(s.date),
                    "work_h": agg.work_h,
                    "sleep_h": agg.sleep_h,
                    "social_h": agg.social_h,
                    "exercise_h": agg.exercise_mpa_h + agg.exercise_vpa_h,
                    "notes": agg.notes,
                }
            )

        full_payload = batch_prompt + f"\n\nDATA_BATCH:\n{json.dumps(bulk_data, ensure_ascii=False)}"

        try:
            raw_resp, status = await _call_gemini_with_handling(gemini_client, full_payload)
            results_dict: dict[str, dict] = {}

            if status == "SUCCESS" and raw_resp:
                results_dict = _parse_json_response(raw_resp)

            for s in summaries:
                date_str = str(s.date)
                agg = agg_cache.get(date_str)
                if agg is None:
                    continue

                day_res = results_dict.get(date_str)

                if day_res:
                    r = day_res.get("recovery_score", {})
                    try:
                        recovery_score = (
                            float(r.get("psychological_detachment", 12))
                            + float(r.get("relaxation", 12))
                            + float(r.get("mastery", 13))
                            + float(r.get("control", 13))
                        )
                    except Exception:
                        recovery_score = lbs_service.DEFAULT_RECOVERY

                    recovery_score = min(100.0, max(0.0, recovery_score))
                    ai_summary = day_res.get("summary") or "Phân tích hoàn thiện trong chu kỳ nén dữ liệu đêm."
                    summary_status = "SUCCESS"
                else:
                    recovery_score = lbs_service.DEFAULT_RECOVERY
                    ai_summary = "Phân tích hoàn thiện trong chu kỳ nén dữ liệu đêm."
                    summary_status = "QUEUE_SLEEP_HOURS"

                await _execute_pure_math_pipeline(
                    db,
                    user_id,
                    s.date,
                    agg,
                    recovery_score,
                    ai_summary,
                    s,
                    summary_status=summary_status,
                )

        except Exception as e:
            logger.error(f"Batch processing failed for user {user_id}: {str(e)}")
            continue


# --- Pattern Insight ---

async def generate_pattern_insight(db: AsyncSession, user_uuid: UUID, days: int, gemini) -> AIInsight:
    cutoff = date.today() - timedelta(days=days)
    result = await db.execute(
        select(DailySummary)
        .where(
            and_(
                DailySummary.user_id == user_uuid,
                DailySummary.date >= cutoff,
                DailySummary.lbs_score.is_not(None),
            )
        )
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
                    "summary": s.ai_summary,
                }
                for s in summaries
            ],
            ensure_ascii=False,
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
