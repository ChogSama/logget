"""
server/services/lbs.py

LBS (Lifestyle Balance Score) scoring engine — pure math, không có I/O.

Component scores (0–100):
    Sleep (x_Sl)   : Asymmetric Plateau-Gaussian, optimal 7–9h
        σ_L=1.5 (steeper, penalizes under-sleep)
        σ_R=1.8 (gentler, penalizes over-sleep) ← confirmed from doc
    Work (x_W)     : Asymmetric Plateau-Gaussian, optimal 6–8h
        σ_W,L=3.0 (gentler, under-working)
        σ_W,R=√4.5≈2.121 (steep, overworking) ← calc từ doc: 12h→16.9đ
    Social (x_So)  : Asymmetric Plateau-Gaussian, optimal 1–3h
        σ_So,L=0.8 (steep, social isolation) ← calc từ doc: 0h→45.7đ
        σ_So,R=2.5 (gentler, over-socializing)
    Exercise (x_E) : MET-min model — V_E=4.0*t_MPA+8.0*t_VPA, target 120 MET-min
    Recovery (x_R) : NLP-based via Gemini (0–100), default _DEFAULT_RECOVERY khi không có note

LBS weights: ω_W=0.20, ω_So=0.15, ω_Sl=0.25, ω_E=0.15, ω_R=0.25

EWMA/ACWR burnout risk:
    WL_t = 100 - S_B
    λ_a=0.50 (N_a=3), λ_c=2/29≈0.069 (N_c=28)
    AW_t = λ_a*WL_t + (1-λ_a)*AW_{t-1}   — lưu vào daily_summaries.acute_workload
    CW_t = λ_c*WL_t + (1-λ_c)*CW_{t-1}   — lưu vào daily_summaries.chronic_workload
    Bias correction: X_corr = X_t / (1-(1-λ)^t)
    ACWR = AW_corr / CW_corr
    R_burn = min(100, AW_corr * φ(ACWR))

imbalance_risk = True khi ≥2 component scores < 50
"""
import math
from dataclasses import dataclass

from server.models.log import ActivityLog

_WEIGHTS = {"work": 0.20, "social": 0.15, "sleep": 0.25, "exercise": 0.15, "recovery": 0.25}

_SIGMA_SL_L = 1.5
_SIGMA_SL_R = 1.8
_SIGMA_W_L = 3.0
_SIGMA_W_R = math.sqrt(4.5)   # ≈ 2.121
_SIGMA_SO_L = 0.8
_SIGMA_SO_R = 2.5

_LAMBDA_A = 0.50
_LAMBDA_C = 2 / 29             # ≈ 0.069

DEFAULT_RECOVERY = 70.0
_IMBALANCE_THRESHOLD = 50.0


@dataclass
class DayAggregate:
    sleep_h: float = 0.0
    work_h: float = 0.0
    social_h: float = 0.0
    exercise_mpa_h: float = 0.0
    exercise_vpa_h: float = 0.0
    notes: str = ""


@dataclass
class ComponentScores:
    work: float
    social: float
    sleep: float
    exercise: float
    recovery: float


@dataclass
class EWMAResult:
    raw_aw: float    # AW_t uncorrected — lưu DB
    raw_cw: float    # CW_t uncorrected — lưu DB
    acwr: float
    r_burn: float
    alert: str       # green/yellow_overload/yellow_deconditioning/red


# --- Component scoring ---

def _gauss(t: float, mu: float, sigma: float) -> float:
    return 100.0 * math.exp(-((t - mu) ** 2) / (2.0 * sigma ** 2))


def score_sleep(hours: float) -> float:
    if 7.0 <= hours <= 9.0:
        return 100.0
    return _gauss(hours, 7.0, _SIGMA_SL_L) if hours < 7.0 else _gauss(hours, 9.0, _SIGMA_SL_R)


def score_work(hours: float) -> float:
    if 6.0 <= hours <= 8.0:
        return 100.0
    return _gauss(hours, 6.0, _SIGMA_W_L) if hours < 6.0 else _gauss(hours, 8.0, _SIGMA_W_R)


def score_social(hours: float) -> float:
    if 1.0 <= hours <= 3.0:
        return 100.0
    return _gauss(hours, 1.0, _SIGMA_SO_L) if hours < 1.0 else _gauss(hours, 3.0, _SIGMA_SO_R)


def score_exercise(mpa_h: float, vpa_h: float) -> float:
    v_e = 4.0 * mpa_h * 60.0 + 8.0 * vpa_h * 60.0  # hours → minutes → MET-min
    return min(100.0, v_e / 120.0 * 100.0)


