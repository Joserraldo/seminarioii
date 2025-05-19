import pygame
import random
import math

# Inicialización de Pygame
pygame.init()
WIDTH, HEIGHT = 800, 700  # Aumenté la altura para el panel informativo
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cruce en T - Simulador con Carriles")

# Colores
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
RED = (200, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 200, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Colores para vehículos según su origen
COLOR_TOP = (0, 150, 255)    # Azul claro para los de arriba
COLOR_LEFT = (255, 100, 0)   # Naranja para los de izquierda
COLOR_RIGHT = (0, 200, 100)  # Verde claro para los de derecha

# Configuración
FPS = 60
SPAWN_RATE = 1200  # ms entre generación de vehículos
MIN_GREEN_TIME = 3000  # tiempo mínimo de luz verde
MAX_GREEN_TIME = 8000  # tiempo máximo de luz verde
YELLOW_TIME = 1500  # tiempo de luz amarilla

# Semáforo mejorado
class TrafficLight:
    def __init__(self, name, position):
        self.name = name
        self.position = position
        self.state = "RED"
        self.last_change = pygame.time.get_ticks()
        self.green_duration = MIN_GREEN_TIME
        self.yellow_duration = YELLOW_TIME
        self.waiting_vehicles = 0
        self.priority = 0
        
    def update(self, force_green=False):
        now = pygame.time.get_ticks()
        elapsed = now - self.last_change
        
        if force_green and self.state != "GREEN":
            self.change_to_green()
            return
            
        if self.state == "GREEN" and elapsed > self.green_duration:
            self.state = "YELLOW"
            self.last_change = now
        elif self.state == "YELLOW" and elapsed > self.yellow_duration:
            self.state = "RED"
            self.last_change = now
            
    def change_to_green(self):
        if self.state != "GREEN":
            self.state = "GREEN"
            self.last_change = pygame.time.get_ticks()
            # Tiempo verde proporcional al número de vehículos esperando
            self.green_duration = min(MAX_GREEN_TIME, 
                                    MIN_GREEN_TIME + self.waiting_vehicles * 500)
    
    def draw(self, surface):
        # Dibujar base del semáforo
        pygame.draw.rect(surface, BLACK, (self.position[0]-10, self.position[1]-30, 20, 60))
        
        # Dibujar luces (todas apagadas primero)
        colors = [BLACK, BLACK, BLACK]
        if self.state == "GREEN":
            colors[2] = GREEN
        elif self.state == "YELLOW":
            colors[1] = YELLOW
        else:
            colors[0] = RED
            
        for i, color in enumerate(colors):
            pygame.draw.circle(surface, color, (self.position[0], self.position[1]-20 + i*20), 8)

# Vehículo mejorado con carriles
class Vehicle:
    def __init__(self, origin):
        self.origin = origin
        self.speed = random.uniform(1.5, 2.5)
        
        # Asignar color según origen
        if origin == "TOP":
            self.color = COLOR_TOP
            self.lane = random.choice([-15, 0, 15])  # Desplazamiento en carril
        elif origin == "LEFT":
            self.color = COLOR_LEFT
            self.lane = random.choice([-15, 0, 15])
        else:  # RIGHT
            self.color = COLOR_RIGHT
            self.lane = random.choice([-15, 0, 15])
            
        self.x, self.y = self.start_position()
        self.route = self.choose_route()
        self.stopped = False
        self.waiting_time = 0
        self.size = random.randint(15, 20)
        
    def start_position(self):
        if self.origin == "TOP": 
            return (WIDTH//2 + self.lane, -30)
        elif self.origin == "LEFT": 
            return (-30, HEIGHT//2 + self.lane)
        else:  # RIGHT
            return (WIDTH + 30, HEIGHT//2 + self.lane)
        
    def choose_route(self):
        options = {
            "TOP": ["LEFT", "RIGHT", "STRAIGHT"],
            "LEFT": ["RIGHT", "STRAIGHT", "TOP"],
            "RIGHT": ["LEFT", "STRAIGHT", "TOP"]
        }
        return random.choice(options[self.origin])
    
    def is_at_intersection(self):
        if self.origin == "TOP" and 200 <= self.y <= 300:
            return True
        if self.origin == "LEFT" and 350 <= self.x <= 450:
            return True
        if self.origin == "RIGHT" and 350 <= self.x <= 450:
            return True
        return False
        
    def move(self, light_state):
        prev_stopped = self.stopped
        stop_position = {
            "TOP": 250,
            "LEFT": 360,
            "RIGHT": 440
        }
        
        # Verificar si debe detenerse
        if self.origin == "TOP":
            self.stopped = (self.y >= stop_position["TOP"] and 
                          light_state != "GREEN" and 
                          self.is_at_intersection())
            if not self.stopped:
                self.y += self.speed
                
        elif self.origin == "LEFT":
            self.stopped = (self.x >= stop_position["LEFT"] and 
                           light_state != "GREEN" and 
                           self.is_at_intersection())
            if not self.stopped:
                self.x += self.speed
                
        elif self.origin == "RIGHT":
            self.stopped = (self.x <= stop_position["RIGHT"] and 
                           light_state != "GREEN" and 
                           self.is_at_intersection())
            if not self.stopped:
                self.x -= self.speed
                
        # Actualizar tiempo de espera
        if self.stopped:
            self.waiting_time += 1
        else:
            self.waiting_time = 0
            
        # Si acaba de empezar a moverse después de estar detenido
        if prev_stopped and not self.stopped:
            return True
        return False
        
    def draw(self, surface):
        # Cambiar color si ha esperado mucho
        if self.waiting_time > 120:
            color = (min(255, self.color[0] + 50), 
                    max(0, self.color[1] - 30), 
                    max(0, self.color[2] - 30))
        else:
            color = self.color
            
        pygame.draw.rect(surface, color, (self.x, self.y, self.size, self.size))

# Función para dibujar la intersección con carriles
def draw_intersection(surface):
    # Carreteras principales
    pygame.draw.rect(surface, DARK_GRAY, (0, HEIGHT//2 - 100, WIDTH, 200))  # Horizontal
    pygame.draw.rect(surface, DARK_GRAY, (WIDTH//2 - 100, 0, 200, HEIGHT//2 + 100))  # Vertical
    
    # Marcas de carril (líneas discontinuas)
    for i in range(0, WIDTH, 40):
        if abs(i - WIDTH//2) > 120:  # No dibujar marcas en la intersección
            pygame.draw.rect(surface, YELLOW, (i, HEIGHT//2 - 2, 20, 4))
            # Carriles adicionales
            pygame.draw.rect(surface, YELLOW, (i, HEIGHT//2 - 22, 20, 4))
            pygame.draw.rect(surface, YELLOW, (i, HEIGHT//2 + 18, 20, 4))
            
    for i in range(0, HEIGHT//2 + 100, 40):
        if i < HEIGHT//2 - 100 or i > HEIGHT//2:  # No dibujar marcas en la intersección
            pygame.draw.rect(surface, YELLOW, (WIDTH//2 - 2, i, 4, 20))
            # Carriles adicionales
            pygame.draw.rect(surface, YELLOW, (WIDTH//2 - 22, i, 4, 20))
            pygame.draw.rect(surface, YELLOW, (WIDTH//2 + 18, i, 4, 20))

# Función para dibujar el panel informativo
def draw_info_panel(surface, lights, vehicles):
    panel_rect = pygame.Rect(0, 0, WIDTH, 50)
    pygame.draw.rect(surface, (40, 40, 40), panel_rect)
    
    font = pygame.font.SysFont('Arial', 16, bold=True)
    small_font = pygame.font.SysFont('Arial', 14)
    
    # Estado de los semáforos
    top_text = f"ARRIBA: {'VERDE' if lights['TOP'].state == 'GREEN' else 'AMARILLO' if lights['TOP'].state == 'YELLOW' else 'ROJO'}"
    left_text = f"IZQUIERDA: {'VERDE' if lights['LEFT'].state == 'GREEN' else 'AMARILLO' if lights['LEFT'].state == 'YELLOW' else 'ROJO'}"
    right_text = f"DERECHA: {'VERDE' if lights['RIGHT'].state == 'GREEN' else 'AMARILLO' if lights['RIGHT'].state == 'YELLOW' else 'ROJO'}"
    
    # Colores de texto según estado
    top_color = GREEN if lights['TOP'].state == 'GREEN' else YELLOW if lights['TOP'].state == 'YELLOW' else RED
    left_color = GREEN if lights['LEFT'].state == 'GREEN' else YELLOW if lights['LEFT'].state == 'YELLOW' else RED
    right_color = GREEN if lights['RIGHT'].state == 'GREEN' else YELLOW if lights['RIGHT'].state == 'YELLOW' else RED
    
    # Leyenda de colores de vehículos
    legend_text = "Leyenda: "
    
    # Renderizar textos
    texts = [
        (font.render(top_text, True, top_color), (20, 10)),
        (font.render(left_text, True, left_color), (220, 10)),
        (font.render(right_text, True, right_color), (420, 10)),
        (small_font.render(legend_text, True, WHITE), (20, 30)),
        (small_font.render("Arriba", True, COLOR_TOP), (100, 30)),
        (small_font.render("Izquierda", True, COLOR_LEFT), (170, 30)),
        (small_font.render("Derecha", True, COLOR_RIGHT), (260, 30)),
        (small_font.render(f"Vehículos totales: {len(vehicles)}", True, WHITE), (620, 10))
    ]
    
    for text, pos in texts:
        surface.blit(text, pos)

# Función principal
def main():
    clock = pygame.time.Clock()
    vehicles = []
    spawn_timer = 0
    
    # Semáforos
    lights = {
        "TOP": TrafficLight("TOP", (WIDTH//2, HEIGHT//2 - 50)),
        "LEFT": TrafficLight("LEFT", (WIDTH//2 - 50, HEIGHT//2 + 20)),
        "RIGHT": TrafficLight("RIGHT", (WIDTH//2 + 50, HEIGHT//2 + 20))
    }
    
    # Iniciar con un semáforo en verde
    lights["TOP"].change_to_green()
    
    running = True
    while running:
        # Manejo de eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
        # Limpiar pantalla
        win.fill(GRAY)
        draw_intersection(win)
        draw_info_panel(win, lights, vehicles)
        
        # Generar vehículos aleatorios
        spawn_timer += clock.get_time()
        if spawn_timer > SPAWN_RATE:
            origin = random.choice(["TOP", "LEFT", "RIGHT"])
            vehicles.append(Vehicle(origin))
            spawn_timer = 0
            
        # Contar vehículos esperando en cada dirección
        for light in lights.values():
            light.waiting_vehicles = 0
            light.priority = 0
            
        for vehicle in vehicles:
            if vehicle.stopped and vehicle.is_at_intersection():
                lights[vehicle.origin].waiting_vehicles += 1
                # Prioridad aumenta con el tiempo de espera
                lights[vehicle.origin].priority += vehicle.waiting_time / 10
                
        # Determinar qué semáforo debe estar en verde
        current_green = None
        for name, light in lights.items():
            if light.state == "GREEN":
                current_green = name
                break
                
        # Si no hay semáforo en verde, elegir el de mayor prioridad
        if current_green is None:
            max_priority = max(lights.values(), key=lambda x: x.priority)
            if max_priority.priority > 0:
                max_priority.change_to_green()
        else:
            # Si el semáforo actual ha terminado su tiempo verde
            current_light = lights[current_green]
            now = pygame.time.get_ticks()
            elapsed = now - current_light.last_change
            
            if elapsed > current_light.green_duration:
                # Buscar siguiente semáforo con mayor prioridad
                next_light = max(lights.values(), key=lambda x: x.priority)
                if next_light.priority > 0 and next_light != current_light:
                    current_light.state = "YELLOW"
                    current_light.last_change = now
                    
        # Actualizar semáforos
        for light in lights.values():
            light.update()
            
        # Mover y dibujar vehículos
        vehicles_to_remove = []
        for i, vehicle in enumerate(vehicles):
            started_moving = vehicle.move(lights[vehicle.origin].state)
            if started_moving:
                lights[vehicle.origin].waiting_vehicles = max(0, lights[vehicle.origin].waiting_vehicles - 1)
                
            vehicle.draw(win)
            
            # Eliminar vehículos que salieron de la pantalla
            if (vehicle.x < -50 or vehicle.x > WIDTH + 50 or 
                vehicle.y < -50 or vehicle.y > HEIGHT + 50):
                vehicles_to_remove.append(i)
                
        # Eliminar vehículos en orden inverso para no afectar los índices
        for i in sorted(vehicles_to_remove, reverse=True):
            vehicles.pop(i)
            
        # Dibujar semáforos
        for light in lights.values():
            light.draw(win)
            
        pygame.display.flip()
        clock.tick(FPS)
        
    pygame.quit()

if __name__ == "__main__":
    main()