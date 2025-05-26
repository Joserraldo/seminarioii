import cv2
from ultralytics import YOLO
import json 
from datetime import datetime 
import os 

print("Cargando modelo YOLOv8n...")
model = YOLO("yolov8n.pt")

video_path = "test2.mp4"
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"Error: No se pudo abrir el video '{video_path}'. Asegúrate de que existe y la ruta es correcta.")
    exit() 

conteo_ids = {
    'person': set(),
    'car': set(),
    'motorcycle': set(),
    'truck': set(), 
    'bus': set()
}

x1_roi, y1_roi = 80, 100
x2_roi, y2_roi = 700, 480

print("Iniciando procesamiento de video. Presiona 'q' para salir.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Fin del video o error al leer frame.")
        break
    results = model.track(frame, persist=True, tracker="bytetrack.yaml")[0]

    boxes = results.boxes
    if boxes is not None and boxes.id is not None:
        ids = boxes.id.cpu().numpy().astype(int)
        cls = boxes.cls.cpu().numpy().astype(int)
        coords = boxes.xyxy.cpu().numpy().astype(int)

        for track_id, class_id, (x1, y1, x2, y2) in zip(ids, cls, coords):
            cls_name = model.names[class_id]

            
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            
            if x1_roi <= cx <= x2_roi and y1_roi <= cy <= y2_roi:
                
                if cls_name in conteo_ids:
                    if track_id not in conteo_ids[cls_name]:
                        conteo_ids[cls_name].add(track_id)
                
                color = (0, 255, 0) 
                if cls_name == 'person':
                    color = (255, 100, 0) 
                elif cls_name in ['car', 'truck', 'bus']:
                    color = (0, 0, 255) 
                elif cls_name == 'motorcycle':
                    color = (0, 255, 255) 

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{cls_name} ID:{track_id}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.rectangle(frame, (x1_roi, y1_roi), (x2_roi, y2_roi), (0, 255, 255), 2)
    cv2.putText(frame, "Zona de conteo", (x1_roi, y1_roi - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    texto_conteo = f"Personas: {len(conteo_ids['person'])} | Autos: {len(conteo_ids['car'])}" \
                   f" | Motos: {len(conteo_ids['motorcycle'])}" \
                   f" | Camiones: {len(conteo_ids['truck'])}" \
                   f" | Buses: {len(conteo_ids['bus'])}"

    cv2.putText(frame, texto_conteo, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA) 

    cv2.imshow("Detección de Tráfico", frame)
    
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

datos_finales_json = {
    "fecha_generacion": datetime.now().isoformat(),
    "resumen_conteo_total": {
        "personas_detectadas": len(conteo_ids['person']),
        "autos_detectados": len(conteo_ids['car']),
        "motocicletas_detectadas": len(conteo_ids['motorcycle']),
        "camiones_detectados": len(conteo_ids['truck']),
        "buses_detectados": len(conteo_ids['bus']),
        "vehiculos_totales": len(conteo_ids['car']) + len(conteo_ids['motorcycle']) +
                             len(conteo_ids['truck']) + len(conteo_ids['bus'])
    },
    "ids_unicos_detectados": {
        "person_ids": list(conteo_ids['person']),
        "car_ids": list(conteo_ids['car']),
        "motorcycle_ids": list(conteo_ids['motorcycle']),
        "truck_ids": list(conteo_ids['truck']),
        "bus_ids": list(conteo_ids['bus'])
    },
    "zona_de_interes_ROI": {
        "x1": x1_roi, "y1": y1_roi,
        "x2": x2_roi, "y2": y2_roi
    },
    "video_procesado": video_path
}

output_dir = "reports"
os.makedirs(output_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
json_filename = os.path.join(output_dir, f"reporte_conteo_trafico_{timestamp}.json")

try:
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(datos_finales_json, f, indent=4, ensure_ascii=False)
    print(f"\nReporte JSON guardado exitosamente en: {json_filename}")
except Exception as e:
    print(f"\nError al guardar el reporte JSON: {e}")

print("\n--- RESUMEN FINAL DEL CONTEO ---")
print(f"Personas detectadas (únicas): {len(conteo_ids['person'])}")
print(f"Autos detectados (únicas): {len(conteo_ids['car'])}")
print(f"Motos detectadas (únicas): {len(conteo_ids['motorcycle'])}")
print(f"Camiones detectados (únicas): {len(conteo_ids['truck'])}")
print(f"Buses detectados (únicas): {len(conteo_ids['bus'])}")
print(f"Total vehículos (autos, motos, camiones, buses): {datos_finales_json['resumen_conteo_total']['vehiculos_totales']}")
print("---------------------------------")
