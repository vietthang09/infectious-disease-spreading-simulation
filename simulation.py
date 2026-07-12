import numpy as np
import random
from agent import Agent

class Simulation:
    def __init__(self, config):
        self.config = config
        self.width = config['grid_width']
        self.height = config['grid_height']

        self.grid = np.empty((self.width, self.height), dtype=object)
        self.grid.fill(None)
        self.agents_list = []
        self.history = {"H": [], "I": [], "S": [], "R": [], "Dead": []}
        self.setup_population()

    def setup_population(self):
        all_cells = [(x, y) for x in range(self.width) for y in range(self.height)]
        random.shuffle(all_cells)

        pop_size = min(self.config["initial_population"], len(all_cells))

        for i in range(pop_size):
            x, y = all_cells.pop()
            initial_state = "I" if i == 0  else "H"
            agent = Agent(agent_id=i, state=initial_state)

            self.grid[x, y] = agent
            self.agents_list.append({"agent": agent, "pos": (x, y)})

    def get_neighbors(self, x, y):
        neighbors = []

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                neighbors.append((nx, ny))
        return neighbors
    
    def update_step(self):
        # Movement phase: each living agent tries to move to an empty
        # neighbouring cell, or stays in its current cell.
        random.shuffle(self.agents_list)

        for item in self.agents_list:
            x, y = item["pos"]
            agent = item["agent"]

            neighbors = self.get_neighbors(x, y)
            neighbors.append((x, y))

            empty_spots = [(nx, ny) for nx, ny in neighbors if self.grid[nx, ny] is None or (nx == x and ny == y)]

            if empty_spots:
                nx, ny = random.choice(empty_spots)
                if (nx, ny) != (x, y):
                    self.grid[nx, ny] = agent
                    self.grid[x, y] = None
                    item["pos"] = (nx, ny)

        # Infection phase: healthy agents adjacent to at least one Sick agent
        # become Infected with probability p.
        new_infections = []
        for item in self.agents_list:
            x, y = item["pos"]
            agent = item["agent"]

            if agent.state == "H":
                neighbors = self.get_neighbors(x, y)
                has_sick_neighbor = any(self.grid[nx, ny] is not None and self.grid[nx, ny].state == "S" for nx, ny in neighbors)

                if has_sick_neighbor:
                    if random.random() < self.config["p"]:
                        new_infections.append(agent)
        
        for agent in new_infections:
            agent.state = "I"
            agent.timer = 0

        # State transition phase: Infected agents incubate for N steps, then
        # Sick agents remain infectious for N steps before recovery or death.
        dead_agents = []
        for item in self.agents_list:
            agent = item["agent"]

            if agent.state == "I":
                agent.timer += 1
                if agent.timer >= self.config["N"]:
                    agent.state = "S"
                    agent.timer = 0

            elif agent.state == "S":
                agent.timer += 1
                if agent.timer >= self.config["N"]:
                    if random.random() < self.config["d"]:
                        dead_agents.append(item)
                    else:
                        agent.state = "R"
        
        # Death removal phase: dead agents leave the grid and no longer move,
        # infect, or occupy a cell.
        for item in dead_agents:
            x, y = item["pos"]
            self.grid[x, y] = None
            if item in self.agents_list:
                self.agents_list.remove(item)

        self.record_history()

    def record_history(self):
        # History is used both by the animation and by Task 2 metrics.
        h_count = sum(1 for item in self.agents_list if item['agent'].state == 'H')
        i_count = sum(1 for item in self.agents_list if item['agent'].state == 'I')
        s_count = sum(1 for item in self.agents_list if item['agent'].state == 'S')
        r_count = sum(1 for item in self.agents_list if item['agent'].state == 'R')
        dead_count = self.config["initial_population"] - len(self.agents_list)

        self.history['H'].append(h_count)
        self.history['I'].append(i_count)
        self.history['S'].append(s_count)
        self.history['R'].append(r_count)
        self.history['Dead'].append(dead_count)

    def active_cases(self):
        if not self.history["I"]:
            return sum(1 for item in self.agents_list if item["agent"].state in ("I", "S"))
        return self.history["I"][-1] + self.history["S"][-1]
