import unittest
import numpy as np
import random
from copy import deepcopy

from config import CONFIG
from simulation import Simulation
from agent import Agent


class TestSimulation(unittest.TestCase):
    def setUp(self):
        self.config = deepcopy(CONFIG)
        self.config["p"] = 0.3
        self.config["N"] = 5
        self.config["sick_duration"] = 5
        self.config["d"] = 0.2
        self.config["s"] = 0.8

    def test_initial_condition(self):
        random.seed(42)
        np.random.seed(42)
        sim = Simulation(self.config)

        self.assertEqual(len(sim.agents_list), 800)
        self.assertEqual(sim.initial_population, 800)

        counts = sim.count_states()
        self.assertEqual(counts["I"], 1)
        self.assertEqual(counts["H"], 799)
        self.assertEqual(counts["S"], 0)
        self.assertEqual(counts["R"], 0)
        self.assertEqual(counts["Dead"], 0)

    def test_population_conservation(self):
        random.seed(123)
        np.random.seed(123)
        sim = Simulation(self.config)

        for _ in range(50):
            sim.update_step()
            counts = sim.count_states()
            total = counts["H"] + counts["I"] + counts["S"] + counts["R"] + counts["Dead"]
            self.assertEqual(total, 800)

    def test_incubation_timing(self):
        # Isolate one infected agent to verify incubation of exactly N steps
        custom_cfg = deepcopy(self.config)
        custom_cfg["initial_population"] = 1
        custom_cfg["N"] = 3
        custom_cfg["sick_duration"] = 4

        random.seed(1)
        np.random.seed(1)
        sim = Simulation(custom_cfg)

        agent = sim.agents_list[0]["agent"]
        self.assertEqual(agent.state, "I")
        self.assertEqual(agent.timer, 0)

        # Step 1: timer becomes 1
        sim.update_step()
        self.assertEqual(agent.state, "I")
        self.assertEqual(agent.timer, 1)

        # Step 2: timer becomes 2
        sim.update_step()
        self.assertEqual(agent.state, "I")
        self.assertEqual(agent.timer, 2)

        # Step 3: timer reaches N=3, transitions to S, timer resets to 0
        sim.update_step()
        self.assertEqual(agent.state, "S")
        self.assertEqual(agent.timer, 0)

    def test_boundary_death_rate_zero(self):
        # When d=0.0 and s=1.0, nobody dies
        custom_cfg = deepcopy(self.config)
        custom_cfg["d"] = 0.0
        custom_cfg["s"] = 1.0

        random.seed(101)
        np.random.seed(101)
        sim = Simulation(custom_cfg)

        for _ in range(100):
            sim.update_step()

        counts = sim.count_states()
        self.assertEqual(counts["Dead"], 0)
        self.assertGreater(counts["R"], 0)

    def test_boundary_death_rate_one(self):
        # When d=1.0 and s=0.0, nobody recovers (all infected die)
        custom_cfg = deepcopy(self.config)
        custom_cfg["d"] = 1.0
        custom_cfg["s"] = 0.0

        random.seed(101)
        np.random.seed(101)
        sim = Simulation(custom_cfg)

        for _ in range(100):
            sim.update_step()

        counts = sim.count_states()
        self.assertEqual(counts["R"], 0)
        self.assertGreater(counts["Dead"], 0)

    def test_reproducibility(self):
        # Identical seeds must produce identical state histories
        def run_sim(seed):
            random.seed(seed)
            np.random.seed(seed)
            sim = Simulation(self.config)
            for _ in range(30):
                sim.update_step()
            return sim.history

        hist1 = run_sim(999)
        hist2 = run_sim(999)
        self.assertEqual(hist1, hist2)

    def test_config_validation(self):
        invalid_cfg = deepcopy(self.config)
        invalid_cfg["d"] = 0.4
        invalid_cfg["s"] = 0.4  # sum != 1.0
        with self.assertRaises(ValueError):
            Simulation(invalid_cfg)


if __name__ == "__main__":
    unittest.main()
