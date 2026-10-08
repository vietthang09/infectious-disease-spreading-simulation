import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import random

# Định nghĩa các hằng số trạng thái
H, I, S, R, DEAD = 0, 1, 2, 3, 4

class Agent:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.state = H
        self.days_in_state = 0

class Simulation:
    def __init__(self, grid_size=30, pop_size=400, p=0.3, N=5, T_sick=7, d=0.1, seed=None):
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
            
        self.grid_size = grid_size
        self.p = p          # Xác suất lây nhiễm khi tiếp xúc
        self.N = N          # Số ngày ủ bệnh
        self.T_sick = T_sick # Số ngày phát bệnh
        self.d = d          # Tỷ lệ tử vong
        self.s = 1.0 - d    # Tỷ lệ phục hồi
        
        self.agents = []
        self.grid = np.full((grid_size, grid_size), None)
        
        # Khởi tạo quần thể ban đầu
        positions = random.sample([(i, j) for i in range(grid_size) for j in range(grid_size)], pop_size)
        for x, y in positions:
            agent = Agent(x, y)
            self.agents.append(agent)
            self.grid[x, y] = agent
            
        # Chọn Bệnh nhân số 0 (Patient Zero)
        patient_zero = self.agents[0]
        patient_zero.state = I
        patient_zero.days_in_state = 0
        
        self.time_step = 0
        self.total_deaths = 0

    def get_neighbors(self, x, y):
        # Thiết lập biên tuần hoàn (periodic boundaries)
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = (x + dx) % self.grid_size, (y + dy) % self.grid_size
                if self.grid[nx, ny] is not None:
                    neighbors.append(self.grid[nx, ny])
        return neighbors

    def step(self):
        new_grid = np.full((self.grid_size, self.grid_size), None)
        
        # 1. Giai đoạn Di chuyển
        for agent in self.agents:
            if agent.state == DEAD:
                continue
            
            # Di chuyển ngẫu nhiên đến các ô kề cạnh hoặc đứng yên
            dx, dy = random.choice([(0,0), (-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)])
            nx, ny = (agent.x + dx) % self.grid_size, (agent.y + dy) % self.grid_size
            
            # Kiểm tra ô trống trước khi chuyển vào
            if new_grid[nx, ny] is None:
                agent.x, agent.y = nx, ny
            new_grid[agent.x, agent.y] = agent
            
        self.grid = new_grid

        # 2. Giai đoạn Lây nhiễm và Cập nhật trạng thái
        states_to_update = []
        for agent in self.agents:
            if agent.state == DEAD:
                continue
                
            agent.days_in_state += 1
            
            if agent.state == H:
                # Tính xác suất lây nhiễm dựa trên số người bệnh xung quanh
                neighbors = self.get_neighbors(agent.x, agent.y)
                sick_neighbors = sum(1 for n in neighbors if n.state == S)
                infection_prob = 1 - (1 - self.p) ** sick_neighbors
                
                if random.random() < infection_prob:
                    states_to_update.append((agent, I))
                    
            elif agent.state == I:
                # Đã hết thời gian ủ bệnh
                if agent.days_in_state >= self.N:
                    states_to_update.append((agent, S))
                    
            elif agent.state == S:
                # Đã qua thời gian phát bệnh, xác định sống hay chết
                if agent.days_in_state >= self.T_sick:
                    if random.random() < self.d:
                        states_to_update.append((agent, DEAD))
                        self.total_deaths += 1
                    else:
                        states_to_update.append((agent, R))

        # Áp dụng các thay đổi
        for agent, new_state in states_to_update:
            agent.state = new_state
            agent.days_in_state = 0
            if new_state == DEAD:
                self.grid[agent.x, agent.y] = None # Loại bỏ hoàn toàn khỏi lưới

        self.time_step += 1
        
        # Trả về True nếu vẫn còn người nhiễm/bệnh
        active_cases = sum(1 for a in self.agents if a.state in [I, S])
        return active_cases > 0

    def get_grid_colors(self):
        # Ánh xạ trạng thái sang giá trị số để vẽ màu
        # 0: Trống/Chết, 1: H, 2: I, 3: S, 4: R
        color_grid = np.zeros((self.grid_size, self.grid_size))
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                agent = self.grid[x, y]
                if agent is None or agent.state == DEAD:
                    color_grid[x, y] = 0
                elif agent.state == H:
                    color_grid[x, y] = 1
                elif agent.state == I:
                    color_grid[x, y] = 2
                elif agent.state == S:
                    color_grid[x, y] = 3
                elif agent.state == R:
                    color_grid[x, y] = 4
        return color_grid

def run_animation():
    # Khởi tạo mô phỏng
    sim = Simulation(grid_size=40, pop_size=600, p=0.4, N=4, T_sick=6, d=0.1)
    
    # Thiết lập matplotlib
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Thiết lập bảng màu mã hóa trạng thái
    cmap = mcolors.ListedColormap(['white', 'blue', 'yellow', 'red', 'green'])
    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)
    
    # Vẽ khung hình đầu tiên
    img = ax.imshow(sim.get_grid_colors(), cmap=cmap, norm=norm)
    
    # Tạo chú thích (Legend)
    labels = ['Empty / Dead', 'Healthy (H)', 'Infected (I)', 'Sick (S)', 'Recovered (R)']
    colors = ['white', 'blue', 'yellow', 'red', 'green']
    patches = [mpatches.Patch(color=colors[i], label=labels[i]) for i in range(len(labels))]
    
    # Bố trí chú thích ở cạnh bên đồ thị
    ax.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    
    # Tắt hiển thị các trục số
    ax.set_xticks([])
    ax.set_yticks([])

    # Hàm cập nhật đồ họa mỗi bước chạy
    def update(frame):
        is_active = sim.step()
        img.set_data(sim.get_grid_colors())
        
        # Thống kê nhanh trên tiêu đề
        h_count = sum(1 for a in sim.agents if a.state == H)
        i_count = sum(1 for a in sim.agents if a.state == I)
        s_count = sum(1 for a in sim.agents if a.state == S)
        r_count = sum(1 for a in sim.agents if a.state == R)
        
        ax.set_title(f"Day: {sim.time_step} | H:{h_count} I:{i_count} S:{s_count} R:{r_count} Dead:{sim.total_deaths}")
        
        if not is_active:
            ani.event_source.stop() # Dừng hiệu ứng khi dịch kết thúc
            
        return [img]
        
    # Tạo đối tượng animation (interval=200ms cho mỗi khung hình)
    ani = animation.FuncAnimation(fig, update, frames=1000, interval=200, blit=False)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_animation()