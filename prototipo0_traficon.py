import cv2
from ultralytics import YOLO
import json
from datetime import datetime
import numpy as np

class SemaforoInteligente:
    def __init__(self):
        # Configuración de duración del semáforo
        self.duracion_verde_base = 10.0
        self.duracion_amarillo = 3.0
        self.duracion_rojo_base = 8.0
        
        # Estado actual
        self.estado = "VERDE"
        self.tiempo_inicio_estado = 0
        self.duracion_actual = self.duracion_verde_base
        
        # Contadores para estadísticas
        self.cambios_verde_a_amarillo = 0
        self.cambios_amarillo_a_rojo = 0
        self.cambios_rojo_a_verde = 0
        
    def calcular_duracion_adaptativa(self, vehiculos_detectados):
        """Calcula la duración adaptativa basada en el tráfico"""
        if self.estado == "VERDE":
            # Verde se extiende si hay mucho tráfico
            if vehiculos_detectados > 6:
                return self.duracion_verde_base + 8
            elif vehiculos_detectados > 3:
                return self.duracion_verde_base + 3
            else:
                return self.duracion_verde_base
        elif self.estado == "ROJO":
            # Rojo se reduce si hay poco tráfico
            if vehiculos_detectados < 2:
                return max(self.duracion_rojo_base - 3, 5)  # Mínimo 5 segundos
            else:
                return self.duracion_rojo_base
        else:  # AMARILLO
            return self.duracion_amarillo
    
    def actualizar(self, tiempo_actual, vehiculos_detectados):
        """Actualiza el estado del semáforo"""
        tiempo_en_estado = tiempo_actual - self.tiempo_inicio_estado
        
        # Verificar si es momento de cambiar de estado
        if tiempo_en_estado >= self.duracion_actual:
            if self.estado == "VERDE":
                self.estado = "AMARILLO"
                self.duracion_actual = self.duracion_amarillo
                self.cambios_verde_a_amarillo += 1
            elif self.estado == "AMARILLO":
                self.estado = "ROJO"
                self.duracion_actual = self.calcular_duracion_adaptativa(vehiculos_detectados)
                self.cambios_amarillo_a_rojo += 1
            elif self.estado == "ROJO":
                self.estado = "VERDE"
                self.duracion_actual = self.calcular_duracion_adaptativa(vehiculos_detectados)
                self.cambios_rojo_a_verde += 1
            
            self.tiempo_inicio_estado = tiempo_actual
        
        return self.estado
    
    def get_tiempo_restante(self, tiempo_actual):
        """Obtiene el tiempo restante en el estado actual"""
        tiempo_transcurrido = tiempo_actual - self.tiempo_inicio_estado
        return max(0, self.duracion_actual - tiempo_transcurrido)

