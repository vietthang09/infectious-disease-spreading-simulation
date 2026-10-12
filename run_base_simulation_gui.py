"""
Interactive Pygame GUI for the Base Epidemic Spreading Simulation.

Features:
1. Base Cellular Automaton Model on a 2D grid with periodic boundaries:
   - 4 states: Healthy (H), Infected (I - incubation), Sick (S - infectious),
     Recovered (R - immune) / Dead.
   - Initial condition: 1 patient zero in Infected (I) state, all others Healthy (H).
   - Moore neighborhood movement (8 directions + stay).

2. Interactive Simulation Controls:
   - Play / Pause (Spacebar or UI button)
   - Single Step +1 (Right arrow key or UI button)
   - Reset with current seed (R key or UI button)
   - New Seed (randomize seed and reset)
   - Speed selection: 1 FPS, 5 FPS, 15 FPS, 30 FPS, and MAX (unthrottled)

3. Comprehensive Parameter Tuning:
   - p: Transmission risk per contact (0.01 - 1.0)
   - N: Incubation period in days/steps (I -> S)
   - sick_duration: Infectious period in days/steps (S -> R/Dead)
   - d: Mortality probability, automatically keeping s = 1 - d
   - Pop: Initial population size

4. Scenario Presets:
   - Baseline (p=0.3, N=5, sick=5, d=0.2, s=0.8, Pop=800)
   - Extremely Dangerous (Subtask 1: p=0.6, N=7, sick=8, d=0.5, Pop=800)
   - Mild / Fast Recovery (p=0.2, N=3, sick=3, d=0.02, Pop=800)
   - High Mortality Outbreak (p=0.35, N=4, sick=5, d=0.85, Pop=800)

5. Real-Time Analytics & Epidemic Curves:
   - Color-coded 2D cellular grid animation.
   - Live multi-curve timeline chart (H, I, S, R, Dead).
   - Real-time statistics: Step, Active cases (I+S), Peak Sick (S max), Cumulative infections.
   - High-resolution Matplotlib plot and CSV export to plots/ and results/.
"""

import csv
import os
import random
import sys
from copy import deepcopy
import numpy as np
import pygame

from config import COLORS, CONFIG
from simulation import Simulation
from agent import Agent


# UI layout constants
CELL_SIZE = CONFIG.get("cell_size", 15)
GRID_W = CONFIG.get("grid_width", 60)
GRID_H = CONFIG.get("grid_height", 40)
PIXEL_W = GRID_W * CELL_SIZE
PIXEL_H = GRID_H * CELL_SIZE

PANEL_W = 430
SCREEN_W = PIXEL_W + PANEL_W
SCREEN_H = max(PIXEL_H, 670)

# Preset epidemic scenarios
PRESETS = [
    {
        "id": "baseline",
        "name": "1. Baseline (Standard)",
        "p": 0.3,
        "N": 5,
        "sick_duration": 5,
        "d": 0.2,
        "pop": 800,
        "desc": "Standard baseline: p=0.3, N=5, d=20%, s=80%",
    },
    {
        "id": "dangerous",
        "name": "2. Highly Dangerous",
        "p": 0.6,
        "N": 7,
        "sick_duration": 8,
        "d": 0.5,
        "pop": 800,
        "desc": "High contagion, long incubation, high mortality",
    },
    {
        "id": "mild",
        "name": "3. Mild / Rapid Recovery",
        "p": 0.2,
        "N": 3,
        "sick_duration": 3,
        "d": 0.02,
        "pop": 800,
        "desc": "Low risk, fast recovery, herd immunity",
    },
    {
        "id": "deadly",
        "name": "4. High Mortality Outbreak",
        "p": 0.35,
        "N": 4,
        "sick_duration": 5,
        "d": 0.85,
        "pop": 800,
        "desc": "d=85%: High mortality breaks transmission chains",
    },
]


