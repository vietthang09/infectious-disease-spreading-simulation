import sys

import pygame

from config import COLORS, CONFIG
from task2_experiment import (
    TASK2_BASELINE,
    TASK2_DEFAULT_SEEDS,
    compute_metrics,
    create_seeded_simulation,
    current_counts,
    d_values,
    export_task2_outputs,
    generate_fixed_seeds,
    run_setting_fast,
    summarize_task2,
)
from ui import Button, draw_grid, draw_text


PANEL_WIDTH = 420
SLOW_FPS = 1
FAST_FPS = 10


def create_task2_state():
    state = {
        "d_start": 0.1,
        "d_end": 0.9,
        "d_step": 0.1,
        "selected_d": 0.1,
        "seeds": TASK2_DEFAULT_SEEDS[:],
        "seed_index": 0,
        "mode": "Slow",
        "sim": None,
        "step": 0,
        "selected_running": False,
        "selected_done": False,
        "selected_metrics": None,
        "batch_running": False,
        "batch_jobs": [],
        "batch_total": 0,
        "batch_completed": 0,
        "raw_results": [],
        "summary": [],
        "status": "Idle",
        "last_output": "Select a Task 2 setting and run it",
    }
    reset_selected_simulation(state)
    return state


def clamp_task2_ranges(task2):
    task2["d_start"] = round(max(0.0, min(0.9, task2["d_start"])), 1)
    task2["d_end"] = round(max(task2["d_start"], min(0.9, task2["d_end"])), 1)
    task2["d_step"] = round(max(0.1, min(0.9, task2["d_step"])), 1)

    values = d_values(task2["d_start"], task2["d_end"], task2["d_step"])
    if task2["selected_d"] not in values:
        task2["selected_d"] = values[0]


def reset_selected_simulation(task2):
    seed = task2["seeds"][task2["seed_index"]]
    task2["sim"] = create_seeded_simulation(task2["selected_d"], seed)
    task2["step"] = 0
    task2["selected_running"] = False
    task2["selected_done"] = False
    task2["selected_metrics"] = None
    task2["status"] = "Selected setting reset"
    task2["last_output"] = f"Ready: d={task2['selected_d']:.1f}, seed={seed}"


def adjust_value(task2, key, delta):
    if task2["batch_running"] or task2["selected_running"]:
        return
    task2[key] = round(task2[key] + delta, 1)
    clamp_task2_ranges(task2)
    reset_selected_simulation(task2)


def cycle_selected_d(task2, direction):
    if task2["batch_running"] or task2["selected_running"]:
        return
    values = d_values(task2["d_start"], task2["d_end"], task2["d_step"])
    index = values.index(task2["selected_d"])
    task2["selected_d"] = values[(index + direction) % len(values)]
    reset_selected_simulation(task2)


def cycle_seed(task2, direction):
    if task2["batch_running"] or task2["selected_running"]:
        return
    task2["seed_index"] = (task2["seed_index"] + direction) % len(task2["seeds"])
    reset_selected_simulation(task2)


def toggle_mode(task2):
    if task2["batch_running"] or task2["selected_running"]:
        return
    task2["mode"] = "Fast" if task2["mode"] == "Slow" else "Slow"
    task2["status"] = f"Mode: {task2['mode']}"


def set_generated_seeds(task2):
    if task2["batch_running"] or task2["selected_running"]:
        return
    task2["seeds"] = generate_fixed_seeds()
    task2["seed_index"] = 0
    reset_selected_simulation(task2)
    task2["last_output"] = "Generated fixed seeds from master seed"


def run_selected(task2):
    if task2["batch_running"] or task2["selected_running"]:
        return

    if task2["selected_done"]:
        reset_selected_simulation(task2)
    task2["selected_running"] = True
    task2["status"] = f"{task2['mode']} run playing"
    task2["last_output"] = f"{task2['mode']} mode is animating the selected setting"


def stop_selected(task2):
    if not task2["selected_running"]:
        return
    task2["selected_running"] = False
    task2["status"] = "Selected run stopped"
    task2["last_output"] = "Animation stopped; reset or run selected again"


