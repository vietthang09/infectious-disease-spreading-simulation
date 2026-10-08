import numpy as np
import matplotlib.pyplot as plt
import random

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
        self.p = p          
        self.N = N          
        self.T_sick = T_sick 
        self.d = d          
        self.s = 1.0 - d    
        
        self.agents = []
        self.grid = np.full((grid_size, grid_size), None)
        
        positions = random.sample([(i, j) for i in range(grid_size) for j in range(grid_size)], pop_size)
        for x, y in positions:
            agent = Agent(x, y)
            self.agents.append(agent)
            self.grid[x, y] = agent
            
        patient_zero = self.agents[0]
        patient_zero.state = I
        patient_zero.days_in_state = 0
        
        self.time_step = 0
        self.total_deaths = 0

    def get_neighbors(self, x, y):
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
        for agent in self.agents:
            if agent.state == DEAD:
                continue
                
            dx, dy = random.choice([(0,0), (-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)])
            nx, ny = (agent.x + dx) % self.grid_size, (agent.y + dy) % self.grid_size
            
            if new_grid[nx, ny] is None:
                agent.x, agent.y = nx, ny
            new_grid[agent.x, agent.y] = agent
            
        self.grid = new_grid

        states_to_update = []
        for agent in self.agents:
            if agent.state == DEAD:
                continue
                
            agent.days_in_state += 1
            
            if agent.state == H:
                neighbors = self.get_neighbors(agent.x, agent.y)
                sick_neighbors = sum(1 for n in neighbors if n.state == S)
                
                infection_prob = 1 - (1 - self.p) ** sick_neighbors
                if random.random() < infection_prob:
                    states_to_update.append((agent, I))
                    
            elif agent.state == I:
                if agent.days_in_state >= self.N:
                    states_to_update.append((agent, S))
                    
            elif agent.state == S:
                if agent.days_in_state >= self.T_sick:
                    if random.random() < self.d:
                        states_to_update.append((agent, DEAD))
                        self.total_deaths += 1
                    else:
                        states_to_update.append((agent, R))

        for agent, new_state in states_to_update:
            agent.state = new_state
            agent.days_in_state = 0
            if new_state == DEAD:
                self.grid[agent.x, agent.y] = None 

        self.time_step += 1
        
        active_cases = sum(1 for a in self.agents if a.state in [I, S])
        return active_cases > 0

def run_experiments():
    d_values = np.arange(0.0, 1.0, 0.1)
    num_runs = 20
    
    avg_durations = []
    std_durations = []
    avg_deaths = []
    std_deaths = []
    
    for d in d_values:
        durations = []
        deaths = []
        for run in range(num_runs):
            sim = Simulation(grid_size=30, pop_size=300, p=0.3, N=5, T_sick=7, d=d, seed=run*100)
            while sim.step():
                pass
            durations.append(sim.time_step)
            deaths.append(sim.total_deaths)
            
        avg_durations.append(np.mean(durations))
        std_durations.append(np.std(durations))
        avg_deaths.append(np.mean(deaths))
        std_deaths.append(np.std(deaths))
        print(f"d = {d:.1f}: Duration = {np.mean(durations):.1f}±{np.std(durations):.1f}, Deaths = {np.mean(deaths):.1f}±{np.std(deaths):.1f}")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    ax1.errorbar(d_values, avg_durations, yerr=std_durations, marker='o', capsize=5, color='blue')
    ax1.set_xlabel('Death rate (d)')
    ax1.set_ylabel('Epidemic duration (steps)')
    ax1.set_title('Epidemic Duration vs Death Rate')
    ax1.grid(True)
    
    ax2.errorbar(d_values, avg_deaths, yerr=std_deaths, marker='s', capsize=5, color='red')
    ax2.set_xlabel('Death rate (d)')
    ax2.set_ylabel('Total deaths')
    ax2.set_title('Total Deaths vs Death Rate')
    ax2.grid(True)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_experiments()