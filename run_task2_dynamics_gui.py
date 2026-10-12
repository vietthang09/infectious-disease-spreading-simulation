"""
Giao diện Pygame trực quan: Nghiên cứu 3 cơ chế dập dịch không gian (Task 2)
1. d rất thấp (d=0.0): Tỷ lệ hồi phục cao -> R tạo thành hàng rào tự nhiên bao vây dịch -> Dịch tắt nhanh.
2. d rất cao (d=0.95): Tỷ lệ chết cao -> Chết nhiều tạo khoảng trống lớn làm đứt gãy đường lây -> Dịch tắt nhanh.
3. d cân bằng (d=0.5): Tử vong tạo khoảng trống + Kháng thể R chắn đường -> Hàng rào kép chia cắt ổ dịch.
"""

import sys
import pygame
from copy import deepcopy

from config import COLORS, CONFIG
from simulation import Simulation


PANEL_WIDTH = 450
DEFAULT_SEED = 101


class Task2DynamicsGUI:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.cell_size = CONFIG["cell_size"]
        self.grid_w = CONFIG["grid_width"]
        self.grid_h = CONFIG["grid_height"]
        self.pixel_w = self.grid_w * self.cell_size
        self.pixel_h = self.grid_h * self.cell_size

        self.screen_w = self.pixel_w + PANEL_WIDTH
        self.screen_h = max(self.pixel_h, 660)

        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption("Task 2 — Phân Tích 3 Cơ Chế Triệt Tiêu Dịch Bệnh Không Gian")
        self.clock = pygame.time.Clock()

        # Fonts
        self.f_title = pygame.font.SysFont("arial", 17, bold=True)
        self.f_sub = pygame.font.SysFont("arial", 12)
        self.f_bold = pygame.font.SysFont("arial", 13, bold=True)
        self.f_main = pygame.font.SysFont("arial", 13)
        self.f_small = pygame.font.SysFont("arial", 11)

        # Định nghĩa 3 trường hợp nghiên cứu
        self.cases = {
            "low": {
                "id": "low",
                "title": "1. d RẤT THẤP (d = 0.0, s = 1.0)",
                "d": 0.0,
                "s": 1.0,
                "tag": "HÀNG RÀO MIỄN DỊCH (HERD IMMUNITY)",
                "desc": (
                    "• Tỷ lệ hồi phục s = 100% cực cao.\n"
                    "• Cá thể khỏi bệnh (R) giữ nguyên trên lưới, không bị lây lại.\n"
                    "• Các cá thể R tạo thành 'Lá chắn sống tự nhiên' bao bọc ổ dịch,\n"
                    "  ngăn virus tiếp cận các cá thể H còn lại.\n"
                    "• Dịch bị cô lập và tắt nhanh mà không có ca tử vong (Dead = 0)!"
                ),
                "highlight_color": (46, 204, 113),
            },
            "balanced": {
                "id": "balanced",
                "title": "2. d CÂN BẰNG (d = 0.5, s = 0.5)",
                "d": 0.5,
                "s": 0.5,
                "tag": "HÀNG RÀO KÉP (R + KHOẢNG TRỐNG)",
                "desc": (
                    "• Tỷ lệ chết d đủ để loại bỏ cá thể bệnh, tạo ra khoảng đệm trống.\n"
                    "• Đồng thời, tỷ lệ hồi phục s đủ lớn để tạo một số lượng lớn cá thể R.\n"
                    "• Sự kết hợp giữa: [Khoảng trống do chết] + [Lá chắn R mang kháng thể]\n"
                    "  tạo nên hàng rào kép chia cắt ổ dịch thành từng cụm nhỏ và dập tắt."
                ),
                "highlight_color": (241, 196, 15),
            },
            "high": {
                "id": "high",
                "title": "3. d RẤT CAO (d = 0.95, s = 0.05)",
                "d": 0.95,
                "s": 0.05,
                "tag": "KHOẢNG TRỐNG TỬ VONG (BURN-OUT)",
                "desc": (
                    "• Tỷ lệ chết d = 95% cực cao. Cá thể bệnh bị chết và xóa khỏi lưới.\n"
                    "• Tạo ra vô số khoảng trống lớn, mật độ dân cư giảm sút nghiêm trọng.\n"
                    "• Các nhóm người khỏe mạnh (H) bị chia cắt, cách ly không gian tự nhiên.\n"
                    "• Chuỗi lây nhiễm đứt gãy vì virus hết vật chủ trung gian để nhảy bước."
                ),
                "highlight_color": (231, 76, 60),
            },
        }

        self.current_case_key = "low"
        self.seed = DEFAULT_SEED
        self.running = False
        self.fps_mode = 5  # 1, 5, 15
        self.step = 0
        self.sim = None
        self.highlight_barriers = True

        self.init_simulation()

    def init_simulation(self):
        self.step = 0
        self.running = False

        c = self.cases[self.current_case_key]
        cfg = deepcopy(CONFIG)
        cfg["d"] = c["d"]
        cfg["s"] = c["s"]

        import random
        random.seed(self.seed)
        self.sim = Simulation(cfg)

    def do_step(self):
        if self.sim.active_cases() == 0:
            self.running = False
            return
        self.step += 1
        self.sim.update_step()
        if self.sim.active_cases() == 0:
            self.running = False

    def draw_grid(self):
        # Nền và lưới
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                agent = self.sim.grid[x, y]
                if agent is not None:
                    col = COLORS.get(agent.state, (200, 200, 200))
                    # Nếu là R và đang bật highlight barrier, vẽ nổi bật hơn
                    if agent.state == "R" and self.highlight_barriers:
                        col = (180, 195, 205)
                    pygame.draw.rect(self.screen, col, rect)
                    if agent.state == "R" and self.highlight_barriers:
                        pygame.draw.rect(self.screen, (220, 235, 245), rect, 1)
                else:
                    # Ô trống (nếu ban đầu có người mà nay đã chết ở mode high d)
                    pygame.draw.rect(self.screen, COLORS["GRID_LINE"], rect, 1)

    def draw_panel(self):
        px = self.pixel_w
        panel_rect = pygame.Rect(px, 0, PANEL_WIDTH, self.screen_h)
        pygame.draw.rect(self.screen, (24, 28, 34), panel_rect)
        pygame.draw.line(self.screen, (48, 56, 68), (px, 0), (px, self.screen_h), 2)

        x = px + 16
        y = 12

        # Header
        t = self.f_title.render("3 CƠ CHẾ DẬP DỊCH THEO d", True, (241, 196, 15))
        self.screen.blit(t, (x, y))
        y += 22
        sub = self.f_sub.render("Khám phá sự ảnh hưởng của d (chết) & s (khỏi) lên làn sóng dịch", True, (150, 160, 175))
        self.screen.blit(sub, (x, y))
        y += 24

        buttons = []

        # 3 Nút chọn kịch bản
        case_buttons = [
            ("btn_low", "low", "1. d THẤP (d=0.0, s=1.0)"),
            ("btn_balanced", "balanced", "2. d CÂN BẰNG (d=0.5, s=0.5)"),
            ("btn_high", "high", "3. d CAO (d=0.95, s=0.05)"),
        ]

        for bid, ckey, label in case_buttons:
            brect = pygame.Rect(x, y, PANEL_WIDTH - 32, 28)
            is_active = (self.current_case_key == ckey)
            fill_c = (41, 128, 185) if is_active else (38, 45, 56)
            border_c = (100, 180, 240) if is_active else (60, 70, 85)
            pygame.draw.rect(self.screen, fill_c, brect, border_radius=4)
            pygame.draw.rect(self.screen, border_c, brect, width=1, border_radius=4)

            lbl = self.f_bold.render(label, True, (255, 255, 255) if is_active else (190, 200, 215))
            self.screen.blit(lbl, (x + 10, y + 6))
            buttons.append((bid, brect))
            y += 33

        y += 4

        # Hộp giải thích cơ chế trường hợp đang chọn
        c = self.cases[self.current_case_key]
        desc_box = pygame.Rect(x, y, PANEL_WIDTH - 32, 118)
        pygame.draw.rect(self.screen, (32, 38, 48), desc_box, border_radius=6)
        pygame.draw.rect(self.screen, c["highlight_color"], desc_box, width=1, border_radius=6)

        tag_lbl = self.f_bold.render(f"▶ CƠ CHẾ: {c['tag']}", True, c["highlight_color"])
        self.screen.blit(tag_lbl, (x + 10, y + 8))

        dy = y + 26
        for line in c["desc"].split("\n"):
            self.screen.blit(self.f_small.render(line, True, (215, 225, 235)), (x + 10, dy))
            dy += 17

        y += 126

        # Thống kê thời gian thực
        counts = self.sim.count_states()
        active = self.sim.active_cases()

        step_str = f"Bước: {self.step} ngày"
        active_str = f"Đang bệnh (I+S): {active}"
        self.screen.blit(self.f_bold.render(step_str, True, (52, 152, 219)), (x, y))
        self.screen.blit(self.f_bold.render(active_str, True, (231, 76, 60) if active > 0 else (46, 204, 113)), (x + 180, y))
        y += 20

        # Thanh trạng thái các màu
        stat_items = [
            (f"H: {counts['H']}", COLORS["H"]),
            (f"I: {counts['I']}", COLORS["I"]),
            (f"S: {counts['S']}", COLORS["S"]),
            (f"R: {counts['R']}", (180, 195, 205)),
            (f"Dead: {counts['Dead']}", (210, 75, 75)),
        ]
        sx = x
        for text, col in stat_items:
            pygame.draw.circle(self.screen, col, (sx + 5, y + 8), 4)
            self.screen.blit(self.f_main.render(text, True, (230, 235, 245)), (sx + 14, y))
            sx += 80
        y += 24

        # Mini đồ thị động (Real-time Timeline)
        graph_box = pygame.Rect(x, y, PANEL_WIDTH - 32, 105)
        pygame.draw.rect(self.screen, (20, 24, 30), graph_box, border_radius=4)
        pygame.draw.rect(self.screen, (50, 60, 75), graph_box, width=1, border_radius=4)

        hist = self.sim.history
        total_steps = len(hist["H"])
        pop_max = float(self.sim.initial_population)

        if total_steps > 1:
            gx, gy, gw, gh = graph_box.x + 8, graph_box.y + 8, graph_box.width - 16, graph_box.height - 16
            for curve_key, col in [("S", (231, 76, 60)), ("R", (180, 195, 205)), ("Dead", (210, 75, 75))]:
                pts = []
                for s_idx, val in enumerate(hist[curve_key]):
                    px_pt = gx + (s_idx / max(1, total_steps - 1)) * gw
                    py_pt = gy + gh - (val / pop_max) * gh
                    pts.append((px_pt, py_pt))
                if len(pts) > 1:
                    pygame.draw.lines(self.screen, col, False, pts, 2)

        # Legend của mini đồ thị
        self.screen.blit(self.f_small.render("Đồ thị thời gian:", True, (150, 160, 170)), (x + 10, y + 6))
        self.screen.blit(self.f_small.render("■ Đỏ: Bệnh (S)", True, (231, 76, 60)), (x + 110, y + 6))
        self.screen.blit(self.f_small.render("■ Xám: Khỏi (R)", True, (180, 195, 205)), (x + 200, y + 6))
        self.screen.blit(self.f_small.render("■ Nâu: Chết", True, (210, 75, 75)), (x + 295, y + 6))

        y += 114

        # Kết quả khi dịch kết thúc
        if active == 0:
            box_fin = pygame.Rect(x, y, PANEL_WIDTH - 32, 42)
            pygame.draw.rect(self.screen, (26, 68, 42), box_fin, border_radius=5)
            pygame.draw.rect(self.screen, (46, 204, 113), box_fin, width=1, border_radius=5)
            fin_text = f"✓ DỊCH ĐÃ TẮT TẠI BƯỚC {self.step}! (R = {counts['R']}, Dead = {counts['Dead']})"
            self.screen.blit(self.f_bold.render(fin_text, True, (46, 204, 113)), (x + 12, y + 12))
            y += 48
        else:
            y += 4

        # Các nút điều khiển mô phỏng
        btn_play_lbl = "Tạm Dừng (Pause)" if self.running else "Chạy (Play)"
        btn_play_rect = pygame.Rect(x, y, 130, 32)
        pygame.draw.rect(self.screen, (41, 128, 185) if not self.running else (192, 57, 43), btn_play_rect, border_radius=4)
        lbl = self.f_bold.render(btn_play_lbl, True, (255, 255, 255))
        self.screen.blit(lbl, lbl.get_rect(center=btn_play_rect.center))
        buttons.append(("btn_play", btn_play_rect))

        btn_step_rect = pygame.Rect(x + 140, y, 130, 32)
        pygame.draw.rect(self.screen, (52, 73, 94), btn_step_rect, border_radius=4)
        lbl = self.f_bold.render("Bước kế (+1)", True, (255, 255, 255))
        self.screen.blit(lbl, lbl.get_rect(center=btn_step_rect.center))
        buttons.append(("btn_step", btn_step_rect))

        btn_reset_rect = pygame.Rect(x + 280, y, PANEL_WIDTH - 32 - 280, 32)
        pygame.draw.rect(self.screen, (70, 80, 95), btn_reset_rect, border_radius=4)
        lbl = self.f_bold.render("Reset", True, (255, 255, 255))
        self.screen.blit(lbl, lbl.get_rect(center=btn_reset_rect.center))
        buttons.append(("btn_reset", btn_reset_rect))

        y += 40

        # Nút tốc độ và Nút Toggle Highlight Barrier
        fps_lbl = f"Tốc độ: {self.fps_mode} FPS"
        btn_fps_rect = pygame.Rect(x, y, 170, 28)
        pygame.draw.rect(self.screen, (45, 55, 70), btn_fps_rect, border_radius=4)
        lbl = self.f_bold.render(fps_lbl, True, (230, 235, 245))
        self.screen.blit(lbl, lbl.get_rect(center=btn_fps_rect.center))
        buttons.append(("btn_fps", btn_fps_rect))

        glow_lbl = "Highlight R: BẬT" if self.highlight_barriers else "Highlight R: TẮT"
        btn_glow_rect = pygame.Rect(x + 180, y, PANEL_WIDTH - 32 - 180, 28)
        pygame.draw.rect(self.screen, (39, 174, 96) if self.highlight_barriers else (60, 70, 80), btn_glow_rect, border_radius=4)
        lbl = self.f_bold.render(glow_lbl, True, (255, 255, 255))
        self.screen.blit(lbl, lbl.get_rect(center=btn_glow_rect.center))
        buttons.append(("btn_glow", btn_glow_rect))

        y += 36

        # Hướng dẫn phím tắt
        help_txt = "Phím tắt: Space (Play/Pause) | Phím → (Bước kế) | R (Reset) | 1, 2, 3 (Đổi kịch bản)"
        self.screen.blit(self.f_small.render(help_txt, True, (130, 140, 155)), (x, self.screen_h - 22))

        return buttons

    def handle_click(self, pos, buttons):
        for bid, rect in buttons:
            if rect.collidepoint(pos):
                if bid == "btn_low":
                    self.current_case_key = "low"
                    self.init_simulation()
                elif bid == "btn_balanced":
                    self.current_case_key = "balanced"
                    self.init_simulation()
                elif bid == "btn_high":
                    self.current_case_key = "high"
                    self.init_simulation()
                elif bid == "btn_play":
                    if self.sim.active_cases() > 0:
                        self.running = not self.running
                    else:
                        self.init_simulation()
                        self.running = True
                elif bid == "btn_step":
                    self.running = False
                    self.do_step()
                elif bid == "btn_reset":
                    self.init_simulation()
                elif bid == "btn_fps":
                    if self.fps_mode == 1:
                        self.fps_mode = 5
                    elif self.fps_mode == 5:
                        self.fps_mode = 15
                    else:
                        self.fps_mode = 1
                elif bid == "btn_glow":
                    self.highlight_barriers = not self.highlight_barriers
                return True
        return False

    def run(self):
        running_app = True
        step_timer = 0

        while running_app:
            dt = self.clock.tick(30)
            step_timer += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running_app = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos, buttons)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.sim.active_cases() > 0:
                            self.running = not self.running
                        else:
                            self.init_simulation()
                            self.running = True
                    elif event.key == pygame.K_RIGHT:
                        self.running = False
                        self.do_step()
                    elif event.key == pygame.K_r:
                        self.init_simulation()
                    elif event.key == pygame.K_1:
                        self.current_case_key = "low"
                        self.init_simulation()
                    elif event.key == pygame.K_2:
                        self.current_case_key = "balanced"
                        self.init_simulation()
                    elif event.key == pygame.K_3:
                        self.current_case_key = "high"
                        self.init_simulation()

            target_interval = 1000 // self.fps_mode
            if self.running and step_timer >= target_interval:
                self.do_step()
                step_timer = 0

            self.screen.fill(COLORS["BACKGROUND"])
            self.draw_grid()
            buttons = self.draw_panel()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


def main():
    app = Task2DynamicsGUI()
    app.run()


if __name__ == "__main__":
    main()