def dibujar_semaforo_elegante(frame, estado, tiempo_restante):
    """Dibuja un semáforo elegante con efectos visuales"""
    # Posición del semáforo
    sem_x, sem_y = 50, 50
    
    # Fondo del semáforo
    cv2.rectangle(frame, (sem_x - 25, sem_y - 15), (sem_x + 25, sem_y + 125), (40, 40, 40), -1)
    cv2.rectangle(frame, (sem_x - 25, sem_y - 15), (sem_x + 25, sem_y + 125), (200, 200, 200), 2)
    
    # Configuración de luces
    luces = [
        ("ROJO", sem_y, (0, 0, 255)),
        ("AMARILLO", sem_y + 35, (0, 255, 255)),
        ("VERDE", sem_y + 70, (0, 255, 0))
    ]
    
    for nombre, pos_y, color in luces:
        if nombre == estado:
            # Luz activa con efecto de brillo
            cv2.circle(frame, (sem_x, pos_y), 18, color, -1)
            cv2.circle(frame, (sem_x, pos_y), 15, tuple(int(c * 1.3) for c in color), -1)
            cv2.circle(frame, (sem_x, pos_y), 10, (255, 255, 255), -1)
        else:
            # Luz apagada
            cv2.circle(frame, (sem_x, pos_y), 15, (60, 60, 60), -1)
            cv2.circle(frame, (sem_x, pos_y), 15, (100, 100, 100), 2)
    
    # Mostrar estado y tiempo restante
    cv2.putText(frame, f"{estado}", (sem_x - 30, sem_y + 150),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"{tiempo_restante:.1f}s", (sem_x - 25, sem_y + 175),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

def dibujar_estadisticas(frame, conteo_ids, semaforo, vehiculos_actuales):
    """Dibuja estadísticas elegantes en pantalla"""
    # Panel de estadísticas
    panel_x, panel_y = frame.shape[1] - 280, 20
    cv2.rectangle(frame, (panel_x - 10, panel_y - 10), (frame.shape[1] - 10, panel_y + 150), (0, 0, 0), -1)
    cv2.rectangle(frame, (panel_x - 10, panel_y - 10), (frame.shape[1] - 10, panel_y + 150), (100, 100, 100), 2)
    
    # Título
    cv2.putText(frame, "ESTADISTICAS DE TRAFICO", (panel_x, panel_y + 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Conteo total
    y_offset = panel_y + 35
    cv2.putText(frame, f"Personas: {len(conteo_ids['person'])}", (panel_x, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 255, 100), 1)
    cv2.putText(frame, f"Vehiculos: {len(conteo_ids['car'])}", (panel_x, y_offset + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 255, 100), 1)
    cv2.putText(frame, f"Motos: {len(conteo_ids['motorcycle'])}", (panel_x, y_offset + 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 255, 100), 1)
    
    # Tráfico actual
    cv2.putText(frame, f"Trafico actual: {vehiculos_actuales}", (panel_x, y_offset + 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 100), 1)
    
    # Estadísticas del semáforo
    cv2.putText(frame, f"Ciclos completados: {semaforo.cambios_rojo_a_verde}", (panel_x, y_offset + 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 255), 1)

def main():
    # Cargar modelo YOLOv8
    print("Cargando modelo YOLO...")
    model = YOLO("yolov8n.pt")
    
    # Video
    cap = cv2.VideoCapture("test.mp4")
    if not cap.isOpened():
        print("Error: No se pudo abrir el video 'test.mp4'")
        return
    
    # Configuración
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    
    # Zona de interés (ROI)
    x1_roi, y1_roi = 80, 70
    x2_roi, y2_roi = 700, 480
    
    # Diccionario para conteo único
    conteo_ids = {
        'person': set(),
        'car': set(),
        'motorcycle': set(),
        'truck': set(),
        'bus': set()
    }
    
    # Inicializar semáforo inteligente
    semaforo = SemaforoInteligente()
    tiempo_inicio = cv2.getTickCount() / cv2.getTickFrequency()
    
    # Variables de control
    frame_count = 0
    paused = False
    
    print("Iniciando simulación...")
    print("Controles:")
    print("  ESPACIO: Pausar/Reanudar")
    print("  'r': Reiniciar video")
    print("  'q': Salir")
    
    while cap.isOpened():
        if not paused:
            ret, frame = cap.read()
            if not ret:
                # Reiniciar video si llegó al final
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            frame_count += 1
        else:
            # Si está pausado, usar el último frame
            pass
        
        # Tiempo actual en segundos
        tiempo_actual = cv2.getTickCount() / cv2.getTickFrequency() - tiempo_inicio
        
        # Detección con seguimiento
        results = model.track(frame, persist=True, tracker="bytetrack.yaml")[0]
        
        boxes = results.boxes
        vehiculos_actuales = 0
        
        if boxes is not None and boxes.id is not None:
            ids = boxes.id.cpu().numpy().astype(int)
            cls = boxes.cls.cpu().numpy().astype(int)
            coords = boxes.xyxy.cpu().numpy().astype(int)
            
            for track_id, class_id, (x1, y1, x2, y2) in zip(ids, cls, coords):
                cls_name = model.names[class_id]
                
                # Centro del objeto
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                
                # Verificar si está dentro del ROI
                if x1_roi <= cx <= x2_roi and y1_roi <= cy <= y2_roi:
                    vehiculos_actuales += 1
                    
                    # Agregar a conteo único si es relevante
                    if cls_name in conteo_ids and track_id not in conteo_ids[cls_name]:
                        conteo_ids[cls_name].add(track_id)
                    
                    # Dibujar bounding box con estilo
                    color = (0, 255, 0) if cls_name != 'person' else (255, 100, 0)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f"{cls_name} #{track_id}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Actualizar semáforo
        estado_semaforo = semaforo.actualizar(tiempo_actual, vehiculos_actuales)
        tiempo_restante = semaforo.get_tiempo_restante(tiempo_actual)
        
        # Dibujar ROI
        cv2.rectangle(frame, (x1_roi, y1_roi), (x2_roi, y2_roi), (0, 255, 255), 2)
        cv2.putText(frame, "ZONA DE DETECCION", (x1_roi, y1_roi - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Dibujar elementos UI
        dibujar_semaforo_elegante(frame, estado_semaforo, tiempo_restante)
        dibujar_estadisticas(frame, conteo_ids, semaforo, vehiculos_actuales)
        
        # Título principal
        cv2.putText(frame, "TraficON - Sistema Inteligente de Semaforos", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Indicador de pausa
        if paused:
            overlay = frame.copy()
            cv2.rectangle(overlay, (frame.shape[1]//2 - 100, frame.shape[0]//2 - 30),
                         (frame.shape[1]//2 + 100, frame.shape[0]//2 + 30), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            cv2.putText(frame, "PAUSADO", (frame.shape[1]//2 - 60, frame.shape[0]//2 + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Mostrar frame
        cv2.imshow("TraficON - Presentacion", frame)
        
        # Control de velocidad basado en estado del semáforo
        if estado_semaforo == "AMARILLO":
            delay = 50  # Más lento en amarillo para efecto dramático
        elif estado_semaforo == "ROJO":
            delay = 1000 # Lento en rojo
        else:
            delay = 1   # Normal en verde
        
        # Manejar teclas
        key = cv2.waitKey(delay) if not paused else cv2.waitKey(0)
        
        if key & 0xFF == ord('q'):
            break
        elif key & 0xFF == ord(' '):
            paused = not paused
        elif key & 0xFF == ord('r'):
            # Reiniciar video y estadísticas
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            conteo_ids = {k: set() for k in conteo_ids.keys()}
            semaforo = SemaforoInteligente()
            tiempo_inicio = cv2.getTickCount() / cv2.getTickFrequency()
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    # Exportar resultados finales
    datos_finales = {
        "resumen_trafico": {
            "personas_totales": len(conteo_ids["person"]),
            "vehiculos_totales": len(conteo_ids["car"]) + len(conteo_ids["truck"]) + len(conteo_ids["bus"]),
            "motocicletas_totales": len(conteo_ids["motorcycle"])
        },
        "estadisticas_semaforo": {
            "ciclos_completados": semaforo.cambios_rojo_a_verde,
            "cambios_verde_amarillo": semaforo.cambios_verde_a_amarillo,
            "cambios_amarillo_rojo": semaforo.cambios_amarillo_a_rojo,
            "estado_final": semaforo.estado
        },
        "configuracion": {
            "duracion_verde_base": semaforo.duracion_verde_base,
            "duracion_amarillo": semaforo.duracion_amarillo,
            "duracion_rojo_base": semaforo.duracion_rojo_base
        },
        "timestamp": datetime.now().isoformat()
    }
    
    nombre_archivo = f"traficon_reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        json.dump(datos_finales, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*50}")
    print("RESUMEN FINAL DE LA SIMULACION")
    print(f"{'='*50}")
    print(f"Personas detectadas: {len(conteo_ids['person'])}")
    print(f"Vehículos detectados: {len(conteo_ids['car']) + len(conteo_ids['truck']) + len(conteo_ids['bus'])}")
    print(f"Motocicletas detectadas: {len(conteo_ids['motorcycle'])}")
    print(f"Ciclos de semáforo completados: {semaforo.cambios_rojo_a_verde}")
    print(f"Reporte exportado: {nombre_archivo}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()