"""
ENCS302 - Computer Organization & Architecture
Assignment 3: 5-Stage Pipelined Processor Simulation
Author: Student Submission
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ─────────────────────────────────────────────
# SECTION 1: Pipeline Stage Constants
# ─────────────────────────────────────────────
STAGES = ['IF', 'ID', 'EX', 'MEM', 'WB']
STAGE_COLORS = {
    'IF':  '#4FC3F7',
    'ID':  '#81C784',
    'EX':  '#FFB74D',
    'MEM': '#F06292',
    'WB':  '#CE93D8',
    'STALL': '#BDBDBD',
    'FLUSH': '#EF5350',
}

# ─────────────────────────────────────────────
# SECTION 2: Sample Instruction Sequence
# ─────────────────────────────────────────────
# Simulated RISC instruction mix (representative)
instructions = [
    "ADD R1, R2, R3",    # I0
    "SUB R4, R1, R5",    # I1 — RAW hazard on R1 (needs forwarding)
    "LW  R6, 0(R7)",     # I2 — Load
    "ADD R8, R6, R9",    # I3 — Load-use hazard (1 stall)
    "BEQ R1, R4, LABEL", # I4 — Branch → 1 flush (misprediction)
    "AND R10,R2, R3",    # I5 — flushed (wrong-path)
    "OR  R11,R4, R5",    # I6 — flushed (wrong-path)
    "XOR R12,R1, R6",    # I7 — correct-path resumes
    "SW  R8, 0(R7)",     # I8
    "MUL R13,R1, R4",    # I9
]

# ─────────────────────────────────────────────
# SECTION 3: Cycle-by-cycle pipeline table
#   Format: dict[instruction_index] = list of (cycle, stage_label)
# ─────────────────────────────────────────────
def build_pipeline_table():
    """
    Returns a 2-D matrix [instruction][cycle] = stage_label or ''
    Manually encodes: forwarding, 1 load-use stall, branch flush.
    """
    n_inst = len(instructions)
    n_cycles = 18
    table = [['' for _ in range(n_cycles)] for _ in range(n_inst)]

    # Normal pipeline for I0 (starts cycle 0)
    offsets = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    # --- I0: ADD (no hazard) ---
    for s, stg in enumerate(STAGES):
        table[0][0 + s] = stg

    # --- I1: SUB — RAW on R1 from I0. Handled by FORWARDING (no stall) ---
    for s, stg in enumerate(STAGES):
        table[1][1 + s] = stg

    # --- I2: LW ---
    for s, stg in enumerate(STAGES):
        table[2][2 + s] = stg

    # --- I3: ADD after LW — load-use hazard: 1 stall inserted ---
    table[3][3] = 'IF'
    table[3][4] = 'STALL'   # stall cycle
    table[3][5] = 'ID'
    table[3][6] = 'EX'
    table[3][7] = 'MEM'
    table[3][8] = 'WB'

    # --- I4: BEQ — starts after I3's extra stall ---
    table[4][4] = 'IF'
    table[4][5] = 'STALL'
    table[4][6] = 'ID'
    table[4][7] = 'EX'
    table[4][8] = 'MEM'
    table[4][9] = 'WB'

    # --- I5, I6: fetched during branch evaluation → FLUSHED ---
    table[5][5] = 'IF'
    table[5][6] = 'FLUSH'

    table[6][6] = 'IF'
    table[6][7] = 'FLUSH'

    # --- I7: correct-path instruction resumes after flush ---
    for s, stg in enumerate(STAGES):
        table[7][8 + s] = stg

    # --- I8 ---
    for s, stg in enumerate(STAGES):
        table[8][9 + s] = stg

    # --- I9 ---
    for s, stg in enumerate(STAGES):
        table[9][10 + s] = stg

    return table, n_cycles

# ─────────────────────────────────────────────
# SECTION 4: CPI Calculation
# ─────────────────────────────────────────────
def compute_cpi(n_instructions=10, stalls=1, flushes=2):
    ideal_cycles = n_instructions + len(STAGES) - 1  # startup fill
    actual_cycles = ideal_cycles + stalls + flushes
    ideal_cpi  = ideal_cycles / n_instructions
    actual_cpi = actual_cycles / n_instructions
    return ideal_cpi, actual_cpi, ideal_cycles, actual_cycles


# ─────────────────────────────────────────────
# SECTION 5: Plot 1 — Pipeline Animation Diagram
# ─────────────────────────────────────────────
def plot_pipeline_animation(table, n_cycles, save_path='pipeline_animation.png'):
    n_inst = len(instructions)
    fig, ax = plt.subplots(figsize=(18, 6))
    ax.set_xlim(0, n_cycles)
    ax.set_ylim(0, n_inst)
    ax.set_facecolor('#1A1A2E')
    fig.patch.set_facecolor('#1A1A2E')

    for i in range(n_inst):
        for c in range(n_cycles):
            stg = table[i][c]
            if stg:
                color = STAGE_COLORS.get(stg, '#FFFFFF')
                rect = mpatches.FancyBboxPatch(
                    (c + 0.05, n_inst - i - 0.95),
                    0.90, 0.85,
                    boxstyle="round,pad=0.05",
                    facecolor=color, edgecolor='#FFFFFF22', linewidth=0.5
                )
                ax.add_patch(rect)
                ax.text(c + 0.5, n_inst - i - 0.52, stg,
                        ha='center', va='center',
                        fontsize=7, fontweight='bold', color='#1A1A2E')

    # Y-axis labels
    for i, inst in enumerate(instructions):
        ax.text(-0.3, n_inst - i - 0.5, f"I{i}: {inst.split()[0]}",
                ha='right', va='center', fontsize=8,
                color='#E0E0E0', fontfamily='monospace')

    # X-axis (cycle numbers)
    ax.set_xticks(np.arange(n_cycles) + 0.5)
    ax.set_xticklabels([f"C{i+1}" for i in range(n_cycles)],
                       fontsize=7, color='#AAAAAA')
    ax.set_yticks([])
    ax.tick_params(axis='x', colors='#AAAAAA', length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Legend
    legend_items = [mpatches.Patch(facecolor=STAGE_COLORS[s], label=s) for s in STAGES]
    legend_items.append(mpatches.Patch(facecolor=STAGE_COLORS['STALL'], label='STALL'))
    legend_items.append(mpatches.Patch(facecolor=STAGE_COLORS['FLUSH'], label='FLUSH'))
    ax.legend(handles=legend_items, loc='lower right', ncol=7,
              facecolor='#16213E', edgecolor='#444', labelcolor='white', fontsize=8)

    ax.set_title('5-Stage Pipeline: Cycle-by-Cycle Execution Diagram',
                 color='white', fontsize=13, fontweight='bold', pad=12)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='#1A1A2E')
    plt.close()
    print(f"[✓] Pipeline animation saved → {save_path}")


# ─────────────────────────────────────────────
# SECTION 6: Plot 2 — CPI Comparison Bar Chart
# ─────────────────────────────────────────────
def plot_cpi_comparison(save_path='cpi_comparison.png'):
    configs = [
        ("No Hazards\n(Ideal)",     0, 0),
        ("With Forwarding\n(1 stall)", 1, 0),
        ("With Branch\n(2 flushes)",   0, 2),
        ("Full Pipeline\n(Realistic)", 1, 2),
    ]

    labels, ideal_cpis, actual_cpis = [], [], []
    for label, stalls, flushes in configs:
        ic, ac, _, _ = compute_cpi(stalls=stalls, flushes=flushes)
        labels.append(label)
        ideal_cpis.append(ic)
        actual_cpis.append(ac)

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#0F3460')
    ax.set_facecolor('#16213E')

    bars1 = ax.bar(x - width/2, ideal_cpis, width, label='Ideal CPI',
                   color='#4FC3F7', edgecolor='white', linewidth=0.5)
    bars2 = ax.bar(x + width/2, actual_cpis, width, label='Actual CPI',
                   color='#F06292', edgecolor='white', linewidth=0.5)

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{bar.get_height():.2f}', ha='center', color='#4FC3F7', fontsize=9)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{bar.get_height():.2f}', ha='center', color='#F06292', fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, color='#CCCCCC', fontsize=9)
    ax.set_ylabel('CPI (Cycles Per Instruction)', color='#CCCCCC')
    ax.set_title('Ideal vs. Actual CPI — Pipeline Performance Analysis',
                 color='white', fontweight='bold', fontsize=12)
    ax.legend(facecolor='#16213E', edgecolor='#555', labelcolor='white')
    ax.tick_params(colors='#AAAAAA')
    ax.set_ylim(0, max(actual_cpis) + 0.3)
    for spine in ax.spines.values():
        spine.set_color('#333')

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='#0F3460')
    plt.close()
    print(f"[✓] CPI comparison chart saved → {save_path}")


# ─────────────────────────────────────────────
# SECTION 7: Text Simulation Output
# ─────────────────────────────────────────────
def generate_simulation_results(save_path='sample_simulation_results.txt'):
    ideal_cpi, actual_cpi, ideal_cyc, actual_cyc = compute_cpi()

    lines = [
        "=" * 60,
        "  ENCS302 | Assignment 3 — Pipeline Simulation Results",
        "=" * 60,
        "",
        "INSTRUCTION SEQUENCE:",
        "-" * 40,
    ]
    for i, inst in enumerate(instructions):
        lines.append(f"  I{i:02d}: {inst}")

    lines += [
        "",
        "HAZARD ANALYSIS:",
        "-" * 40,
        "  Data Hazard (RAW)   : I1 depends on I0 (R1)",
        "    → Resolved via FORWARDING (EX/MEM → EX)",
        "    → No stall cycle required.",
        "",
        "  Load-Use Hazard     : I3 depends on I2 (LW R6)",
        "    → Load-use cannot be forwarded in time.",
        "    → 1 STALL cycle inserted (pipeline bubble).",
        "    → After stall, MEM→EX forwarding used.",
        "",
        "  Control Hazard      : I4 = BEQ (branch)",
        "    → Branch resolved at end of EX stage.",
        "    → 2 instructions (I5, I6) fetched speculatively.",
        "    → Branch taken (misprediction assumed).",
        "    → I5 and I6 FLUSHED from pipeline.",
        "    → 2 wasted cycles (penalty = 2).",
        "",
        "FORWARDING PATHS USED:",
        "-" * 40,
        "  EX/MEM → EX  : I0→I1 (R1 result forwarded)",
        "  MEM/WB → EX  : I2→I3 (R6 after stall)",
        "",
        "CPI COMPUTATION:",
        "-" * 40,
        f"  Total Instructions  : 10",
        f"  Pipeline Stages     : 5",
        f"  Ideal Cycles        : {ideal_cyc}   (N + 4)",
        f"  Stall Cycles Added  : 1",
        f"  Flush Cycles Added  : 2",
        f"  Actual Cycles       : {actual_cyc}",
        f"",
        f"  Ideal  CPI = {ideal_cyc}  / 10 = {ideal_cpi:.3f}",
        f"  Actual CPI = {actual_cyc} / 10 = {actual_cpi:.3f}",
        f"",
        f"  Performance Penalty = {actual_cpi - ideal_cpi:.3f} extra cycles/instruction",
        f"  Speedup Lost        = {((actual_cpi - ideal_cpi)/actual_cpi)*100:.1f}%",
        "",
        "=" * 60,
        "  Simulation Complete.",
        "=" * 60,
    ]

    with open(save_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"[✓] Simulation results saved → {save_path}")
    return '\n'.join(lines)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == '__main__':
    print("\n=== ENCS302 Assignment 3 — Pipeline Simulator ===\n")

    table, n_cycles = build_pipeline_table()
    plot_pipeline_animation(table, n_cycles, 'pipeline_animation.png')
    plot_cpi_comparison('cpi_comparison.png')
    results = generate_simulation_results('sample_simulation_results.txt')

    print("\n--- CONSOLE OUTPUT ---")
    print(results)
