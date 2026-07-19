import numpy as np
import random
from agent import Agent

class Simulation:
    def __init__(self, config):
        self.config = config
        self._validate_config()
        self.width = config['grid_width']
        self.height = config['grid_height']

        self.grid = np.empty((self.width, self.height), dtype=object)
        self.grid.fill(None)
        self.agents_list = []
        self.history = {"H": [], "I": [], "S": [], "R": [], "Dead": []}
        self.setup_population()
        self.initial_population = len(self.agents_list)
        self.record_history()

    def _validate_config(self):
        required = ("grid_width", "grid_height", "initial_population", "p", "N", "d", "s")
        missing = [key for key in required if key not in self.config]
        if missing:
            raise ValueError(f"Missing simulation config values: {', '.join(missing)}")
        if not 0.0 <= self.config["p"] <= 1.0:
            raise ValueError("p must be between 0 and 1")
        if not 0.0 <= self.config["d"] <= 1.0 or not 0.0 <= self.config["s"] <= 1.0:
            raise ValueError("d and s must be between 0 and 1")
        if abs(self.config["d"] + self.config["s"] - 1.0) > 1e-9:
            raise ValueError("d and s must satisfy d + s = 1")
        if self.config["N"] < 1 or self.config.get("sick_duration", self.config["N"]) < 1:
            raise ValueError("N and sick_duration must be positive")

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

        # Infection phase: p is a per-contact risk. If a Healthy agent has k
        # Sick neighbours, the chance of at least one successful transmission is
        # 1 - (1 - p) ** k.
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
                    infection_probability = 1 - (1 - self.config["p"]) ** sick_neighbors
                    if random.random() < infection_probability:
                        new_infections.append(agent)
        
        newly_infected = set(new_infections)
        for agent in newly_infected:
            agent.state = "I"
            agent.timer = 0

        # State transition phase: Infected agents incubate for N steps, then
        # Sick agents remain infectious for N steps before recovery or death.
        dead_agents = []
        for item in self.agents_list:
            agent = item["agent"]

            if agent.state == "I":
                # Infection starts at timer 0. Agents infected during this step
                # begin incubation on the next step, avoiding an off-by-one day.
                if agent in newly_infected:
                    continue
                agent.timer += 1
                if agent.timer >= self.config["N"]:
                    agent.state = "S"
                    agent.timer = 0

            elif agent.state == "S":
                agent.timer += 1
                if agent.timer >= self.config.get("sick_duration", self.config["N"]):
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
        counts = self.count_states()

        self.history['H'].append(counts["H"])
        self.history['I'].append(counts["I"])
        self.history['S'].append(counts["S"])
        self.history['R'].append(counts["R"])
        self.history['Dead'].append(counts["Dead"])

    def count_states(self):
        return {
            "H": sum(1 for item in self.agents_list if item['agent'].state == 'H'),
            "I": sum(1 for item in self.agents_list if item['agent'].state == 'I'),
            "S": sum(1 for item in self.agents_list if item['agent'].state == 'S'),
            "R": sum(1 for item in self.agents_list if item['agent'].state == 'R'),
            "Dead": self.initial_population - len(self.agents_list),
        }

    def active_cases(self):
        if not self.history["I"]:
            return sum(1 for item in self.agents_list if item["agent"].state in ("I", "S"))
        return self.history["I"][-1] + self.history["S"][-1]