def compute_scores(agg: DayAggregate, recovery_score: float) -> ComponentScores:
    return ComponentScores(
        work=round(score_work(agg.work_h), 2),
        social=round(score_social(agg.social_h), 2),
        sleep=round(score_sleep(agg.sleep_h), 2),
        exercise=round(score_exercise(agg.exercise_mpa_h, agg.exercise_vpa_h), 2),
        recovery=round(min(100.0, max(0.0, recovery_score)), 2),
    )


def compute_lbs(scores: ComponentScores) -> float:
    return round(
        _WEIGHTS["work"] * scores.work
        + _WEIGHTS["social"] * scores.social
        + _WEIGHTS["sleep"] * scores.sleep
        + _WEIGHTS["exercise"] * scores.exercise
        + _WEIGHTS["recovery"] * scores.recovery,
        2,
    )


def is_imbalance(scores: ComponentScores) -> bool:
    dims = [scores.work, scores.social, scores.sleep, scores.exercise, scores.recovery]
    return sum(1 for d in dims if d < _IMBALANCE_THRESHOLD) >= 2


# --- Log aggregation ---

def aggregate_logs(logs: list[ActivityLog]) -> DayAggregate:
    agg = DayAggregate()
    notes = []
    for log in logs:
        if log.note:
            notes.append(log.note)
        h = log.duration_hours or 0.0
        t = log.activity_type.value if hasattr(log.activity_type, "value") else log.activity_type
        if t == "sleep":
            agg.sleep_h += h
        elif t == "work":
            agg.work_h += h
        elif t == "social":
            agg.social_h += h
        elif t == "exercise":
            iv = log.intensity.value if (log.intensity and hasattr(log.intensity, "value")) else log.intensity
            if iv == "vigorous":
                agg.exercise_vpa_h += h
            else:
                agg.exercise_mpa_h += h
        # recovery logs contribute only to notes
    agg.notes = "\n".join(notes)
    return agg


# --- EWMA / ACWR ---

def _phi(acwr: float) -> float:
    """Hệ số khuếch đại tải trọng theo vùng thích nghi sinh học."""
    if acwr < 0.8:
        return 1.2
    if acwr <= 1.3:
        return 1.0
    if acwr <= 1.5:
        return 1.0 + 1.5 * (acwr - 1.3)
    return 1.3 + 3.0 * (acwr - 1.5)


def _alert(r_burn: float, acwr: float) -> str:
    if r_burn >= 75.0 or acwr > 1.5:
        return "red"
    if 1.3 < acwr <= 1.5 or 50.0 <= r_burn < 75.0:
        return "yellow_overload"
    if acwr < 0.8:
        return "yellow_deconditioning"
    return "green"


def compute_ewma(wl_t: float, prev_aw: float, prev_cw: float, day_index: int) -> EWMAResult:
    """
    Cập nhật EWMA với WL_t của ngày hiện tại, áp dụng bias correction.
    day_index: số thứ tự ngày tính từ 1 (đếm tất cả ngày đã phân tích của user).
    Trả về EWMAResult với raw_aw/raw_cw để lưu DB.
    """
    raw_aw = _LAMBDA_A * wl_t + (1.0 - _LAMBDA_A) * prev_aw
    raw_cw = _LAMBDA_C * wl_t + (1.0 - _LAMBDA_C) * prev_cw

    div_a = 1.0 - (1.0 - _LAMBDA_A) ** day_index
    div_c = 1.0 - (1.0 - _LAMBDA_C) ** day_index
    aw_corr = raw_aw / div_a
    cw_corr = raw_cw / div_c if div_c > 0 else raw_aw

    acwr = round(aw_corr / cw_corr if cw_corr > 0 else 1.0, 4)
    r_burn = round(min(100.0, aw_corr * _phi(acwr)), 2)

    return EWMAResult(
        raw_aw=round(raw_aw, 4),
        raw_cw=round(raw_cw, 4),
        acwr=acwr,
        r_burn=r_burn,
        alert=_alert(r_burn, acwr),
    )


def burnout_from_stored(raw_aw: float, raw_cw: float, day_index: int) -> EWMAResult:
    """
    Tính ACWR/burnout từ giá trị EWMA đã lưu trong DB (không update EWMA).
    Dùng cho GET /dashboard/overview để hiển thị trạng thái hiện tại.
    """
    div_a = 1.0 - (1.0 - _LAMBDA_A) ** day_index
    div_c = 1.0 - (1.0 - _LAMBDA_C) ** day_index
    aw_corr = raw_aw / div_a if div_a > 0 else raw_aw
    cw_corr = raw_cw / div_c if div_c > 0 else raw_aw

    acwr = round(aw_corr / cw_corr if cw_corr > 0 else 1.0, 4)
    r_burn = round(min(100.0, aw_corr * _phi(acwr)), 2)

    return EWMAResult(
        raw_aw=raw_aw,
        raw_cw=raw_cw,
        acwr=acwr,
        r_burn=r_burn,
        alert=_alert(r_burn, acwr),
    )