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
# VISUALIZATION — 3 panels
# ================================================================

def plot_economics(u_fn, output="economics_journey.png"):
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle(
        "Preference  →  Utility  →  Strategic Interaction",
        fontsize=15, fontweight="bold", y=1.01
    )

    # ----------------------------------------------------------
    # Panel 1: Preference as ordinal ranking
    # ----------------------------------------------------------
    ax = axes[0]
    # choose bundles so some are indifferent (same Cobb-Douglas U)
    bundles = [(1, 4), (2, 2), (4, 1), (3, 3), (1, 1)]
    labels  = ["A",    "B",    "C",    "D",    "E"]
    utils   = [u_fn(b) for b in bundles]

    norm_u  = np.array(utils) / max(utils)
    colors  = plt.cm.RdYlGn(norm_u)

    xs = [b[0] for b in bundles]
    ys = [b[1] for b in bundles]
    ax.scatter(xs, ys, c=colors, s=220, zorder=5, edgecolors="k", linewidths=0.8)

    for lbl, (x, y), u in zip(labels, bundles, utils):
        ax.annotate(
            f"{lbl}  U={u:.2f}", (x, y),
            textcoords="offset points", xytext=(8, 6), fontsize=9
        )

    # annotate the indifference: A~B~C (all U=2.0 when alpha=beta=0.5)
    ax.annotate(
        "A ~ B ~ C\n(same utility)", xy=(2, 2),
        xytext=(0.3, 3.5), fontsize=8.5, color="steelblue",
        arrowprops=dict(arrowstyle="->", color="steelblue", lw=0.8)
    )

    ax.set_xlim(0, 5); ax.set_ylim(0, 5)
    ax.set_xlabel("Good X", fontsize=11); ax.set_ylabel("Good Y", fontsize=11)
    ax.set_title("Layer 1 — Preferences\nordinal ranking & indifference", fontsize=11)
    ax.grid(True, alpha=0.3)

    # ----------------------------------------------------------
    # Panel 2: Utility — indifference curves & optimum
    # ----------------------------------------------------------
    ax = axes[1]
    u_levels = [1.0, 1.5, 2.0, 2.5, 3.0]
    palette  = plt.cm.Blues(np.linspace(0.35, 0.85, len(u_levels)))

    for u_lv, color in zip(u_levels, palette):
        x, y = u_fn.indifference_curve(u_lv)
        mask = (y > 0.05) & (y < 5.5)
        ax.plot(x[mask], y[mask], color=color, lw=2, label=f"U = {u_lv}")

    # Budget line: I=6, px=py=1
    income, px, py = 6, 1, 1
    x_b = np.array([0, income / px])
    ax.plot(x_b, income / py - (py / px) * x_b, "r--", lw=1.8, alpha=0.8,
            label=f"Budget (I={income})")

    x_star, y_star = u_fn.maximize(income, px, py)
    u_star = u_fn((x_star, y_star))
    ax.scatter([x_star], [y_star], color="red", s=160, zorder=6,
               label=f"Optimum ({x_star:.1f}, {y_star:.1f})\nU={u_star:.2f}")

    ax.set_xlim(0, 5.5); ax.set_ylim(0, 5.5)
    ax.set_xlabel("Good X", fontsize=11); ax.set_ylabel("Good Y", fontsize=11)
    ax.set_title("Layer 2 — Utility Function\nCobb-Douglas U(x,y)=√x·√y", fontsize=11)
    ax.legend(fontsize=8, loc="upper right"); ax.grid(True, alpha=0.3)

    # ----------------------------------------------------------
    # Panel 3: Strategic Interaction — Prisoner's Dilemma heatmap
    # ----------------------------------------------------------
    ax = axes[2]
    payoff_grid = np.array([
        [[-1, -1], [-3,  0]],
        [[ 0, -3], [-2, -2]],
    ], dtype=float)
    strategies = ["Cooperate", "Defect"]

    # heatmap of Player 1's payoffs
    p1_mat = payoff_grid[:, :, 0]
    im = ax.imshow(p1_mat, cmap="RdYlGn", vmin=-3.5, vmax=0.5, aspect="auto")
    plt.colorbar(im, ax=ax, label="Player 1 payoff", shrink=0.8)

    nash_cells = {(1, 1)}   # (Defect, Defect)
    for i in range(2):
        for j in range(2):
            p1, p2 = int(payoff_grid[i, j, 0]), int(payoff_grid[i, j, 1])
            mark = " ★" if (i, j) in nash_cells else ""
            ax.text(j, i, f"({p1}, {p2}){mark}", ha="center", va="center",
                    fontsize=13, fontweight="bold")

    ax.set_xticks([0, 1]); ax.set_xticklabels(strategies, fontsize=10)
    ax.set_yticks([0, 1]); ax.set_yticklabels(strategies, fontsize=10)
    ax.set_xlabel("Player 2", fontsize=11); ax.set_ylabel("Player 1", fontsize=11)
    ax.set_title("Layer 3 — Strategic Interaction\nPrisoner's Dilemma  ★ = Nash Eq.", fontsize=11)

    plt.tight_layout()
    fig.savefig(output, dpi=150, bbox_inches="tight")
    print(f"\nPlot saved → {output}")


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

    # ---- Plot ---------------------------------------------------
    plot_economics(u_fn, "/home/user/jules-ai-flow/economics_journey.png")


if __name__ == "__main__":
    main()
