"""
server/services/ai.py

Orchestration layer: Gemini API + LBS pipeline + DB upsert.

analyze_day(db, user_uuid, target_date, logs, gemini, summary):
    1. aggregate_logs → DayAggregate
    2. Gemini (1 call): score x_R (REQ 4 dims) + generate Vietnamese daily summary
    3. compute_scores, compute_lbs, is_imbalance
    4. compute_ewma (với EWMA state của ngày trước từ DB)
    5. Upsert DailySummary → status=SUCCESS
    Fallback: Gemini fail → x_R=50, rule-based summary; vẫn trả SUCCESS.

generate_pattern_insight(db, user_uuid, days, gemini):
    Query last `days` SUCCESS summaries → Gemini pattern → store AIInsight.

Rate limit: Gemini free tier 15 RPM.
    analyze_day = 1 call/request. generate_pattern_insight = 1 call/request.
"""
import asyncio
import json
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.models.log import ActivityLog, AIInsight, DailySummary, InsightType
from server.services import lbs as lbs_service

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_MODEL = "gemini-2.0-flash"


@lru_cache(maxsize=None)
def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


# --- Gemini ---

async def _call_gemini(client, prompt: str) -> str:
    """1 retry với delay 1s."""
    for attempt in range(2):
        try:
            resp = await client.aio.models.generate_content(model=_MODEL, contents=prompt)
            return resp.text
        except Exception:
            if attempt == 1:
                raise
            await asyncio.sleep(1.0)


# --- DB helpers ---

async def get_daily_summary(
    db: AsyncSession, user_id: UUID, target_date: date
) -> DailySummary | None:
    result = await db.execute(
        select(DailySummary).where(
            and_(DailySummary.user_id == user_id, DailySummary.date == target_date)
        )
    )
    return result.scalar_one_or_none()


async def _get_ewma_state(
    db: AsyncSession, user_id: UUID, before_date: date
) -> tuple[float, float, int]:
    """Returns (prev_raw_aw, prev_raw_cw, day_index_cho_ngày_target)."""
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


# --- Recovery scoring + daily summary ---

def _fallback_summary(lbs: float) -> str:
    if lbs >= 75:
        return f"Hôm nay bạn duy trì lối sống khá cân bằng (LBS: {lbs:.0f}). Tiếp tục phát huy!"
    if lbs >= 50:
        return f"Điểm cân bằng hôm nay là {lbs:.0f}. Một vài khía cạnh có thể cải thiện thêm."
    return f"Hôm nay điểm cân bằng ở mức thấp ({lbs:.0f}). Hãy chú ý nghỉ ngơi và phục hồi."


async def _gemini_analyze(
    client, agg: lbs_service.DayAggregate, prelim_lbs: float
) -> tuple[float, str]:
    """
    1 Gemini call: trả về (recovery_score 0–100, summary_text).
    Fallback: (DEFAULT_RECOVERY, rule-based text) khi fail hoặc không có note.
    """
    if not agg.notes.strip():
        return lbs_service.DEFAULT_RECOVERY, _fallback_summary(prelim_lbs)

    base_prompt = _load_prompt("daily_summary.txt")
    user_data = (
        f"\n\n---\nDỮ LIỆU HOẠT ĐỘNG HÔM NAY:\n"
        f"- Làm việc: {round(agg.work_h, 2)} giờ\n"
        f"- Ngủ: {round(agg.sleep_h, 2)} giờ\n"
        f"- Giao tiếp xã hội: {round(agg.social_h, 2)} giờ\n"
        f"- Vận động: {round(agg.exercise_mpa_h + agg.exercise_vpa_h, 2)} giờ\n"
        f"- Điểm LBS sơ bộ (chưa có Recovery): {prelim_lbs:.1f}\n\n"
        f"GHI CHÚ NGƯỜI DÙNG:\n{agg.notes}\n"
    )

    try:
        raw = await _call_gemini(client, base_prompt + user_data)
        raw = raw.strip()
        # Strip markdown code fences nếu có
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) >= 2 else raw
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())
        r = data.get("recovery_score", {})
        x_r = (
            float(r.get("psychological_detachment", 12))
            + float(r.get("relaxation", 12))
            + float(r.get("mastery", 13))
            + float(r.get("control", 13))
        )
        x_r = min(100.0, max(0.0, x_r))
        summary = data.get("summary") or _fallback_summary(prelim_lbs)
        return x_r, summary
    except Exception:
        return lbs_service.DEFAULT_RECOVERY, _fallback_summary(prelim_lbs)


# --- Main pipeline ---

async def analyze_day(
    db: AsyncSession,
    user_uuid: UUID,
    target_date: date,
    logs: list[ActivityLog],
    gemini,
    summary: DailySummary,
) -> DailySummary:
    """
    Full day analysis. Caller pre-creates summary với status=PROCESSING.
    Luôn trả SUCCESS (Gemini failure → fallback values, không FAILED).
    """
    agg = lbs_service.aggregate_logs(logs)

    # Tính sơ bộ LBS không có recovery (để làm context cho prompt)
    prelim = lbs_service.compute_scores(agg, lbs_service.DEFAULT_RECOVERY)
    prelim_lbs = lbs_service.compute_lbs(prelim)

    recovery_score, ai_summary = await _gemini_analyze(gemini, agg, prelim_lbs)

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


# --- Pattern insight ---

async def generate_pattern_insight(
    db: AsyncSession,
    user_uuid: UUID,
    days: int,
    gemini,
) -> AIInsight:
    cutoff = date.today() - timedelta(days=days)
    result = await db.execute(
        select(DailySummary)
        .where(
            and_(
                DailySummary.user_id == user_uuid,
                DailySummary.date >= cutoff,
                DailySummary.status == "SUCCESS",
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
            content = await _call_gemini(gemini, base_prompt + user_data)
            content = content.strip()
        except Exception:
            content = "Hệ thống AI tạm thời không khả dụng. Vui lòng thử lại sau."

    insight = AIInsight(
        user_id=user_uuid,
        insight_type=InsightType.pattern,
        content=content,
    )
    db.add(insight)
    await db.commit()
    await db.refresh(insight)
    return insight