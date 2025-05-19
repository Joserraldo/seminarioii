import cv2
from ultralytics import YOLO

# Cargar modelo YOLOv8 nano
model = YOLO("yolov8n.pt")

# Cargar video
cap = cv2.VideoCapture("test.mp4")

# Diccionario para almacenar IDs únicos
conteo_ids = {
    'person': set(),
    'car': set(),
    'motorcycle': set()
}

# Coordenadas de la zona de interés (ROI) [y1:y2, x1:x2]
x1_roi, y1_roi = 80, 100
x2_roi, y2_roi = 700, 480

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Hacer tracking
    results = model.track(frame, persist=True, tracker="bytetrack.yaml")[0]

    boxes = results.boxes
    if boxes is not None and boxes.id is not None:
        ids = boxes.id.cpu().numpy().astype(int)
        cls = boxes.cls.cpu().numpy().astype(int)
        coords = boxes.xyxy.cpu().numpy().astype(int)

        for track_id, class_id, (x1, y1, x2, y2) in zip(ids, cls, coords):
            cls_name = model.names[class_id]

            # Verificar si el centro del objeto está dentro del ROI
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            if x1_roi <= cx <= x2_roi and y1_roi <= cy <= y2_roi:
                if cls_name in conteo_ids and track_id not in conteo_ids[cls_name]:
                    conteo_ids[cls_name].add(track_id)

                # Dibujar cuadro y etiqueta solo si está dentro del ROI
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{cls_name} ID:{track_id}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Dibujar zona de interés (ROI)
    cv2.rectangle(frame, (x1_roi, y1_roi), (x2_roi, y2_roi), (0, 255, 255), 2)
    cv2.putText(frame, "Zona de conteo", (x1_roi, y1_roi - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    # Mostrar conteo
    texto = f"Personas: {len(conteo_ids['person'])}  Autos: {len(conteo_ids['car'])}  Motos: {len(conteo_ids['motorcycle'])}"
    cv2.putText(frame, texto, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    cv2.imshow("Detección TraficON", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

# Mostrar resultado final
print("Conteo único final:")
for k, v in conteo_ids.items():
    print(f"{k}: {len(v)}")