def step_selected_simulation(task2):
    if not task2["selected_running"]:
        return

    task2["sim"].update_step()
    task2["step"] += 1

    if task2["sim"].active_cases() == 0 or task2["step"] >= TASK2_BASELINE["max_steps"]:
        task2["selected_running"] = False
        task2["selected_done"] = True
        task2["selected_metrics"] = compute_metrics(
            task2["sim"],
            task2["selected_d"],
            task2["seeds"][task2["seed_index"]],
            task2["step"],
        )
        task2["status"] = f"Selected {task2['mode'].lower()} run done"
        task2["last_output"] = (
            f"{task2['mode']} result: duration={task2['step']}, "
            f"deaths={task2['selected_metrics']['total_deaths']}"
        )


def start_batch_fast(task2):
    if task2["batch_running"] or task2["selected_running"]:
        return

    clamp_task2_ranges(task2)
    values = d_values(task2["d_start"], task2["d_end"], task2["d_step"])
    task2["batch_jobs"] = [(d_value, seed) for d_value in values for seed in task2["seeds"]]
    task2["batch_total"] = len(task2["batch_jobs"])
    task2["batch_completed"] = 0
    task2["raw_results"] = []
    task2["summary"] = []
    task2["batch_running"] = True
    task2["status"] = "Running all settings fast"
    task2["last_output"] = "Batch fast run started"


def update_batch_fast(task2):
    if not task2["batch_running"]:
        return

    if task2["batch_jobs"]:
        d_value, seed = task2["batch_jobs"].pop(0)
        task2["raw_results"].append(run_setting_fast(d_value, seed))
        task2["batch_completed"] += 1
        task2["last_output"] = f"Batch: d={d_value:.1f}, seed={seed}"
        return

    task2["summary"] = summarize_task2(task2["raw_results"])
    raw_path, summary_path = export_task2_outputs(task2["raw_results"], task2["summary"])
    task2["batch_running"] = False
    task2["status"] = "Batch fast run done"
    task2["last_output"] = f"Saved {raw_path} and {summary_path}"


def add_adjust_buttons(buttons, panel_x, y, on_minus, on_plus, enabled):
    buttons.append(Button((panel_x + 284, y - 4, 34, 26), "-", on_minus, enabled))
    buttons.append(Button((panel_x + 324, y - 4, 34, 26), "+", on_plus, enabled))


