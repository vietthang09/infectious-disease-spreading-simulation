import pygame
import sys
from config import CONFIG, COLORS
from simulation import Simulation
import matplotlib.pyplot as plt
import os 

def clear_old_plots():
    if not os.path.exists("plots_history"):
        os.makedirs("plots_history")
    else:
        for filename in os.listdir("plots_history"):
            file_path = os.path.join("plots_history", filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

def export_plot(history, step):
    plt.figure(figsize=(8, 5))

    plt.plot(history['H'], label='Healthy', color='#2ecc71')
    plt.plot(history['I'], label='Infected', color='#f1c40f')
    plt.plot(history['S'], label='Sick', color='#e74c3c')
    plt.plot(history['R'], label='Recovered', color='#95a5a6')
    plt.plot(history['Dead'], label='Dead', color='black')

    plt.title(f'Epidemic Simulation - Step {step}')
    plt.xlabel('Time Steps')
    plt.ylabel('Number of Agents')
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.6)

    filename = f"plots_history/epidemic_curve_step_{step:04d}.png"

    plt.savefig(filename)
    plt.close()

def main():

    clear_old_plots()

    pygame.init()

    cell_size = CONFIG["cell_size"]
    screen_width = CONFIG["grid_width"] * cell_size
    screen_height = CONFIG["grid_height"] * cell_size

    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Epidemic Simulation")
    clock = pygame.time.Clock()

    sim = Simulation(CONFIG)

    running = True
    step_count = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
        
        sim.update_step()
        step_count += 1

        screen.fill(COLORS["BACKGROUND"])

        for x in range(sim.width):
            for y in range(sim.height):
                agent = sim.grid[x, y]
                rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)

                if agent is not None:
                    pygame.draw.rect(screen, COLORS[agent.state], rect)
                else:
                    pygame.draw.rect(screen, COLORS["GRID_LINE"], rect, 1)

        h_count = sim.history['H'][-1]
        i_count = sim.history['I'][-1]
        s_count = sim.history['S'][-1]
        r_count = sim.history['R'][-1]
        dead_count = sim.history['Dead'][-1]

        pygame.display.set_caption(f"Step: {step_count} | H: {h_count} | I: {i_count} | S: {s_count} | R: {r_count} | Dead: {dead_count}")
        pygame.display.flip()

        export_plot(sim.history, step_count)

        clock.tick(CONFIG["fps"])

if __name__ == "__main__":
    main()