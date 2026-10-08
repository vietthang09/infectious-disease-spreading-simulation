"""
Simulation engine — Cellular Finite State Automaton trên lưới 2D.

Mô hình gồm 4 trạng thái: Healthy (H), Infected (I), Sick (S), Recovered (R).
Đây là phần "luật chơi" chung, không phụ thuộc vào bất kỳ subtask cụ thể nào.

Quy trình mỗi bước (update_step):
    1. Movement phase  — agent di chuyển ngẫu nhiên sang ô kề trống
    2. Infection phase  — H tiếp xúc S → có thể chuyển thành I
    3. Transition phase — I ủ bệnh N bước → S; S bệnh sick_duration bước → chết hoặc R
    4. Death removal    — agent chết bị xóa khỏi grid

Tham số quan trọng (đọc từ config dict):
    p             : xác suất lây nhiễm mỗi lần tiếp xúc H–S
    N             : thời gian ủ bệnh (I → S)
    sick_duration : thời gian mang bệnh (S → R/chết), mặc định = N
    d             : xác suất chết khi hết thời gian sick
    s             : xác suất hồi phục (s = 1 - d)
"""

import numpy as np
import random
from agent import Agent


class Simulation:
    def __init__(self, config):
        self.config = config
        self._validate_config()
        self.width = config['grid_width']
        self.height = config['grid_height']

        # Grid 2D dạng numpy array of objects.
        # Mỗi ô chứa None (trống) hoặc 1 Agent.
        self.grid = np.empty((self.width, self.height), dtype=object)
        self.grid.fill(None)

        self.agents_list = []  # Danh sách dict {"agent": Agent, "pos": (x,y)}

        # History: ghi lại số lượng mỗi trạng thái sau mỗi bước.
        # Dùng cho cả animation (UI) lẫn tính metrics (experiment).
        self.history = {"H": [], "I": [], "S": [], "R": [], "Dead": []}

        self.setup_population()
        self.initial_population = len(self.agents_list)
        self.record_history()  # Ghi snapshot bước 0 (trước khi chạy)

    def _validate_config(self):
        """Kiểm tra config hợp lệ trước khi chạy, tránh lỗi ngầm."""
        required = ("grid_width", "grid_height", "initial_population", "p", "N", "d", "s")
        missing = [key for key in required if key not in self.config]
        if missing:
            raise ValueError(f"Missing simulation config values: {', '.join(missing)}")
        if not 0.0 <= self.config["p"] <= 1.0:
            raise ValueError("p must be between 0 and 1")
        if not 0.0 <= self.config["d"] <= 1.0 or not 0.0 <= self.config["s"] <= 1.0:
            raise ValueError("d and s must be between 0 and 1")
        # Ràng buộc quan trọng: d + s = 1 (đề bài yêu cầu)
        if abs(self.config["d"] + self.config["s"] - 1.0) > 1e-9:
            raise ValueError("d and s must satisfy d + s = 1")
        if self.config["N"] < 1 or self.config.get("sick_duration", self.config["N"]) < 1:
            raise ValueError("N and sick_duration must be positive")

    def setup_population(self):
        """Khởi tạo population trên grid.

        - Chọn ngẫu nhiên các ô để đặt agent.
        - Agent đầu tiên (i=0) là "patient zero" ở trạng thái Infected (I).
        - Tất cả agent còn lại ở trạng thái Healthy (H).

        Đây đúng yêu cầu đề bài: "one agent is patient zero in the Infected
        state (day 0 of incubation). All others are Healthy."
        """
        all_cells = [(x, y) for x in range(self.width) for y in range(self.height)]
        random.shuffle(all_cells)

        pop_size = min(self.config["initial_population"], len(all_cells))

        for i in range(pop_size):
            x, y = all_cells.pop()
            initial_state = "I" if i == 0 else "H"
            agent = Agent(agent_id=i, state=initial_state)

            self.grid[x, y] = agent
            self.agents_list.append({"agent": agent, "pos": (x, y)})

    def get_neighbors(self, x, y):
        """Trả về 8 ô kề (Moore neighborhood) với periodic boundaries.

        Periodic boundaries = lưới "quấn" lại (toroidal grid):
        - Ô ngoài cùng bên phải kề với ô ngoài cùng bên trái.
        - Ô trên cùng kề với ô dưới cùng.

        Thực hiện bằng phép modulo: nx = (x + dx) % width.

        Đề bài yêu cầu: "2D grid (periodic boundaries)".
        """
        neighbors = []

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Bỏ qua chính nó

                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                neighbors.append((nx, ny))
        return neighbors

    def update_step(self):
        """Thực hiện 1 bước thời gian của simulation.

        Gồm 4 pha tuần tự — thứ tự rất quan trọng để tránh artifact:
        1. Movement: di chuyển trước, rồi mới xét lây
        2. Infection: xét lây dựa trên vị trí MỚI sau di chuyển
        3. Transition: chuyển trạng thái I→S, S→R/chết
        4. Death removal: xóa agent chết khỏi grid
        """

        # ── PHASE 1: MOVEMENT ───────────────────────────────────────────
        # Mỗi agent sống thử di chuyển sang 1 ô kề trống, hoặc đứng yên.
        # Shuffle trước để không có agent nào được ưu tiên di chuyển.
        #
        # Đề bài: "Agents move randomly to a neighbouring cell (or stay)
        # each time step."
        random.shuffle(self.agents_list)

        for item in self.agents_list:
            x, y = item["pos"]
            agent = item["agent"]

            neighbors = self.get_neighbors(x, y)
            neighbors.append((x, y))  # Thêm ô hiện tại = option "đứng yên"

            # Lọc các ô trống hoặc chính ô mình đang đứng
            empty_spots = [
                (nx, ny)
                for nx, ny in neighbors
                if self.grid[nx, ny] is None or (nx == x and ny == y)
            ]

            if empty_spots:
                nx, ny = random.choice(empty_spots)
                if (nx, ny) != (x, y):
                    self.grid[nx, ny] = agent
                    self.grid[x, y] = None
                    item["pos"] = (nx, ny)

        # ── PHASE 2: INFECTION ──────────────────────────────────────────
        # Xét từng agent Healthy: đếm số hàng xóm Sick (k hàng xóm).
        # Xác suất bị lây = 1 - (1-p)^k  (mô hình per-contact risk).
        #
        # Tại sao dùng 1-(1-p)^k mà không phải k*p?
        #   → Vì p là xác suất lây MỖI lần tiếp xúc. Nếu có k lần tiếp xúc
        #     độc lập, xác suất KHÔNG bị lây = (1-p)^k, nên xác suất bị lây
        #     ít nhất 1 lần = 1 - (1-p)^k. Công thức này đảm bảo xác suất
        #     luôn nằm trong [0,1], khác với k*p có thể >1 khi k lớn.
        #
        # Đề bài: "p – infection risk per contact (when a Healthy agent is
        # adjacent to a Sick agent)."
        new_infections = []
        for item in self.agents_list:
            x, y = item["pos"]
            agent = item["agent"]

            if agent.state == "H":
                neighbors = self.get_neighbors(x, y)
                sick_neighbors = sum(
                    1
                    for nx, ny in neighbors
                    if self.grid[nx, ny] is not None and self.grid[nx, ny].state == "S"
                )

                if sick_neighbors > 0:
                    # Option: flat_infection_rate = True -> luôn là p dù gặp bao nhiêu người S
                    # Mặc định: False -> 1 - (1-p)^k (tính theo số tiếp xúc độc lập)
                    if self.config.get("flat_infection_rate", False):
                        infection_probability = self.config["p"]
                    else:
                        infection_probability = 1 - (1 - self.config["p"]) ** sick_neighbors

                    if random.random() < infection_probability:
                        new_infections.append(agent)

        # Áp dụng lây nhiễm: H → I, timer = 0 (bắt đầu ủ bệnh)
        newly_infected = set(new_infections)
        for agent in newly_infected:
            agent.state = "I"
            agent.timer = 0

        # ── PHASE 3: STATE TRANSITIONS ──────────────────────────────────
        #
        # Trạng thái I (Infected = đang ủ bệnh):
        #   - timer tăng 1 mỗi bước.
        #   - Khi timer >= N → chuyển sang S (Sick = lây được).
        #   - Agent MỚI bị lây ở phase 2 TRÊN sẽ bị skip (continue) để
        #     tránh off-by-one: ngày bị lây là ngày 0, bắt đầu đếm từ bước sau.
        #
        # Trạng thái S (Sick = đang lây):
        #   - timer tăng 1 mỗi bước.
        #   - Khi timer >= sick_duration → xổ số:
        #       • random() < d → chết (thêm vào dead_agents)
        #       • ngược lại     → hồi phục (R), miễn dịch vĩnh viễn
        #
        # Đề bài Task 2: "Fix all parameters except d and s (with s = 1 − d)."
        # → Cơ chế d/s nằm ở đây: dòng `if random.random() < self.config["d"]`.
        dead_agents = []
        for item in self.agents_list:
            agent = item["agent"]

            if agent.state == "I":
                # Skip agent vừa bị lây ở bước này — tránh đếm sai 1 ngày ủ
                if agent in newly_infected:
                    continue
                agent.timer += 1
                if agent.timer >= self.config["N"]:
                    agent.state = "S"
                    agent.timer = 0  # Reset timer để đếm thời gian sick

            elif agent.state == "S":
                agent.timer += 1
                if agent.timer >= self.config.get("sick_duration", self.config["N"]):
                    if random.random() < self.config["d"]:
                        # Chết: sẽ bị xóa ở phase 4
                        dead_agents.append(item)
                    else:
                        # Hồi phục: miễn dịch, không bị lây lại
                        agent.state = "R"

        # ── PHASE 4: DEATH REMOVAL ──────────────────────────────────────
        # Agent chết bị xóa khỏi grid (ô trở thành trống) VÀ khỏi
        # agents_list (không còn di chuyển hay lây).
        #
        # Đề bài: "Dead agents are removed from the grid (empty cell)."
        #
        # Lưu ý: việc xóa agent chết tạo thêm ô trống → agent khác dễ
        # di chuyển hơn → ảnh hưởng đến tốc độ lây lan. Đây là hiệu ứng
        # quan trọng mà Task 2 muốn phân tích: d cao → chết nhiều → ô
        # trống nhiều → lây chậm hơn, nhưng cũng → ít herd immunity.
        for item in dead_agents:
            x, y = item["pos"]
            self.grid[x, y] = None
            if item in self.agents_list:
                self.agents_list.remove(item)

        self.record_history()

    def record_history(self):
        """Ghi lại số agent mỗi trạng thái sau mỗi bước.

        History này phục vụ 2 mục đích:
        - Animation: UI đọc history[-1] để hiển thị real-time.
        - Metrics: experiment đọc toàn bộ history để tính peak_sick,
          epidemic_duration, v.v.
        """
        counts = self.count_states()

        self.history['H'].append(counts["H"])
        self.history['I'].append(counts["I"])
        self.history['S'].append(counts["S"])
        self.history['R'].append(counts["R"])
        self.history['Dead'].append(counts["Dead"])

    def count_states(self):
        """Đếm số agent ở mỗi trạng thái hiện tại.

        Dead = initial_population - len(agents_list) vì agent chết
        đã bị remove khỏi agents_list ở phase 4.
        """
        return {
            "H": sum(1 for item in self.agents_list if item['agent'].state == 'H'),
            "I": sum(1 for item in self.agents_list if item['agent'].state == 'I'),
            "S": sum(1 for item in self.agents_list if item['agent'].state == 'S'),
            "R": sum(1 for item in self.agents_list if item['agent'].state == 'R'),
            "Dead": self.initial_population - len(self.agents_list),
        }

    def active_cases(self):
        """Đếm số ca đang hoạt động (I + S).

        Dùng để kiểm tra điều kiện dừng: khi active_cases() == 0
        → dịch đã kết thúc tự nhiên (không còn ai lây hay bệnh).

        Ưu tiên đọc từ history (đã ghi sẵn) thay vì duyệt lại
        agents_list để tránh tính 2 lần.
        """
        if not self.history["I"]:
            return sum(1 for item in self.agents_list if item["agent"].state in ("I", "S"))
        return self.history["I"][-1] + self.history["S"][-1]
