"""
Economics: Preference → Utility → Strategic Interaction
========================================================

Layer 1  Preference  — 对结果的排序关系（完备性、传递性）
Layer 2  Utility     — 用数字表示偏好（效用函数、无差异曲线、最优选择）
Layer 3  Strategic   — 多主体互动（博弈论、纳什均衡）
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless environment — saves to file
import matplotlib.pyplot as plt
from itertools import product as iproduct


# ================================================================
# LAYER 1 — PREFERENCE RELATION
# ================================================================

class PreferenceRelation:
    """
    Ordinal ranking over bundles (x, y).

    Internally backed by a utility function, but only exposes
    pairwise comparisons — mirroring the axiomatic foundation:
      ≿  weak preference  (weakly_prefers)
      ≻  strict preference (strictly_prefers)
      ~  indifference     (indifferent)
    """

    def __init__(self, utility_fn):
        self._u = utility_fn

    def weakly_prefers(self, a, b):
        return self._u(a) >= self._u(b)

    def strictly_prefers(self, a, b):
        return self._u(a) > self._u(b)

    def indifferent(self, a, b):
        return np.isclose(self._u(a), self._u(b), rtol=1e-6)

    def is_complete(self, bundles):
        """∀ a,b: a≿b or b≿a"""
        return all(
            self.weakly_prefers(a, b) or self.weakly_prefers(b, a)
            for a, b in iproduct(bundles, repeat=2)
        )

    def is_transitive(self, bundles):
        """∀ a,b,c: a≿b and b≿c ⟹ a≿c"""
        return all(
            not (self.weakly_prefers(a, b) and self.weakly_prefers(b, c))
            or self.weakly_prefers(a, c)
            for a, b, c in iproduct(bundles, repeat=3)
        )


# ================================================================
# LAYER 2 — UTILITY FUNCTION (Cobb-Douglas)
# ================================================================

class CobbDouglasUtility:
    """
    U(x, y) = x^alpha * y^beta

    Most common utility form in micro — captures diminishing
    marginal utility and substitutability between goods.
    """

    def __init__(self, alpha=0.5, beta=0.5):
        self.alpha = alpha
        self.beta  = beta

    def __call__(self, bundle):
        x, y = bundle
        return (x ** self.alpha) * (y ** self.beta)

    def indifference_curve(self, u_level, x_range=(0.05, 6)):
        """y = (U / x^alpha)^(1/beta)"""
        x = np.linspace(x_range[0], x_range[1], 400)
        with np.errstate(divide='ignore', invalid='ignore'):
            y = (u_level / (x ** self.alpha)) ** (1.0 / self.beta)
        return x, y

    def maximize(self, income, px, py):
        """
        Interior optimum from Lagrangian:
          x* = (alpha / alpha+beta) * I / px
          y* = (beta  / alpha+beta) * I / py
        """
        share = self.alpha + self.beta
        x_star = (self.alpha / share) * income / px
        y_star = (self.beta  / share) * income / py
        return x_star, y_star


# ================================================================
# LAYER 3 — NORMAL FORM GAME
# ================================================================

class NormalFormGame:
    """
    Two-player, finite strategy normal-form game.

    payoffs[i][j] = (payoff_player1, payoff_player2)
    """

    def __init__(self, strategies1, strategies2, payoffs, name="Game"):
        self.s1       = strategies1
        self.s2       = strategies2
        self.payoffs  = payoffs        # list[list[(int,int)]]
        self.name     = name

    # ---- solution concepts ----------------------------------------

    def best_responses(self):
        """
        Returns BR1[j] = set of i that maximise P1's payoff when P2 plays j,
                BR2[i] = set of j that maximise P2's payoff when P1 plays i.
        """
        n1, n2 = len(self.s1), len(self.s2)
        BR1 = {}
        for j in range(n2):
            max_p = max(self.payoffs[i][j][0] for i in range(n1))
            BR1[j] = {i for i in range(n1) if self.payoffs[i][j][0] == max_p}
        BR2 = {}
        for i in range(n1):
            max_p = max(self.payoffs[i][j][1] for j in range(n2))
            BR2[i] = {j for j in range(n2) if self.payoffs[i][j][1] == max_p}
        return BR1, BR2

    def nash_equilibria(self):
        """Pure-strategy Nash Equilibria: mutual best responses."""
        BR1, BR2 = self.best_responses()
        result = []
        for i in range(len(self.s1)):
            for j in range(len(self.s2)):
                if i in BR1[j] and j in BR2[i]:
                    p1, p2 = self.payoffs[i][j]
                    result.append((self.s1[i], self.s2[j], p1, p2))
        return result

    def dominant_strategies(self):
        """Strictly dominant strategy for each player (if one exists)."""
        n1, n2 = len(self.s1), len(self.s2)
        dom = {}
        for i in range(n1):
            if all(
                self.payoffs[i][j][0] > self.payoffs[i2][j][0]
                for j in range(n2) for i2 in range(n1) if i2 != i
            ):
                dom["player1"] = self.s1[i]
        for j in range(n2):
            if all(
                self.payoffs[i][j][1] > self.payoffs[i][j2][1]
                for i in range(n1) for j2 in range(n2) if j2 != j
            ):
                dom["player2"] = self.s2[j]
        return dom

    # ---- display --------------------------------------------------

    def print_matrix(self):
        nash_set = {(s1, s2) for s1, s2, _, _ in self.nash_equilibria()}
        n2 = len(self.s2)
        width = 14
        print(f"\n{'='*55}")
        print(f"  {self.name}")
        print(f"{'='*55}")
        header = f"{'':>14}" + "".join(f"{s:^{width}}" for s in self.s2)
        print(header)
        print(f"{'':>14}" + "-" * (width * n2))
        for i, s1 in enumerate(self.s1):
            row = f"{s1:>14} |"
            for j, s2 in enumerate(self.s2):
                p1, p2 = self.payoffs[i][j]
                mark = " ★" if (s1, s2) in nash_set else "  "
                row += f"  ({p1:+d},{p2:+d}){mark}   "
            print(row)
        print()


# ================================================================
# VISUALIZATION — ASCII terminal output
# ================================================================

def ascii_plot(u_fn):

    def section(title):
        bar = "─" * 62
        print(f"\n┌{bar}┐")
        print(f"│  {title:<60}│")
        print(f"└{bar}┘")

    # ----------------------------------------------------------
    # Panel 1: Preference — 2D scatter grid
    # ----------------------------------------------------------
    section("Layer 1 — Preferences  (ordinal ranking & indifference)")

    bundles = [(1, 4), (2, 2), (4, 1), (3, 3), (1, 1)]
    labels  = ["A",    "B",    "C",    "D",    "E"]
    utils   = [u_fn(b) for b in bundles]
    ranked  = sorted(zip(utils, labels, bundles), reverse=True)

    GW, GH = 38, 11
    grid = [["·"] * GW for _ in range(GH)]
    for lbl, (bx, by) in zip(labels, bundles):
        col = min(GW - 1, round((bx / 5.0) * (GW - 1)))
        row = min(GH - 1, GH - 1 - round((by / 5.0) * (GH - 1)))
        grid[row][col] = lbl

    print(f"\n  Good Y")
    for r in range(GH):
        y_val = 5.0 * (GH - 1 - r) / (GH - 1)
        lbl_y = f"{y_val:.0f}" if r % (GH // 5) == 0 else " "
        rank_idx = r - 1
        rank_str = ""
        if 0 <= rank_idx < len(ranked):
            u, lb, b = ranked[rank_idx]
            rank_str = f"  {rank_idx+1}. {lb}={b}  U={u:.2f}"
        print(f"  {lbl_y:1s} │{''.join(grid[r])}{rank_str}")
    print(f"    └" + "─" * GW)
    print(f"      0        1        2        3        4        5  Good X")
    print(f"\n  A~B~C all have U=2.00 → same indifference curve")
    print(f"  D has U=3.00 (higher curve) ;  E has U=1.00 (lower curve)")

    # ----------------------------------------------------------
    # Panel 2: Utility — indifference curves + budget + optimum
    # ----------------------------------------------------------
    section("Layer 2 — Utility Function  U(x,y) = √x · √y")

    GW2, GH2 = 50, 16
    x_max, y_max = 5.5, 5.5
    u_levels = [1.0, 1.5, 2.0, 2.5, 3.0]
    u_chars  = ["1",  "2",  "3",  "4",  "5"]

    grid2 = [[" "] * GW2 for _ in range(GH2)]
    for ri in range(GH2):
        for ci in range(GW2):
            x = 0.15 + (ci / (GW2 - 1)) * x_max
            y = y_max - (ri / (GH2 - 1)) * y_max
            if x <= 0 or y <= 0:
                continue
            u = u_fn((x, y))
            for lv, ch in zip(u_levels, u_chars):
                if abs(u - lv) / lv < 0.07:
                    grid2[ri][ci] = ch
                    break
            # budget line x+y=6
            if abs(x + y - 6.0) < 0.13 and 0.2 < x < 5.9 and 0.2 < y < 5.9:
                grid2[ri][ci] = "/"
    # optimal point (3, 3)
    oc = round((3.0 / x_max) * (GW2 - 1))
    or_ = round(((y_max - 3.0) / y_max) * (GH2 - 1))
    grid2[or_][oc] = "★"

    print(f"\n  Curves: 1=U1.0  2=U1.5  3=U2.0  4=U2.5  5=U3.0")
    print(f"  /=budget line (I=6, px=py=1)   ★=optimum (3,3) U=3.00\n")
    print(f"  Good Y")
    for ri in range(GH2):
        y_val = y_max - (ri / (GH2 - 1)) * y_max
        lbl_y = f"{y_val:.1f}" if ri % 4 == 0 else "    "
        print(f"  {lbl_y:4s} │{''.join(grid2[ri])}")
    print(f"        └" + "─" * GW2)
    print(f"         0" + "".join(f"{'':>8}{v:.0f}" for v in [1, 2, 3, 4, 5]) + "  Good X")
    print(f"\n  Budget tangent to curve '5' at ★ → optimal split x*=3, y*=3")

    # ----------------------------------------------------------
    # Panel 3: Games — printed via NormalFormGame.print_matrix()
    # ----------------------------------------------------------
    section("Layer 3 — Strategic Interaction  (★ = Nash Equilibrium)")


# ================================================================
# MAIN — text walkthrough
# ================================================================

def main():
    SEP = "=" * 60

    print(SEP)
    print("  ECONOMICS: Preference → Utility → Strategic Interaction")
    print(SEP)

    u_fn = CobbDouglasUtility(alpha=0.5, beta=0.5)

    # ---- Layer 1 ------------------------------------------------
    print("\n[LAYER 1]  Preference Relations")
    print("-" * 40)

    bundles = [(1, 4), (2, 2), (4, 1), (3, 3), (1, 1)]
    labels  = ["A",    "B",    "C",    "D",    "E"]
    pref    = PreferenceRelation(u_fn)

    print("Bundles (good X, good Y)  →  U(x,y) = √x·√y")
    for lbl, b in zip(labels, bundles):
        print(f"  {lbl} = {b}   U = {u_fn(b):.4f}")

    print("\nPairwise comparisons:")
    print(f"  A ≻ E?  {pref.strictly_prefers((1,4),(1,1))}    (U_A={u_fn((1,4)):.2f} > U_E={u_fn((1,1)):.2f})")
    print(f"  A ~ B?  {pref.indifferent((1,4),(2,2))}    (both U=2.00 — on same indiff. curve)")
    print(f"  D ≻ B?  {pref.strictly_prefers((3,3),(2,2))}    (U_D={u_fn((3,3)):.2f} > U_B={u_fn((2,2)):.2f})")

    print("\nAxiom verification (over 5 bundles):")
    print(f"  Completeness : {pref.is_complete(bundles)}")
    print(f"  Transitivity : {pref.is_transitive(bundles)}")

    print("\nKey insight: preferences are ORDINAL — only ranking matters,")
    print("not the absolute numbers. That's where utility functions come in.")

    # ---- Layer 2 ------------------------------------------------
    print(f"\n{'='*60}")
    print("[LAYER 2]  Utility Function & Consumer Optimum")
    print("-" * 40)
    print("U(x, y) = x^0.5 · y^0.5   (symmetric Cobb-Douglas)")
    print("Budget:   1·x + 1·y = 6   (income I=6, prices px=py=1)\n")

    x_star, y_star = u_fn.maximize(income=6, px=1, py=1)
    u_star = u_fn((x_star, y_star))

    print(f"  Lagrangian solution →  x* = {x_star:.2f},  y* = {y_star:.2f}")
    print(f"  Maximum utility     →  U* = {u_star:.4f}")
    print(f"  Equal split because α = β = 0.5 (symmetric tastes)")
    print(f"  MRS = MRT at optimum: (α/β)·(y/x) = (px/py)  →  y*/x* = 1  ✓")

    # ---- Layer 3 ------------------------------------------------
    print(f"\n{'='*60}")
    print("[LAYER 3]  Strategic Interaction — Game Theory")
    print("-" * 40)
    print("Now add a SECOND agent. Each has their own utility.")
    print("Outcomes depend on BOTH players' choices → strategic thinking.\n")

    # Prisoner's Dilemma
    pd = NormalFormGame(
        strategies1=["Cooperate", "Defect"],
        strategies2=["Cooperate", "Defect"],
        payoffs=[
            [(-1, -1), (-3,  0)],
            [( 0, -3), (-2, -2)],
        ],
        name="Prisoner's Dilemma"
    )
    pd.print_matrix()
    ne = pd.nash_equilibria()
    dom = pd.dominant_strategies()
    print(f"  Nash Equilibria     : {[(s1, s2) for s1, s2, *_ in ne]}")
    print(f"  Dominant strategies : {dom}")
    print("  Insight: Defect dominates for BOTH players individually.")
    print("  Result: (Defect, Defect) — collectively worse than (Coop, Coop)!")
    print("  This is the tragedy of the commons / social dilemma.")

    # Battle of the Sexes
    bos = NormalFormGame(
        strategies1=["Opera", "Football"],
        strategies2=["Opera", "Football"],
        payoffs=[
            [(2, 1), (0, 0)],
            [(0, 0), (1, 2)],
        ],
        name="Battle of the Sexes"
    )
    bos.print_matrix()
    ne2 = bos.nash_equilibria()
    print(f"  Nash Equilibria     : {[(s1, s2) for s1, s2, *_ in ne2]}")
    print("  Insight: Multiple equilibria — both players prefer to coordinate,")
    print("  but disagree on WHERE. Requires focal points or communication.")

    # ---- Connecting the layers ----------------------------------
    print(f"\n{'='*60}")
    print("CONNECTION: Preference → Utility → Strategic Interaction")
    print("-" * 40)
    print("""
  1. PREFERENCE defines what each agent wants (axiomatic)
     Completeness + Transitivity ⟹ rational ordering

  2. UTILITY represents that preference numerically
     Enables calculus: maximise U(x,y) s.t. budget constraint
     → Marshallian demand, indifference curves, welfare analysis

  3. STRATEGIC INTERACTION adds OTHER agents with their own U
     Each agent maximises their OWN utility, knowing others do too
     → Nash Equilibrium: no unilateral deviation is profitable
     → Emergent phenomena: coordination failures, social dilemmas
    """)

    # ---- ASCII Visualization ------------------------------------
    ascii_plot(u_fn)


if __name__ == "__main__":
    main()