def draw_task2_panel(screen, fonts, task2, panel_x, panel_height):
    font, small_font, title_font = fonts
    buttons = []

    pygame.draw.rect(screen, (25, 29, 36), (panel_x, 0, PANEL_WIDTH, panel_height))
    pygame.draw.line(screen, (70, 76, 86), (panel_x, 0), (panel_x, panel_height), 2)

    enabled = not task2["batch_running"] and not task2["selected_running"]
    seed = task2["seeds"][task2["seed_index"]]
    counts = current_counts(task2["sim"])
    active_cases = counts["I"] + counts["S"]

    y = 18
    draw_text(screen, title_font, "Task 2 Only", panel_x + 18, y)
    y += 30
    draw_text(screen, small_font, "Baseline: p=0.3, N=5, max_steps=300", panel_x + 18, y)
    y += 32

    rows = [
        (
            "d start",
            f"{task2['d_start']:.1f}",
            lambda: adjust_value(task2, "d_start", -0.1),
            lambda: adjust_value(task2, "d_start", 0.1),
        ),
        (
            "d end",
            f"{task2['d_end']:.1f}",
            lambda: adjust_value(task2, "d_end", -0.1),
            lambda: adjust_value(task2, "d_end", 0.1),
        ),
        (
            "d step",
            f"{task2['d_step']:.1f}",
            lambda: adjust_value(task2, "d_step", -0.1),
            lambda: adjust_value(task2, "d_step", 0.1),
        ),
        (
            "selected d",
            f"{task2['selected_d']:.1f}",
            lambda: cycle_selected_d(task2, -1),
            lambda: cycle_selected_d(task2, 1),
        ),
        (
            "seed",
            str(seed),
            lambda: cycle_seed(task2, -1),
            lambda: cycle_seed(task2, 1),
        ),
    ]

    for label, value, minus_action, plus_action in rows:
        draw_text(screen, font, f"{label}: {value}", panel_x + 18, y)
        add_adjust_buttons(buttons, panel_x, y, minus_action, plus_action, enabled)
        y += 32

    buttons.append(
        Button(
            (panel_x + 18, y, 90, 30),
            f"Mode: {task2['mode']}",
            lambda: toggle_mode(task2),
            enabled,
        )
    )
    buttons.append(Button((panel_x + 116, y, 96, 30), "Run", lambda: run_selected(task2), enabled))
    buttons.append(
        Button((panel_x + 220, y, 80, 30), "Stop", lambda: stop_selected(task2), task2["selected_running"])
    )
    buttons.append(
        Button(
            (panel_x + 308, y, 84, 30),
            "Reset",
            lambda: reset_selected_simulation(task2),
            not task2["batch_running"],
        )
    )
    y += 40

    buttons.append(
        Button((panel_x + 18, y, 176, 30), "Generate Seeds", lambda: set_generated_seeds(task2), enabled)
    )
    buttons.append(
        Button((panel_x + 204, y, 176, 30), "Run All Fast", lambda: start_batch_fast(task2), enabled)
    )
    y += 42

    draw_text(screen, small_font, f"Seeds: {', '.join(str(value) for value in task2['seeds'])}", panel_x + 18, y)
    y += 24
    draw_text(screen, font, f"Status: {task2['status']}", panel_x + 18, y)
    y += 24
    draw_text(screen, font, f"Step: {task2['step']} / {TASK2_BASELINE['max_steps']}", panel_x + 18, y)
    y += 24
    draw_text(
        screen,
        font,
        f"H/I/S/R/D: {counts['H']} / {counts['I']} / {counts['S']} / {counts['R']} / {counts['Dead']}",
        panel_x + 18,
        y,
    )
    y += 24
    draw_text(screen, font, f"Active I+S: {active_cases}", panel_x + 18, y)
    y += 24
    draw_text(screen, font, f"Batch: {task2['batch_completed']} / {task2['batch_total']}", panel_x + 18, y)
    y += 30
    draw_text(screen, small_font, task2["last_output"], panel_x + 18, y, (190, 198, 210))
    y += 36

    if task2["selected_metrics"]:
        metrics = task2["selected_metrics"]
        draw_text(screen, title_font, "Selected Result", panel_x + 18, y)
        y += 28
        draw_text(
            screen,
            small_font,
            f"duration={metrics['epidemic_duration']} deaths={metrics['total_deaths']}",
            panel_x + 18,
            y,
        )
        y += 22
        draw_text(
            screen,
            small_font,
            f"recovered={metrics['final_recovered']} peak sick={metrics['peak_sick']}",
            panel_x + 18,
            y,
        )
        y += 30

    draw_text(screen, title_font, "Batch Summary", panel_x + 18, y)
    y += 28
    draw_text(screen, small_font, "d     duration      deaths", panel_x + 18, y, (180, 188, 200))
    y += 20

    for row in task2["summary"][-9:]:
        text = (
            f"{row['d']:.1f}   "
            f"{row['duration_mean']:.1f} +/- {row['duration_std']:.1f}   "
            f"{row['deaths_mean']:.1f} +/- {row['deaths_std']:.1f}"
        )
        draw_text(screen, small_font, text, panel_x + 18, y)
        y += 20

    for button in buttons:
        button.draw(screen, small_font)

    return buttons


def main():
    pygame.init()
    pygame.font.init()

    cell_size = CONFIG["cell_size"]
    grid_pixel_width = CONFIG["grid_width"] * cell_size
    screen_width = grid_pixel_width + PANEL_WIDTH
    screen_height = CONFIG["grid_height"] * cell_size

    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Task 2 Epidemic Experiment")
    clock = pygame.time.Clock()
    fonts = (
        pygame.font.SysFont("arial", 16),
        pygame.font.SysFont("arial", 14),
        pygame.font.SysFont("arial", 20, bold=True),
    )

    task2 = create_task2_state()
    buttons = []
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in buttons:
                    if button.handle_click(event.pos):
                        break

        update_batch_fast(task2)
        step_selected_simulation(task2)

        screen.fill(COLORS["BACKGROUND"])
        draw_grid(screen, task2["sim"], cell_size)
        buttons = draw_task2_panel(screen, fonts, task2, grid_pixel_width, screen_height)

        counts = current_counts(task2["sim"])
        pygame.display.set_caption(
            f"Task 2 | d={task2['selected_d']:.1f} | seed={task2['seeds'][task2['seed_index']]} | "
            f"Step: {task2['step']} | H: {counts['H']} | I: {counts['I']} | "
            f"S: {counts['S']} | R: {counts['R']} | Dead: {counts['Dead']}"
        )
        pygame.display.flip()

        if task2["selected_running"] and task2["mode"] == "Slow":
            clock.tick(SLOW_FPS)
        elif task2["selected_running"] and task2["mode"] == "Fast":
            clock.tick(FAST_FPS)
        else:
            clock.tick(30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