class BaseSimulationGUI:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Infectious Disease Spreading Simulation — Base Model GUI")
        self.clock = pygame.time.Clock()

        # Fonts
        self.f_title = pygame.font.SysFont("arial", 16, bold=True)
        self.f_sub = pygame.font.SysFont("arial", 12)
        self.f_bold = pygame.font.SysFont("arial", 12, bold=True)
        self.f_main = pygame.font.SysFont("arial", 12)
        self.f_small = pygame.font.SysFont("arial", 11)

        # Simulation parameters
        self.p = float(CONFIG.get("p", 0.3))
        self.N = int(CONFIG.get("N", 5))
        self.sick_duration = int(CONFIG.get("sick_duration", 5))
        self.d = float(CONFIG.get("d", 0.2))
        self.pop = int(CONFIG.get("initial_population", 800))
        self.flat_rate = bool(CONFIG.get("flat_infection_rate", True))

        self.seed = 101
        self.fps_options = [1, 5, 15, 30, 0]  # 0 indicates MAX / unthrottled
        self.fps_idx = 1  # Default: 5 FPS

        self.running = False
        self.step = 0
        self.sim = None
        self.active_preset = "baseline"
        self.status_msg = "Ready"

        # Initialize simulation instance
        self.reset_simulation()

    def get_current_config(self):
        cfg = deepcopy(CONFIG)
        cfg["grid_width"] = GRID_W
        cfg["grid_height"] = GRID_H
        cfg["initial_population"] = self.pop
        cfg["p"] = round(self.p, 3)
        cfg["N"] = self.N
        cfg["sick_duration"] = self.sick_duration
        cfg["d"] = round(self.d, 3)
        cfg["s"] = round(1.0 - self.d, 3)
        cfg["flat_infection_rate"] = self.flat_rate
        return cfg

    def reset_simulation(self, new_seed=False):
        if new_seed:
            self.seed = random.randint(1, 999999)

        random.seed(self.seed)
        np.random.seed(self.seed)

        config = self.get_current_config()
        self.sim = Simulation(config)
        self.step = 0
        self.running = False
        self.set_notification(f"Reset simulation (Seed = {self.seed})")

    def set_notification(self, msg):
        self.status_msg = msg

    def apply_preset(self, preset):
        self.p = preset["p"]
        self.N = preset["N"]
        self.sick_duration = preset["sick_duration"]
        self.d = preset["d"]
        self.pop = preset["pop"]
        self.active_preset = preset["id"]
        self.reset_simulation()
        self.set_notification(f"Applied preset: {preset['name']}")

    def do_step(self):
        if self.sim.active_cases() == 0:
            self.running = False
            return

        self.step += 1
        self.sim.update_step()

        if self.sim.active_cases() == 0:
            self.running = False
            counts = self.sim.count_states()
            self.set_notification(f"Outbreak ended at step {self.step}! Dead: {counts['Dead']}, Recovered: {counts['R']}")

    def export_data_and_plot(self):
        """Export simulation trajectory to CSV and generate a publication-quality Matplotlib plot."""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            os.makedirs("results", exist_ok=True)
            os.makedirs("plots", exist_ok=True)

            hist = self.sim.history
            steps_cnt = len(hist["H"])
            csv_path = "results/base_simulation_history.csv"

            # 1. Export CSV
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["step", "H", "I", "S", "R", "Dead", "active_cases"])
                for s in range(steps_cnt):
                    writer.writerow([
                        s,
                        hist["H"][s],
                        hist["I"][s],
                        hist["S"][s],
                        hist["R"][s],
                        hist["Dead"][s],
                        hist["I"][s] + hist["S"][s],
                    ])

            # 2. Export Matplotlib Plot
            plot_path = "plots/base_simulation_curves.png"
            plt.figure(figsize=(9, 5.5), dpi=150)
            x_axis = list(range(steps_cnt))

            plt.plot(x_axis, hist["H"], label="Healthy (H)", color="#2ecc71", linewidth=2)
            plt.plot(x_axis, hist["I"], label="Infected (I - Incubation)", color="#f1c40f", linewidth=2)
            plt.plot(x_axis, hist["S"], label="Sick (S - Infectious)", color="#e74c3c", linewidth=2)
            plt.plot(x_axis, hist["R"], label="Recovered (R - Immune)", color="#95a5a6", linewidth=2)
            plt.plot(x_axis, hist["Dead"], label="Dead", color="#34495e", linewidth=2, linestyle="--")

            # Mark infection peak
            peak_s = max(hist["S"])
            peak_step = hist["S"].index(peak_s)
            plt.scatter([peak_step], [peak_s], color="#c0392b", s=60, zorder=5)
            plt.annotate(
                f"Peak Sick S={peak_s} (day {peak_step})",
                xy=(peak_step, peak_s),
                xytext=(peak_step + max(1, steps_cnt // 20), peak_s),
                arrowprops=dict(facecolor="#c0392b", shrink=0.05, width=1, headwidth=6),
                fontsize=9,
                fontweight="bold",
                color="#c0392b",
            )

            s_val = round(1.0 - self.d, 3)
            plt.title(
                f"Base Model Epidemic Trajectory (p={self.p}, N={self.N}, d={self.d}, s={s_val}, Pop={self.pop})",
                fontsize=12,
                fontweight="bold",
            )
            plt.xlabel("Time (Steps / Days)", fontsize=10)
            plt.ylabel("Number of Agents", fontsize=10)
            plt.grid(True, linestyle=":", alpha=0.6)
            plt.legend(loc="best", framealpha=0.9)
            plt.tight_layout()
            plt.savefig(plot_path)
            plt.close()

            self.set_notification(f"Saved: {plot_path} & {csv_path}")
        except Exception as e:
            self.set_notification(f"Export error: {str(e)[:30]}")

    def draw_grid_view(self):
        grid_rect = pygame.Rect(0, 0, PIXEL_W, PIXEL_H)
        pygame.draw.rect(self.screen, COLORS["BACKGROUND"], grid_rect)

        for x in range(self.sim.width):
            for y in range(self.sim.height):
                agent = self.sim.grid[x, y]
                rx = x * CELL_SIZE
                ry = y * CELL_SIZE
                if agent is not None:
                    color = COLORS.get(agent.state, (200, 200, 200))
                    pygame.draw.rect(self.screen, color, (rx, ry, CELL_SIZE, CELL_SIZE))

                    # Highlight Patient Zero during initial days
                    if agent.id == 0 and self.step <= 10:
                        pygame.draw.rect(self.screen, (255, 255, 255), (rx, ry, CELL_SIZE, CELL_SIZE), 1)
                else:
                    pygame.draw.rect(self.screen, COLORS["GRID_LINE"], (rx, ry, CELL_SIZE, CELL_SIZE), 1)

        # Border between grid and control panel
        pygame.draw.line(self.screen, (60, 70, 85), (PIXEL_W, 0), (PIXEL_W, SCREEN_H), 2)

    def draw_timeline_chart(self, rect):
        """Draw real-time epidemic curves directly on the Pygame control panel."""
        pygame.draw.rect(self.screen, (22, 26, 33), rect, border_radius=5)
        pygame.draw.rect(self.screen, (55, 65, 80), rect, width=1, border_radius=5)

        hist = self.sim.history
        total_steps = len(hist["H"])
        pop_max = float(max(self.pop, 1))

        gx = rect.x + 10
        gy = rect.y + 24
        gw = rect.width - 20
        gh = rect.height - 34

        self.screen.blit(self.f_bold.render("Real-time Epidemic Curves", True, (220, 230, 242)), (rect.x + 10, rect.y + 6))

        # Horizontal grid lines
        pygame.draw.line(self.screen, (38, 45, 56), (gx, gy + gh // 2), (gx + gw, gy + gh // 2), 1)
        pygame.draw.line(self.screen, (38, 45, 56), (gx, gy), (gx + gw, gy), 1)

        # Y-axis ticks
        self.screen.blit(self.f_small.render(f"{self.pop}", True, (100, 115, 130)), (gx + 2, gy - 2))
        self.screen.blit(self.f_small.render(f"{self.pop // 2}", True, (100, 115, 130)), (gx + 2, gy + gh // 2 - 2))

        # Trajectory curves
        curves = [
            ("H", (46, 204, 113), 1),
            ("R", (149, 165, 166), 2),
            ("Dead", (200, 70, 70), 2),
            ("I", (241, 196, 15), 2),
            ("S", (231, 76, 60), 2),
        ]

        if total_steps > 1:
            for key, col, width in curves:
                pts = []
                for s_idx, val in enumerate(hist[key]):
                    px = gx + (s_idx / max(1, total_steps - 1)) * gw
                    py = gy + gh - (val / pop_max) * gh
                    pts.append((px, py))
                if len(pts) > 1:
                    pygame.draw.lines(self.screen, col, False, pts, width)

        # Color legend
        leg_y = rect.bottom - 18
        leg_items = [
            ("H", (46, 204, 113)),
            ("I", (241, 196, 15)),
            ("S", (231, 76, 60)),
            ("R", (149, 165, 166)),
            ("Dead", (200, 70, 70)),
        ]
        lx = rect.x + 12
        for lbl, c in leg_items:
            pygame.draw.rect(self.screen, c, (lx, leg_y + 2, 8, 8))
            self.screen.blit(self.f_small.render(lbl, True, (200, 210, 220)), (lx + 12, leg_y))
            lx += 75

    def draw_panel(self):
        panel_rect = pygame.Rect(PIXEL_W, 0, PANEL_W, SCREEN_H)
        pygame.draw.rect(self.screen, (28, 33, 42), panel_rect)

        x = PIXEL_W + 16
        y = 12

        # 1. Header
        title = self.f_title.render("BASE MODEL SIMULATION", True, (240, 245, 255))
        self.screen.blit(title, (x, y))
        sub = self.f_sub.render("2D Cellular Automaton • 4 States: H - I - S - R", True, (130, 145, 165))
        self.screen.blit(sub, (x, y + 20))
        y += 42

        # 2. Main Controls: Play, Step, Reset, New Seed
        btn_h = 30
        buttons = []

        # Play / Pause
        play_label = "⏸ Pause" if self.running else "Play"
        play_color = (192, 57, 43) if self.running else (39, 174, 96)
        play_rect = pygame.Rect(x, y, 115, btn_h)
        pygame.draw.rect(self.screen, play_color, play_rect, border_radius=4)
        pygame.draw.rect(self.screen, (255, 255, 255), play_rect, width=1, border_radius=4)
        lbl_p = self.f_bold.render(play_label, True, (255, 255, 255))
        self.screen.blit(lbl_p, lbl_p.get_rect(center=play_rect.center))
        buttons.append(("toggle_play", play_rect))

        # Step +1
        step_rect = pygame.Rect(x + 122, y, 75, btn_h)
        pygame.draw.rect(self.screen, (41, 128, 185), step_rect, border_radius=4)
        lbl_s = self.f_bold.render("Step +1", True, (255, 255, 255))
        self.screen.blit(lbl_s, lbl_s.get_rect(center=step_rect.center))
        buttons.append(("step", step_rect))

        # Reset
        reset_rect = pygame.Rect(x + 204, y, 85, btn_h)
        pygame.draw.rect(self.screen, (52, 73, 94), reset_rect, border_radius=4)
        lbl_r = self.f_bold.render("Reset", True, (240, 240, 240))
        self.screen.blit(lbl_r, lbl_r.get_rect(center=reset_rect.center))
        buttons.append(("reset", reset_rect))

        # Random Seed
        seed_rect = pygame.Rect(x + 296, y, 96, btn_h)
        pygame.draw.rect(self.screen, (52, 73, 94), seed_rect, border_radius=4)
        lbl_seed = self.f_bold.render("New Seed", True, (240, 240, 240))
        self.screen.blit(lbl_seed, lbl_seed.get_rect(center=seed_rect.center))
        buttons.append(("new_seed", seed_rect))

        y += btn_h + 8

        # Speed options (FPS)
        fps_val = self.fps_options[self.fps_idx]
        self.screen.blit(self.f_bold.render("Simulation Speed:", True, (200, 210, 225)), (x, y + 4))

        fps_btns = [("1 FPS", 0), ("5 FPS", 1), ("15 FPS", 2), ("30 FPS", 3), ("MAX", 4)]
        fx = x + 124
        for flabel, f_idx in fps_btns:
            f_rect = pygame.Rect(fx, y, 48, 24)
            is_cur = (self.fps_idx == f_idx)
            f_fill = (41, 128, 185) if is_cur else (45, 52, 64)
            f_border = (120, 180, 240) if is_cur else (65, 75, 90)
            pygame.draw.rect(self.screen, f_fill, f_rect, border_radius=3)
            pygame.draw.rect(self.screen, f_border, f_rect, width=1, border_radius=3)
            txt = self.f_small.render(flabel, True, (255, 255, 255) if is_cur else (180, 190, 205))
            self.screen.blit(txt, txt.get_rect(center=f_rect.center))
            buttons.append((f"fps_{f_idx}", f_rect))
            fx += 53

        y += 32

        # 3. Scenario Presets
        self.screen.blit(self.f_bold.render("Scenario Presets:", True, (200, 210, 225)), (x, y))
        y += 18

        px = x
        for i, preset in enumerate(PRESETS):
            pre_rect = pygame.Rect(px, y, 194, 26)
            is_act = (self.active_preset == preset["id"])
            p_fill = (46, 85, 125) if is_act else (38, 44, 55)
            p_border = (80, 150, 220) if is_act else (60, 70, 85)
            pygame.draw.rect(self.screen, p_fill, pre_rect, border_radius=4)
            pygame.draw.rect(self.screen, p_border, pre_rect, width=1, border_radius=4)

            p_txt = self.f_small.render(preset["name"], True, (255, 255, 255) if is_act else (185, 195, 210))
            self.screen.blit(p_txt, (px + 6, y + 6))
            buttons.append((f"preset_{preset['id']}", pre_rect))

            if i % 2 == 0:
                px += 200
            else:
                px = x
                y += 30

        y += 4

        # 4. Parameter Tuning
        param_box = pygame.Rect(x, y, PANEL_W - 32, 138)
        pygame.draw.rect(self.screen, (22, 26, 33), param_box, border_radius=5)
        pygame.draw.rect(self.screen, (55, 65, 80), param_box, width=1, border_radius=5)

        self.screen.blit(self.f_bold.render("Parameter Tuning (Applies on Reset):", True, (220, 230, 245)), (x + 10, y + 6))

        py_row = y + 26
        param_rows = [
            ("Transmission risk p:", f"{self.p:.2f}", "p_dec", "p_inc"),
            ("Incubation N (days):", f"{self.N}", "N_dec", "N_inc"),
            ("Sick duration (days):", f"{self.sick_duration}", "sick_dec", "sick_inc"),
            ("Mortality d (s = 1 - d):", f"d={self.d:.2f} (s={1.0-self.d:.2f})", "d_dec", "d_inc"),
            ("Population Pop:", f"{self.pop}", "pop_dec", "pop_inc"),
        ]

        for plabel, pval_str, b_dec, b_inc in param_rows:
            self.screen.blit(self.f_small.render(plabel, True, (170, 185, 200)), (x + 12, py_row + 2))

            # [-] Button
            btn_minus = pygame.Rect(x + 235, py_row, 24, 18)
            pygame.draw.rect(self.screen, (45, 55, 70), btn_minus, border_radius=3)
            lbl_m = self.f_bold.render("-", True, (240, 240, 240))
            self.screen.blit(lbl_m, lbl_m.get_rect(center=btn_minus.center))
            buttons.append((b_dec, btn_minus))

            # Value text
            val_lbl = self.f_small.render(pval_str, True, (255, 230, 130))
            self.screen.blit(val_lbl, val_lbl.get_rect(center=(x + 315, py_row + 9)))

            # [+] Button
            btn_plus = pygame.Rect(x + 365, py_row, 24, 18)
            pygame.draw.rect(self.screen, (45, 55, 70), btn_plus, border_radius=3)
            lbl_p = self.f_bold.render("+", True, (240, 240, 240))
            self.screen.blit(lbl_p, lbl_p.get_rect(center=btn_plus.center))
            buttons.append((b_inc, btn_plus))

            py_row += 21

        y += 144

        # 5. Live Metrics & Statistics
        counts = self.sim.count_states()
        active = self.sim.active_cases()
        hist = self.sim.history
        peak_s = max(hist["S"]) if hist["S"] else 0
        total_infected = self.pop - counts["H"]

        stat_box = pygame.Rect(x, y, PANEL_W - 32, 68)
        pygame.draw.rect(self.screen, (22, 26, 33), stat_box, border_radius=5)
        pygame.draw.rect(self.screen, (55, 65, 80), stat_box, width=1, border_radius=5)

        s_step = self.f_bold.render(f"Step: {self.step} days", True, (52, 152, 219))
        self.screen.blit(s_step, (x + 10, y + 6))

        s_act = self.f_bold.render(f"Active (I+S): {active}", True, (231, 76, 60) if active > 0 else (46, 204, 113))
        self.screen.blit(s_act, (x + 160, y + 6))

        s_peak = self.f_small.render(f"Peak Sick (S max): {peak_s}", True, (241, 196, 15))
        self.screen.blit(s_peak, (x + 10, y + 26))

        pct_inf = (total_infected / max(1, self.pop)) * 100
        s_tot = self.f_small.render(f"Cumulative Infected: {total_infected} ({pct_inf:.1f}%)", True, (220, 220, 230))
        self.screen.blit(s_tot, (x + 160, y + 26))

        # Color-coded counters
        c_items = [
            (f"H:{counts['H']}", COLORS["H"]),
            (f"I:{counts['I']}", COLORS["I"]),
            (f"S:{counts['S']}", COLORS["S"]),
            (f"R:{counts['R']}", (149, 165, 166)),
            (f"Dead:{counts['Dead']}", (210, 75, 75)),
        ]
        cx = x + 10
        for ctext, ccol in c_items:
            pygame.draw.circle(self.screen, ccol, (cx + 4, y + 54), 4)
            self.screen.blit(self.f_small.render(ctext, True, (220, 230, 240)), (cx + 12, y + 47))
            cx += 76

        y += 74

        # 6. Real-time Epidemic Curves Chart
        chart_h = 135
        chart_rect = pygame.Rect(x, y, PANEL_W - 32, chart_h)
        self.draw_timeline_chart(chart_rect)
        y += chart_h + 8

        # 7. Export Button & Status Toast
        exp_rect = pygame.Rect(x, y, 175, 28)
        pygame.draw.rect(self.screen, (39, 174, 96), exp_rect, border_radius=4)
        lbl_exp = self.f_bold.render("📊 Export Plot & CSV", True, (255, 255, 255))
        self.screen.blit(lbl_exp, lbl_exp.get_rect(center=exp_rect.center))
        buttons.append(("export", exp_rect))

        msg_color = (245, 230, 140) if "Error" not in self.status_msg else (231, 76, 60)
        msg_surf = self.f_small.render(f"Status: {self.status_msg}", True, msg_color)
        self.screen.blit(msg_surf, (x + 185, y + 7))

        return buttons

    def handle_click(self, btn_id):
        if btn_id == "toggle_play":
            if self.sim.active_cases() == 0:
                self.reset_simulation()
            self.running = not self.running
            self.set_notification("Running simulation..." if self.running else "Simulation paused")

        elif btn_id == "step":
            self.running = False
            self.do_step()

        elif btn_id == "reset":
            self.reset_simulation(new_seed=False)

        elif btn_id == "new_seed":
            self.reset_simulation(new_seed=True)

        elif btn_id.startswith("fps_"):
            idx = int(btn_id.split("_")[1])
            self.fps_idx = idx

        elif btn_id.startswith("preset_"):
            p_id = btn_id.replace("preset_", "")
            for p in PRESETS:
                if p["id"] == p_id:
                    self.apply_preset(p)
                    break

        elif btn_id == "p_dec":
            self.p = max(0.05, round(self.p - 0.05, 2))
            self.active_preset = "custom"
        elif btn_id == "p_inc":
            self.p = min(1.0, round(self.p + 0.05, 2))
            self.active_preset = "custom"

        elif btn_id == "N_dec":
            self.N = max(1, self.N - 1)
            self.active_preset = "custom"
        elif btn_id == "N_inc":
            self.N = min(20, self.N + 1)
            self.active_preset = "custom"

        elif btn_id == "sick_dec":
            self.sick_duration = max(1, self.sick_duration - 1)
            self.active_preset = "custom"
        elif btn_id == "sick_inc":
            self.sick_duration = min(20, self.sick_duration + 1)
            self.active_preset = "custom"

        elif btn_id == "d_dec":
            self.d = max(0.0, round(self.d - 0.05, 2))
            self.active_preset = "custom"
        elif btn_id == "d_inc":
            self.d = min(1.0, round(self.d + 0.05, 2))
            self.active_preset = "custom"

        elif btn_id == "pop_dec":
            self.pop = max(50, self.pop - 50)
            self.active_preset = "custom"
        elif btn_id == "pop_inc":
            self.pop = min(GRID_W * GRID_H - 1, self.pop + 50)
            self.active_preset = "custom"

        elif btn_id == "export":
            self.export_data_and_plot()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.sim.active_cases() == 0:
                            self.reset_simulation()
                        self.running = not self.running
                    elif event.key == pygame.K_RIGHT:
                        self.running = False
                        self.do_step()
                    elif event.key == pygame.K_r:
                        self.reset_simulation()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    if hasattr(self, "_active_buttons"):
                        for bid, brect in self._active_buttons:
                            if brect.collidepoint(pos):
                                self.handle_click(bid)
                                break

            if self.running:
                self.do_step()

            self.draw_grid_view()
            self._active_buttons = self.draw_panel()

            pygame.display.flip()

            target_fps = self.fps_options[self.fps_idx]
            if target_fps > 0:
                self.clock.tick(target_fps)
            else:
                self.clock.tick(120)


if __name__ == "__main__":
    app = BaseSimulationGUI()
    app.run()
