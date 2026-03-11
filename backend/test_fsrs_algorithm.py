"""
FSRS Algorithm Validation Script
Run from the backend/ directory:  python test_fsrs_algorithm.py

Tests:
  1. FSRSAlgorithm — initial_stability, initial_difficulty, next_interval
  2. FSRSAlgorithm.review() — step-by-step trace for a 10-card sequence
  3. compute_fsrs_rating — all four rating branches
  4. Side-by-side SM-2 vs FSRS interval comparison (all-correct run)
"""

import sys
import math
sys.path.insert(0, ".")

from app.spaced.algorithms import FSRSAlgorithm, compute_fsrs_rating, SM2Algorithm

PASS = "PASS"
FAIL = "FAIL"
results = []


def check(label: str, condition: bool) -> None:
    tag = PASS if condition else FAIL
    results.append((tag, label))
    print(f"  [{tag}] {label}")


# ─────────────────────────────────────────────────────────────
# 1. FSRSAlgorithm — initial state
# ─────────────────────────────────────────────────────────────
print("\n=== 1. Initial stability & difficulty ===")
fsrs = FSRSAlgorithm()

for rating, expected_s in [(1, fsrs.w[0]), (2, fsrs.w[1]),
                            (3, fsrs.w[2]), (4, fsrs.w[3])]:
    s = fsrs.initial_stability(rating)
    check(f"initial_stability(rating={rating}) == w[{rating-1}]={expected_s:.4f}",
          math.isclose(s, expected_s, rel_tol=1e-9))

for rating in [1, 2, 3, 4]:
    d = fsrs.initial_difficulty(rating)
    expected = min(max(fsrs.w[4] - (rating - 3) * fsrs.w[5], 1.0), 10.0)
    check(f"initial_difficulty(rating={rating}) = {d:.4f} (expected {expected:.4f})",
          math.isclose(d, expected, rel_tol=1e-9))
    check(f"initial_difficulty(rating={rating}) clamped [1,10]", 1.0 <= d <= 10.0)

# ─────────────────────────────────────────────────────────────
# 2. next_interval — verify formula t = 9S*(1/R - 1)
# ─────────────────────────────────────────────────────────────
print("\n=== 2. next_interval correctness ===")
for s, r, label in [(1.0, 0.9, "S=1 R=0.9"), (10.0, 0.9, "S=10 R=0.9"),
                    (1.0, 0.8, "S=1 R=0.8"), (50.0, 0.9, "S=50 R=0.9")]:
    fsrs_r = FSRSAlgorithm(desired_retention=r)
    interval = fsrs_r.next_interval(s)
    expected_raw = 9.0 * s * (1.0 / r - 1.0)
    expected = min(max(1, round(expected_raw)), 365)
    check(f"next_interval({label}) = {interval} days (expected {expected})",
          interval == expected)

# Verify the old -1/3 bug is gone: at S=10, R=0.9 it must NOT equal the wrong value
wrong = round((9 * 10) * (0.9 ** (-1/3) - 1))
correct = round(9 * 10 * (1 / 0.9 - 1))
interval_10 = FSRSAlgorithm(desired_retention=0.9).next_interval(10.0)
check(f"next_interval(S=10) = {interval_10}, NOT the old bug value {wrong}",
      interval_10 != wrong and interval_10 == correct)

# ─────────────────────────────────────────────────────────────
# 3. compute_fsrs_rating
# ─────────────────────────────────────────────────────────────
print("\n=== 3. compute_fsrs_rating ===")
check("Wrong answer → 1 (Again)",         compute_fsrs_rating(False, 1000) == 1)
check("Wrong + slow → 1 (Again)",         compute_fsrs_rating(False, 9000) == 1)
check("Correct + fast (1s) → 4 (Easy)",   compute_fsrs_rating(True,  1000) == 4)
check("Correct + fast (2999ms) → 4",      compute_fsrs_rating(True,  2999) == 4)
check("Correct + normal (3000ms) → 3",    compute_fsrs_rating(True,  3000) == 3)
check("Correct + normal (8000ms) → 3",    compute_fsrs_rating(True,  8000) == 3)
check("Correct + slow (8001ms) → 2 (Hard)", compute_fsrs_rating(True, 8001) == 2)
check("Correct + very slow (15s) → 2",    compute_fsrs_rating(True, 15000) == 2)

