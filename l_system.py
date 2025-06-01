import pygame
import math
import time

class LSystem:
    def __init__(self, axiom, rules, angle, start_pos=(400, 500), start_angle=-90):
        self.sentence = axiom
        self.rules = rules
        self.angle = angle
        self.start_pos = start_pos
        self.start_angle = start_angle
        self.generations = [axiom]  # Сохраняем все поколения

    def generate(self):
        next_sentence = ""
        for char in self.sentence:
            if char in self.rules:
                next_sentence += self.rules[char]
            else:
                next_sentence += char
        self.sentence = next_sentence
        self.generations.append(next_sentence)  # Сохраняем новое поколение

    def draw(self, screen, length=100, color=(255, 255, 255), generation_index=None):
        if generation_index is not None:
            current_sentence = self.generations[generation_index]
        else:
            current_sentence = self.sentence

        stack = []
        turtle_pos = list(self.start_pos)
        turtle_angle = self.start_angle
        
        for char in current_sentence:
            if char == 'F':
                new_x = turtle_pos[0] + length * math.cos(math.radians(turtle_angle))
                new_y = turtle_pos[1] + length * math.sin(math.radians(turtle_angle))
                pygame.draw.line(screen, color, turtle_pos, (new_x, new_y), 1)
                turtle_pos[0] = new_x
                turtle_pos[1] = new_y
            elif char == '+':
                turtle_angle += self.angle
            elif char == '-':
                turtle_angle -= self.angle
            elif char == '[':
                stack.append((turtle_pos[:], turtle_angle))
            elif char == ']':
                turtle_pos, turtle_angle = stack.pop()

def animate_koch_snowflake():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Анимация фрактала Коха")
    
    koch = LSystem(
        axiom="F--F--F",
        rules={"F": "F+F--F+F"},
        angle=60
    )
    
    max_iterations = 4
    for _ in range(max_iterations):
        koch.generate()
    
    running = True
    generation = 0
    last_update = time.time()
    update_interval = 1.0  # Секунд между обновлениями

    while running:
        current_time = time.time()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        if current_time - last_update >= update_interval:
            screen.fill((0, 0, 0))
            koch.draw(screen, length=2 * (4 - generation), color=(255, 255, 255), generation_index=generation)
            pygame.display.flip()
            
            generation = (generation + 1) % (max_iterations + 1)
            last_update = current_time
    
    pygame.quit()

def animate_sierpinski_triangle():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Анимация треугольника Серпинского")
    
    sierpinski = LSystem(
        axiom="F-G-G",
        rules={"F": "F-G+F+G-F", "G": "GG"},
        angle=120,
        start_pos=(100, 500)
    )
    
    max_iterations = 6
    for _ in range(max_iterations):
        sierpinski.generate()
    
    running = True
    generation = 0
    last_update = time.time()
    update_interval = 1.0

    while running:
        current_time = time.time()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        if current_time - last_update >= update_interval:
            screen.fill((0, 0, 0))
            sierpinski.draw(screen, length=2 * (6 - generation), color=(255, 255, 255), generation_index=generation)
            pygame.display.flip()
            
            generation = (generation + 1) % (max_iterations + 1)
            last_update = current_time
    
    pygame.quit()

def animate_dragon_curve():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Анимация кривой дракона")
    
    dragon = LSystem(
        axiom="FX",
        rules={"X": "X+YF+", "Y": "-FX-Y"},
        angle=90,
        start_pos=(400, 300)
    )
    
    max_iterations = 12
    for _ in range(max_iterations):
        dragon.generate()
    
    running = True
    generation = 0
    last_update = time.time()
    update_interval = 1.0

    while running:
        current_time = time.time()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        if current_time - last_update >= update_interval:
            screen.fill((0, 0, 0))
            dragon.draw(screen, length=3 * (12 - generation), color=(255, 255, 255), generation_index=generation)
            pygame.display.flip()
            
            generation = (generation + 1) % (max_iterations + 1)
            last_update = current_time
    
    pygame.quit()

if __name__ == "__main__":
    # Раскомментируйте нужную функцию для отображения соответствующего фрактала
    # animate_koch_snowflake()
    # animate_sierpinski_triangle()
    animate_dragon_curve() 