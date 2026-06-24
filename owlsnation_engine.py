"""
OWLSNATION ENGINE — CORE MATHEMATICAL ENGINE (V2.0)
==================================================
All float variables are processed via r3().
Phase 7 runs strictly on Score Power + Dominance Index filters.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple


def r3(x: float) -> float:
    """Strict 3-decimal calculator rounding rule."""
    return round(x * 1000) / 1000


# ---------------------------------------------------------------------------
# Phase 1: Efficiency % & Conversion Rates
# ---------------------------------------------------------------------------

@dataclass
class Phase1Result:
    pct_scored: float
    calc_scored: float
    pct_concede: float
    calc_concede: float


def phase1(goals_scored: float, goals_conceded: float,
           shots_on_target_for: float, shots_on_target_against: float) -> Phase1Result:
    pct_scored = r3((goals_scored / max(shots_on_target_for, 0.1)) * 100)
    calc_scored = r3((1 / max(pct_scored, 0.1)) * 100)
    pct_concede = r3((goals_conceded / max(shots_on_target_against, 0.1)) * 100)
    calc_concede = r3((1 / max(pct_concede, 0.1)) * 100)
    return Phase1Result(pct_scored, calc_scored, pct_concede, calc_concede)


# ---------------------------------------------------------------------------
# Phase 2 & 3: Net Score, Score Power, Final Strength
# ---------------------------------------------------------------------------

@dataclass
class Phase23Result:
    net: float
    ratio: float
    power: float
    avg_xg_bc: float
    strength: float


def phase23(g_self: float, c_opp: float, sot_self: float,
            xg_self: float, bc_self: float,
            calc_scored_self: float, calc_concede_opp: float) -> Phase23Result:
    net = r3(calc_scored_self / max(calc_concede_opp, 0.001))
    ratio = r3(g_self / max(c_opp, 0.1))
    power = r3((ratio / max(net, 0.001)) * sot_self)
    avg_xg_bc = r3((xg_self + bc_self) / 2)
    strength = r3(avg_xg_bc * power)
    return Phase23Result(net, ratio, power, avg_xg_bc, strength)


# ---------------------------------------------------------------------------
# Phase 4: Discrete Poisson Distribution Grid -> Baseline Odds
# ---------------------------------------------------------------------------

MAX_SCORE_CAP = 6

def pmf(k: int, lam: float) -> float:
    if lam <= 0: lam = 0.01
    return (lam ** k * math.exp(-lam)) / math.factorial(k)


def poisson_grid(lambda_home: float, lambda_away: float, cap: int = MAX_SCORE_CAP) -> List[List[float]]:
    grid = []
    for h in range(cap + 1):
        row = [pmf(h, lambda_home) * pmf(a, lambda_away) for a in range(cap + 1)]
        grid.append(row)
    return grid


def normalize_grid(grid: List[List[float]]) -> List[List[float]]:
    total = sum(sum(row) for row in grid)
    return [[v / (total if total > 0 else 1) for v in row] for row in grid]


def outcome_sums(grid: List[List[float]]) -> Tuple[float, float, float]:
    home = draw = away = 0.0
    for h, row in enumerate(grid):
        for a, p in enumerate(row):
            if h > a: home += p
            elif h == a: draw += p
            else: away += p
    return home, draw, away


def to_pct(home: float, draw: float, away: float) -> Dict[str, float]:
    total = home + draw + away
    if total == 0: total = 1
    return {"h": r3(home / total * 100), "d": r3(draw / total * 100), "a": r3(away / total * 100)}


def odds_from_pct(pct: Dict[str, float]) -> Dict[str, float]:
    return {
        "oh": r3(100 / max(pct["h"], 0.001)),
        "od": r3(100 / max(pct["d"], 0.001)),
        "oa": r3(100 / max(pct["a"], 0.001)),
    }


# ---------------------------------------------------------------------------
# Phase 5: 5-Odds Stress Matrix -> Separate Dominance Index
# ---------------------------------------------------------------------------

W_TAC, W_HUM, W_ENV, W_MKT = 0.6, 0.5, 0.4, 0.3
SIGMA = r3(W_TAC * W_HUM * W_ENV * W_MKT)
DRAG = r3(100 * SIGMA)


def renormalize(h: float, d: float, a: float) -> Dict[str, float]:
    total = h + d + a
    if total == 0: total = 1
    return {"h": r3(h / total * 100), "d": r3(d / total * 100), "a": r3(a / total * 100)}


def stress_state(base: Dict[str, float], target: str) -> Dict[str, float]:
    h, d, a = base["h"], base["d"], base["a"]
    if target == "home": h = r3((h + 50) - DRAG)
    elif target == "away": a = r3((a + 50) - DRAG)
    elif target == "draw": d = r3((d + 50) - DRAG)
    elif target == "all":
        h = r3((h + 50) - DRAG)
        d = r3((d + 50) - DRAG)
        a = r3((a + 50) - DRAG)
    return renormalize(h, d, a)


def build_five_states(base_pct: Dict[str, float]) -> List[Dict[str, float]]:
    return [dict(base_pct), stress_state(base_pct, "home"), stress_state(base_pct, "away"),
            stress_state(base_pct, "draw"), stress_state(base_pct, "all")]


def implied_probs(states: List[Dict[str, float]]) -> List[Dict[str, float]]:
    out = []
    for s in states:
        o = odds_from_pct(s)
        out.append({"h": r3(1 / o["oh"]), "d": r3(1 / o["od"]), "a": r3(1 / o["oa"])})
    return out


def dominance_index(implied: List[Dict[str, float]], side: str) -> float:
    baseline = implied[0][side]
    total = 0.0
    for state in implied[1:]:
        total = r3(total + r3(state[side] - baseline))
    return total


# ---------------------------------------------------------------------------
# Phase 6: Ensemble Master Odds & Bookmaker Comparisons
# ---------------------------------------------------------------------------

def master_pct_from_states(states: List[Dict[str, float]]) -> Dict[str, float]:
    return {
        "h": r3(sum(s["h"] for s in states) / 5),
        "d": r3(sum(s["d"] for s in states) / 5),
        "a": r3(sum(s["a"] for s in states) / 5),
    }


def bookmaker_normalized_pct(bk_h: float, bk_d: float, bk_a: float) -> Dict[str, float]:
    implied = {"h": 1 / bk_h, "d": 1 / bk_d, "a": 1 / bk_a}
    total = implied["h"] + implied["d"] + implied["a"]
    return {"h": r3(implied["h"] / total * 100), "d": r3(implied["d"] / total * 100), "a": r3(implied["a"] / total * 100)}


def value_margin(master_pct: Dict[str, float], bk_pct: Dict[str, float]) -> Dict[str, float]:
    return {"h": r3(master_pct["h"] - bk_pct["h"]), "d": r3(master_pct["d"] - bk_pct["d"]), "a": r3(master_pct["a"] - bk_pct["a"])}


# ---------------------------------------------------------------------------
# Phase 7: Score Power Baseline & Dominance Filter Grid (THE FIX)
# ---------------------------------------------------------------------------

def dom_adj_factor(dom: float) -> float:
    return 1 + 0.4 * math.tanh(dom / 0.3)


@dataclass
class DynamicGridResult:
    lambda_home: float
    lambda_away: float
    draw_diff_pct: float
    model_consensus_draw_pct: float
    grid: List[List[float]]
    outcome_pct: Dict[str, float]


def build_scorepower_dominance_grid(sp_home: float, sp_away: float,
                                    dom_home: float, dom_away: float,
                                    base_draw_pct: float, master_draw_pct: float,
                                    bookmaker_draw_pct: float) -> DynamicGridResult:
    # 1. Base the initial goals baseline expectation strictly on calculated Score Powers
    base_lambda_home = r3(math.sqrt(max(sp_home, 0.1)) * 1.2)
    base_lambda_away = r3(math.sqrt(max(sp_away, 0.1)) * 1.2)

    # 2. Refine the baseline targets using the Dominance Index shifts
    lambda_home = r3(min(base_lambda_home * dom_adj_factor(dom_home), 6.0))
    lambda_away = r3(min(base_lambda_away * dom_adj_factor(dom_away), 6.0))

    raw_grid = poisson_grid(max(lambda_home, 0.05), max(lambda_away, 0.05))
    grid = normalize_grid(raw_grid)
    n = len(grid)

    # 3. Apply the 3-Way Draw Variance adjustment
    model_consensus_draw_pct = r3((base_draw_pct + master_draw_pct) / 2)
    draw_diff_pct = r3(bookmaker_draw_pct - model_consensus_draw_pct)

    diag_sum = sum(grid[i][i] for i in range(n))
    off_sum = sum(grid[h][a] for h in range(n) for a in range(n) if h != a)

    new_diag_frac = min(max(diag_sum * 100 + draw_diff_pct, 0.001), 99.999) / 100
    new_off_frac = 1 - new_diag_frac
    diag_scale = new_diag_frac / diag_sum if diag_sum > 0 else 0.0
    off_scale = new_off_frac / off_sum if off_sum > 0 else 0.0

    final_grid = [[grid[h][a] * (diag_scale if h == a else off_scale) for a in range(n)] for h in range(n)]

    home_pct = sum(final_grid[h][a] for h in range(n) for a in range(n) if h > a) * 100
    draw_pct = sum(final_grid[i][i] for i in range(n)) * 100
    away_pct = sum(final_grid[h][a] for h in range(n) for a in range(n) if a > h) * 100

    return DynamicGridResult(lambda_home, lambda_away, draw_diff_pct, model_consensus_draw_pct, final_grid, {"h": home_pct, "d": draw_pct, "a": away_pct})


@dataclass
class MarketCandidate:
    name: str
    prob: float


def generate_v2_markets(dg: DynamicGridResult, top_scores: List[Tuple[int, int, float]]) -> List[MarketCandidate]:
    top_total_p = sum(p for _, _, p in top_scores)
    under_weight = sum(p for h, a, p in top_scores if h + a <= 2)
    btts_yes_weight = sum(p for h, a, p in top_scores if h >= 1 and a >= 1)
    
    under_pct = r3((under_weight / top_total_p) * 100) if top_total_p > 0 else 50.0
    over_pct = r3(100 - under_pct)
    btts_yes_pct = r3((btts_yes_weight / top_total_p) * 100) if top_total_p > 0 else 50.0
    btts_no_pct = r3(100 - btts_yes_pct)

    btts_name = "BTTS — Yes" if btts_yes_pct >= btts_no_pct else "BTTS — No"
    btts_prob = max(btts_yes_pct, btts_no_pct)

    goals_name = "Under 2.5 Goals" if under_pct >= over_pct else "Over 2.5 Goals"
    goals_prob = max(under_pct, over_pct)

    dc12_prob = r3(dg.outcome_pct["h"] + dg.outcome_pct["a"])

    candidates = [
        MarketCandidate(btts_name, btts_prob),
        MarketCandidate(goals_name, goals_prob),
        MarketCandidate("Double Chance (12) — No Draw", dc12_prob)
    ]
    candidates.sort(key=lambda c: c.prob, reverse=True)
    return candidates


def get_top_scores(grid: List[List[float]], top_n: int = 3) -> List[Tuple[int, int, float]]:
    n = len(grid)
    flat = [(h, a, grid[h][a]) for h in range(n) for a in range(n)]
    flat.sort(key=lambda x: x[2], reverse=True)
    return flat[:top_n]


@dataclass
class TeamStats:
    name: str
    goals_scored: float
    goals_conceded: float
    shots_on_target_for: float
    shots_on_target_against: float
    big_chances: float
    expected_goals: float


@dataclass
class EngineResult:
    sp_home: float
    sp_away: float
    strength_home: float
    strength_away: float
    baseline_pct: Dict[str, float]
    baseline_odds: Dict[str, float]
    dominance_home: float
    dominance_away: float
    master_pct: Dict[str, float]
    master_odds: Dict[str, float]
    bookmaker_pct: Dict[str, float]
    value_margin: Dict[str, float]
    model_consensus_draw_pct: float
    draw_diff_pct: float
    lambda_home: float
    lambda_away: float
    top_markets: List[MarketCandidate]
    top_scores: List[Tuple[int, int, float]]


def run_engine(team_a: TeamStats, team_b: TeamStats, bk_h: float, bk_d: float, bk_a: float) -> EngineResult:
    p1a = phase1(team_a.goals_scored, team_a.goals_conceded, team_a.shots_on_target_for, team_a.shots_on_target_against)
    p1b = phase1(team_b.goals_scored, team_b.goals_conceded, team_b.shots_on_target_for, team_b.shots_on_target_against)

    p23a = phase23(team_a.goals_scored, team_b.goals_conceded, team_a.shots_on_target_for, team_a.expected_goals, team_a.big_chances, p1a.calc_scored, p1b.calc_concede)
    p23b = phase23(team_b.goals_scored, team_a.goals_conceded, team_b.shots_on_target_for, team_b.expected_goals, team_b.big_chances, p1b.calc_scored, p1a.calc_concede)

    grid = poisson_grid(p23a.strength, p23b.strength)
    h_sum, d_sum, a_sum = outcome_sums(grid)
    base_pct = to_pct(h_sum, d_sum, a_sum)
    base_odds = odds_from_pct(base_pct)

    states = build_five_states(base_pct)
    implied = implied_probs(states)
    dom_home = dominance_index(implied, "h")
    dom_away = dominance_index(implied, "a")

    master_pct = master_pct_from_states(states)
    master_odds = odds_from_pct(master_pct)
    bk_pct = bookmaker_normalized_pct(bk_h, bk_d, bk_a)
    margin = value_margin(master_pct, bk_pct)

    dg = build_scorepower_dominance_grid(p23a.power, p23b.power, dom_home, dom_away, base_pct["d"], master_pct["d"], bk_pct["d"])
    scores = get_top_scores(dg.grid)
    markets = generate_v2_markets(dg, scores)

    return EngineResult(
        sp_home=p23a.power, sp_away=p23b.power, strength_home=p23a.strength, strength_away=p23b.strength,
        baseline_pct=base_pct, baseline_odds=base_odds, dominance_home=dom_home, dominance_away=dom_away,
        master_pct=master_pct, master_odds=master_odds, bookmaker_pct=bk_pct, value_margin=margin,
        model_consensus_draw_pct=dg.model_consensus_draw_pct, draw_diff_pct=dg.draw_diff_pct,
        lambda_home=dg.lambda_home, lambda_away=dg.lambda_away, top_markets=markets[:2], top_scores=scores
    )