# Custom thresholds
check("Custom thresholds respected",
      compute_fsrs_rating(True, 500, fast_threshold_ms=1000, slow_threshold_ms=2000) == 4)
check("Custom slow threshold",
      compute_fsrs_rating(True, 2500, fast_threshold_ms=1000, slow_threshold_ms=2000) == 2)

# ─────────────────────────────────────────────────────────────
# 4. Step-by-step trace — mixed correct/wrong sequence
# ─────────────────────────────────────────────────────────────
print("\n=== 4. Step-by-step FSRS trace (10 answers) ===")
RATINGS = [3, 3, 1, 3, 4, 3, 2, 4, 4, 3]  # mixed: Good/Good/Again/Good/Easy/...
LABELS  = ["Good","Good","Again","Good","Easy","Good","Hard","Easy","Easy","Good"]
fsrs = FSRSAlgorithm(desired_retention=0.9)
s = fsrs.initial_stability(3)
d = fsrs.initial_difficulty(3)
elapsed = 0.0
print(f"  {'#':<3} {'Rating':<8} {'S':>7} {'D':>6} {'R':>6} {'Interval':>10}")
print(f"  {'-'*3} {'-'*8} {'-'*7} {'-'*6} {'-'*6} {'-'*10}")
print(f"  {'0':<3} {'(init)':<8} {s:>7.3f} {d:>6.3f} {'—':>6} {'—':>10}")
for i, (rating, label) in enumerate(zip(RATINGS, LABELS), 1):
    r = fsrs.calculate_retrievability(elapsed, s)
    s, d, interval = fsrs.review(s, d, elapsed, rating)
    print(f"  {i:<3} {label:<8} {s:>7.3f} {d:>6.3f} {r:>6.3f} {interval:>9}d")
    elapsed = float(interval)

check("Trace completed without error", True)
check("Stability > 0 after all reviews", s > 0)
check("Difficulty in [1, 10] after all reviews", 1.0 <= d <= 10.0)

# ─────────────────────────────────────────────────────────────
# 5. SM-2 vs FSRS side-by-side (all Easy / quality-5 run)
# ─────────────────────────────────────────────────────────────
print("\n=== 5. SM-2 vs FSRS — all-correct run (8 reviews) ===")
print(f"  {'Review':<8} {'SM-2 interval':>14} {'FSRS interval':>14}")
print(f"  {'-'*8} {'-'*14} {'-'*14}")

sm2 = SM2Algorithm()
sm2_ef = 2.5
sm2_rep = 0
sm2_prev = 1

fsrs2 = FSRSAlgorithm(desired_retention=0.9)
f_s = fsrs2.initial_stability(4)   # Easy
f_d = fsrs2.initial_difficulty(4)
f_elapsed = 0.0

for i in range(1, 9):
    sm2_interval, sm2_ef, sm2_rep = sm2.calculate_next_interval(
        ease_factor=sm2_ef, repetition=sm2_rep, was_correct=True,
        previous_interval=sm2_prev, response_quality=5
    )
    sm2_prev = sm2_interval

    f_s, f_d, f_interval = fsrs2.review(f_s, f_d, f_elapsed, rating=4)
    f_elapsed = float(f_interval)

    print(f"  {i:<8} {sm2_interval:>13}d {f_interval:>13}d")

check("SM-2 vs FSRS comparison printed", True)

# ─────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────
passed = sum(1 for t, _ in results if t == PASS)
failed = sum(1 for t, _ in results if t == FAIL)
print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed out of {len(results)} checks")
if failed:
    print("\nFailed checks:")
    for tag, label in results:
        if tag == FAIL:
            print(f"  ✗ {label}")
    sys.exit(1)
else:
    print("All checks passed ✓")
