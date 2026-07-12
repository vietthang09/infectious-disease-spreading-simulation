import pygame

from config import COLORS


class Button:
    def __init__(self, rect, label, action, enabled=True):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action
        self.enabled = enabled

    def draw(self, screen, font):
        fill = (64, 72, 84) if self.enabled else (42, 46, 54)
        border = (120, 130, 145) if self.enabled else (72, 78, 88)
        text_color = (235, 238, 242) if self.enabled else (135, 140, 148)
        pygame.draw.rect(screen, fill, self.rect, border_radius=4)
        pygame.draw.rect(screen, border, self.rect, width=1, border_radius=4)
        label = font.render(self.label, True, text_color)
        screen.blit(label, label.get_rect(center=self.rect.center))

    def handle_click(self, pos):
        if self.enabled and self.rect.collidepoint(pos):
            self.action()
            return True
        return False


def draw_text(screen, font, text, x, y, color=(230, 234, 240)):
    screen.blit(font.render(text, True, color), (x, y))


def draw_grid(screen, sim, cell_size):
    for x in range(sim.width):
        for y in range(sim.height):
            agent = sim.grid[x, y]
            rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)

            if agent is not None:
                pygame.draw.rect(screen, COLORS[agent.state], rect)
            else:
                pygame.draw.rect(screen, COLORS["GRID_LINE"], rect, 1)
