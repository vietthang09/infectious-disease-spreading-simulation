"""
Giao diện đồ họa Pygame trực quan:
Mô phỏng trường hợp F0 bị triệt tiêu vì xung quanh không có cá thể để lây.

Các tính năng nổi bật trên GUI:
1. Hiển thị lưới 2D (60 x 40 ô) với các màu sắc chuẩn:
   - Xanh lá: Healthy (H)
   - Vàng: Infected (I - ủ bệnh)
   - Đỏ: Sick (S - lây lan)
   - Xám: Recovered (R)
2. Highlight đặc biệt cho F0:
   - Vòng hào quang sáng bao quanh F0.
   - Khung viền màu cam/vàng bao quanh 8 ô lân cận (Moore neighborhood) của F0
     để người xem thấy rõ: "Vùng tiếp xúc này hoàn toàn trống (k = 0)!".
3. Bảng điều khiển (Control Panel) bên phải:
   - Hiển thị tọa độ F0, trạng thái (I/S/R/Dead), timer ủ bệnh/bệnh.
   - Số cá thể kề cận (k) và nguy cơ lây nhiễm (0.0%).
   - Nút Play/Pause, Step (+1), Reset, Tốc độ (1 FPS / 5 FPS).
   - Chọn nhanh 2 kịch bản:
       * Kịch bản A: Mật độ thưa (Pop=20, di chuyển tự do)
       * Kịch bản B: Giãn cách R=0 (Pop=800, đứng yên)
"""

import sys
import pygame
from copy import deepcopy

from config import COLORS, CONFIG
from simulation import Simulation
from agent import Agent


PANEL_WIDTH = 380
FPS_SLOW = 1
FPS_FAST = 5


class ExtinctionGUIApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.cell_size = CONFIG["cell_size"]
        self.grid_width = CONFIG["grid_width"]
        self.grid_height = CONFIG["grid_height"]
        self.grid_pixel_w = self.grid_width * self.cell_size
        self.grid_pixel_h = self.grid_height * self.cell_size

        self.screen_w = self.grid_pixel_w + PANEL_WIDTH
        self.screen_h = max(self.grid_pixel_h, 620)

        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption("Mô Phỏng Dịch Bệnh — F0 Bị Triệt Tiêu (Zero Contacts)")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("arial", 18, bold=True)
        self.font_bold = pygame.font.SysFont("arial", 14, bold=True)
        self.font_main = pygame.font.SysFont("arial", 14)
        self.font_small = pygame.font.SysFont("arial", 12)

        # Trạng thái mô phỏng
        self.scenario = "sparse"  # "sparse" hoặc "lockdown"
        self.running = False
        self.speed = "Slow"  # "Slow" hoặc "Fast"
        self.step = 0
        self.sim = None
        self.f0_final_note = None

        self.reset_simulation()

    def reset_simulation(self):
        self.step = 0
        self.running = False
        self.f0_final_note = None

        cfg = deepcopy(CONFIG)
        if self.scenario == "sparse":
            cfg["initial_population"] = 20
            self.sim = Simulation(cfg)
            import random
            random.seed(3)
            self.sim.setup_population()
        else:
            cfg["initial_population"] = 800
            import random
            random.seed(8)
            self.sim = Simulation(cfg)

    def do_step(self):
        if self.sim.active_cases() == 0:
            self.running = False
            return

        self.step += 1

        # Nếu là chế độ lockdown (R=0): giữ nguyên vị trí, chỉ cập nhật lây nhiễm và chuyển trạng thái
        if self.scenario == "lockdown":
            import random
            # Phase 2: Infection
            new_infections = []
            for item in self.sim.agents_list:
                x, y = item["pos"]
                agent = item["agent"]
                if agent.state == "H":
                    nbrs = self.sim.get_neighbors(x, y)
                    sick_nbrs = sum(
                        1 for nx, ny in nbrs
                        if self.sim.grid[nx, ny] is not None and self.sim.grid[nx, ny].state == "S"
                    )
                    if sick_nbrs > 0:
                        prob = (
                            self.sim.config["p"]
                            if self.sim.config.get("flat_infection_rate", False)
                            else 1 - (1 - self.sim.config["p"]) ** sick_nbrs
                        )
                        if random.random() < prob:
                            new_infections.append(agent)

            for agent in set(new_infections):
                agent.state = "I"
                agent.timer = 0

            # Phase 3: Transition
            dead_agents = []
            for item in self.sim.agents_list:
                agent = item["agent"]
                if agent.state == "I":
                    if agent in set(new_infections):
                        continue
                    agent.timer += 1
                    if agent.timer >= self.sim.config["N"]:
                        agent.state = "S"
                        agent.timer = 0
                elif agent.state == "S":
                    agent.timer += 1
                    if agent.timer >= self.sim.config.get("sick_duration", self.sim.config["N"]):
                        if random.random() < self.sim.config["d"]:
                            dead_agents.append(item)
                        else:
                            agent.state = "R"

            # Phase 4: Death removal
            for item in dead_agents:
                x, y = item["pos"]
                self.sim.grid[x, y] = None
                if item in self.sim.agents_list:
                    self.sim.agents_list.remove(item)

            self.sim.record_history()
        else:
            self.sim.update_step()

        # Kiểm tra kết quả F0
        f0_item = next((it for it in self.sim.agents_list if it["agent"].id == 0), None)
        if f0_item is None and self.f0_final_note is None:
            self.f0_final_note = f"F0 Tử vong (Dead) tại bước {self.step}"
        elif f0_item and f0_item["agent"].state == "R" and self.f0_final_note is None:
            self.f0_final_note = f"F0 Hồi phục (R) tại bước {self.step}"

        if self.sim.active_cases() == 0:
            self.running = False

    def draw_grid_and_agents(self):
        # Vẽ lưới nền
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                agent = self.sim.grid[x, y]
                if agent is not None:
                    color = COLORS.get(agent.state, (200, 200, 200))
                    pygame.draw.rect(self.screen, color, rect)
                else:
                    pygame.draw.rect(self.screen, COLORS["GRID_LINE"], rect, 1)

        # Highlight F0 và 8 ô lân cận của F0
        f0_item = next((it for it in self.sim.agents_list if it["agent"].id == 0), None)
        if f0_item is not None:
            fx, fy = f0_item["pos"]
            f0_rect = pygame.Rect(fx * self.cell_size, fy * self.cell_size, self.cell_size, self.cell_size)

            # Vẽ viền 8 ô lân cận của F0 (Moore neighborhood) màu vàng cam
            neighbors = self.sim.get_neighbors(fx, fy)
            for nx, ny in neighbors:
                n_rect = pygame.Rect(nx * self.cell_size, ny * self.cell_size, self.cell_size, self.cell_size)
                # Vẽ viền đệm thể hiện không có ai
                pygame.draw.rect(self.screen, (243, 156, 18), n_rect, 1)

            # Vẽ hào quang F0 nhấp nháy
            pulse_rect = f0_rect.inflate(6, 6)
            pygame.draw.rect(self.screen, (255, 255, 0), pulse_rect, 2)
            pygame.draw.rect(self.screen, (255, 255, 255), f0_rect, 1)

    def draw_panel(self):
        px = self.grid_pixel_w
        panel_rect = pygame.Rect(px, 0, PANEL_WIDTH, self.screen_h)
        pygame.draw.rect(self.screen, (28, 32, 38), panel_rect)
        pygame.draw.line(self.screen, (52, 73, 94), (px, 0), (px, self.screen_h), 2)

        x = px + 18
        y = 15

        # Tiêu đề
        lbl_title = self.font_title.render("MÔ PHỎNG F0 TRIỆT TIÊU", True, (241, 196, 15))
        self.screen.blit(lbl_title, (x, y))
        y += 24
        lbl_sub = self.font_small.render("(F0 Extinction Due to Zero Contacts)", True, (149, 165, 166))
        self.screen.blit(lbl_sub, (x, y))
        y += 28

        # Thông tin F0
        f0_item = next((it for it in self.sim.agents_list if it["agent"].id == 0), None)
        h_nbrs = 0
        if f0_item:
            f0_state = f0_item["agent"].state
            f0_timer = f0_item["agent"].timer
            f0_pos = f0_item["pos"]
            nbrs = self.sim.get_neighbors(f0_pos[0], f0_pos[1])
            h_nbrs = sum(1 for nx, ny in nbrs if self.sim.grid[nx, ny] and self.sim.grid[nx, ny].state == "H")
            f0_status_str = f"{f0_state} (timer={f0_timer})"
            f0_pos_str = str(f0_pos)
        else:
            f0_status_str = "Dead (Tử vong)"
            f0_pos_str = "Đã rời khỏi lưới"

        # Khung thẻ F0 Info
        card_rect = pygame.Rect(x, y, PANEL_WIDTH - 36, 110)
        pygame.draw.rect(self.screen, (38, 44, 53), card_rect, border_radius=6)
        pygame.draw.rect(self.screen, (64, 75, 89), card_rect, width=1, border_radius=6)

        cy = y + 10
        self.screen.blit(self.font_bold.render("THÔNG TIN BỆNH NHÂN ZERO (F0):", True, (230, 235, 245)), (x + 12, cy))
        cy += 22
        self.screen.blit(self.font_main.render(f"• Trạng thái: {f0_status_str}", True, (241, 196, 15) if f0_item else (231, 76, 60)), (x + 12, cy))
        cy += 20
        self.screen.blit(self.font_main.render(f"• Vị trí hiện tại: {f0_pos_str}", True, (200, 208, 220)), (x + 12, cy))
        cy += 20
        nbr_color = (46, 204, 113) if h_nbrs == 0 else (231, 76, 60)
        nbr_text = f"• H kề cận (8 ô): {h_nbrs} người  (Nguy cơ: 0.0%)" if h_nbrs == 0 else f"• H kề cận: {h_nbrs} người (Có tiếp xúc!)"
        self.screen.blit(self.font_bold.render(nbr_text, True, nbr_color), (x + 12, cy))

        y += 122

        # Thống kê quần thể
        counts = self.sim.count_states()
        self.screen.blit(self.font_bold.render(f"BƯỚC HIỆN TẠI: {self.step} (Ngày {self.step})", True, (52, 152, 219)), (x, y))
        y += 24

        stat_lines = [
            (f"Healthy (H): {counts['H']}", COLORS["H"]),
            (f"Infected (I): {counts['I']}", COLORS["I"]),
            (f"Sick (S): {counts['S']}", COLORS["S"]),
            (f"Recovered (R): {counts['R']}", COLORS["R"]),
            (f"Dead: {counts['Dead']}", (200, 70, 70)),
        ]
        for text, col in stat_lines:
            pygame.draw.circle(self.screen, col, (x + 6, y + 8), 5)
            self.screen.blit(self.font_main.render(text, True, (220, 225, 235)), (x + 18, y))
            y += 20

        y += 8
        active = self.sim.active_cases()
        active_col = (231, 76, 60) if active > 0 else (46, 204, 113)
        self.screen.blit(self.font_bold.render(f"Ca bệnh hoạt động (I+S): {active}", True, active_col), (x, y))
        y += 26

        # Kết luận ổ dịch
        if active == 0:
            box_res = pygame.Rect(x, y, PANEL_WIDTH - 36, 56)
            pygame.draw.rect(self.screen, (22, 60, 38), box_res, border_radius=5)
            pygame.draw.rect(self.screen, (46, 204, 113), box_res, width=1, border_radius=5)
            self.screen.blit(self.font_bold.render("✓ Ổ DỊCH ĐÃ BỊ TRIỆT TIÊU!", True, (46, 204, 113)), (x + 10, y + 8))
            msg = self.f0_final_note if self.f0_final_note else f"F0 hết bệnh tại bước {self.step}"
            self.screen.blit(self.font_small.render(f"{msg} | F1 = 0 ca", True, (230, 240, 235)), (x + 10, y + 30))
            y += 66
        else:
            y += 10

        # Kịch bản đang chọn
        scen_text = "Kịch bản A: Mật độ thưa (Pop=20)" if self.scenario == "sparse" else "Kịch bản B: Giãn cách R=0 (Pop=800)"
        self.screen.blit(self.font_bold.render(f"Đang chạy: {scen_text}", True, (243, 156, 18)), (x, y))
        y += 28

        # Vẽ các nút tương tác
        buttons = []

        btn_play_label = "Tạm Dừng (Pause)" if self.running else "Bắt Đầu (Play)"
        btn_play_rect = pygame.Rect(x, y, 160, 32)
        buttons.append(("toggle_play", btn_play_rect, btn_play_label, (41, 128, 185) if not self.running else (192, 57, 43)))

        btn_step_rect = pygame.Rect(x + 170, y, 160, 32)
        buttons.append(("step", btn_step_rect, "Bước kế (+1)", (52, 73, 94)))
        y += 40

        btn_speed_label = f"Tốc độ: {self.speed}"
        btn_speed_rect = pygame.Rect(x, y, 160, 30)
        buttons.append(("toggle_speed", btn_speed_rect, btn_speed_label, (70, 80, 95)))

        btn_reset_rect = pygame.Rect(x + 170, y, 160, 30)
        buttons.append(("reset", btn_reset_rect, "Làm mới (Reset)", (52, 73, 94)))
        y += 40

        # Chọn kịch bản
        self.screen.blit(self.font_bold.render("CHỌN KỊCH BẢN MÔ PHỎNG:", True, (200, 208, 220)), (x, y))
        y += 22

        btn_scen_a_rect = pygame.Rect(x, y, PANEL_WIDTH - 36, 28)
        color_a = (39, 174, 96) if self.scenario == "sparse" else (50, 60, 72)
        buttons.append(("set_sparse", btn_scen_a_rect, "A. Dân số thưa (Pop=20, Seed=3)", color_a))
        y += 34

        btn_scen_b_rect = pygame.Rect(x, y, PANEL_WIDTH - 36, 28)
        color_b = (39, 174, 96) if self.scenario == "lockdown" else (50, 60, 72)
        buttons.append(("set_lockdown", btn_scen_b_rect, "B. Giãn cách R=0 (Pop=800, Seed=8)", color_b))
        y += 38

        # Hướng dẫn
        note_txt = "Ghi chú: Ô có hào quang vàng là F0. Khung viền cam xung quanh là 8 ô lân cận (hoàn toàn trống)."
        self.screen.blit(self.font_small.render(note_txt, True, (130, 140, 155)), (x, self.screen_h - 26))

        # Render các nút
        for action_id, rect, label, fill_color in buttons:
            pygame.draw.rect(self.screen, fill_color, rect, border_radius=4)
            pygame.draw.rect(self.screen, (100, 115, 130), rect, width=1, border_radius=4)
            lbl = self.font_bold.render(label, True, (240, 245, 250))
            self.screen.blit(lbl, lbl.get_rect(center=rect.center))

        return buttons

    def handle_click(self, pos, buttons):
        for action_id, rect, label, fill_color in buttons:
            if rect.collidepoint(pos):
                if action_id == "toggle_play":
                    if self.sim.active_cases() > 0:
                        self.running = not self.running
                    else:
                        self.reset_simulation()
                        self.running = True
                elif action_id == "step":
                    self.running = False
                    self.do_step()
                elif action_id == "toggle_speed":
                    self.speed = "Fast" if self.speed == "Slow" else "Slow"
                elif action_id == "reset":
                    self.reset_simulation()
                elif action_id == "set_sparse":
                    self.scenario = "sparse"
                    self.reset_simulation()
                elif action_id == "set_lockdown":
                    self.scenario = "lockdown"
                    self.reset_simulation()
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
                            self.reset_simulation()
                            self.running = True
                    elif event.key == pygame.K_RIGHT:
                        self.running = False
                        self.do_step()
                    elif event.key == pygame.K_r:
                        self.reset_simulation()

            # Xử lý tự động chạy bước
            target_interval = 1000 // FPS_SLOW if self.speed == "Slow" else 1000 // FPS_FAST
            if self.running and step_timer >= target_interval:
                self.do_step()
                step_timer = 0

            self.screen.fill(COLORS["BACKGROUND"])
            self.draw_grid_and_agents()
            buttons = self.draw_panel()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


def main():
    app = ExtinctionGUIApp()
    app.run()


if __name__ == "__main__":
    main()
