# core/processing.py
import os
import cv2
from core.detection import detect_objects
from core.ocr_pipeline import run_ocr_pipeline
from utils.logger import log

def process_image(image_path: str):
    """
    Processes the image: detects objects, finds the largest, crops, and runs OCR pipeline.
    """
    if not image_path:
        log.error("No image path provided.")
        return

    final_ocr_result = "N/A" # Default result if processing fails

    try:
        # --- Step 1: Perform YOLO detection ---
        detections, image, model = detect_objects(image_path)

        if image is None:
            log.error("Failed to load image. Aborting processing.")
            return # Exit if image loading failed in detect_objects

        if detections is None:
            log.error("Detection failed. Aborting processing.")
            return # Exit if detection itself failed critically

        if not detections:
            log.warning(f"No objects ('CAP', 'BOX', 'SOYJOY') detected in image: {image_path}")
            # Decide how to handle no detections: return, log, etc.
            final_ocr_result = "No objects detected"

        else:
            # --- Step 2: Find the detection with the largest area ---
            largest_detection = None
            max_area = -1

            # Ensure valid categories are uppercase
            valid_categories = {"CAP", "BOX", "SOYJOY"}
            for det in detections:
                boxes = det.boxes   
                for box in boxes:
                    
                    # Get the class name and convert to uppercase
                    class_id = int(box.cls[0].item())
                    class_name = model.names[class_id].upper()
                    
                    # Skip if not a valid category
                    if class_name not in valid_categories:
                        continue
                    
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    
                    # Calculate area
                    area = (x2 - x1) * (y2 - y1)
                    
                    # Update if this is the largest area so far
                    if area > max_area:
                        max_area = area
                        largest_detection = {
                            'category': class_name,
                            'box': [x1, y1, x2, y2],
                            'confidence': float(box.conf[0].item())
                        }
            
            # --- Step 3: Crop the image to the largest detection ---
            if largest_detection:
                x1, y1, x2, y2 = largest_detection['box']
                # Add a small margin (e.g., 5 pixels) around the detection
                margin = 5
                x1 = max(0, x1 - margin)
                y1 = max(0, y1 - margin)
                x2 = min(image.shape[1], x2 + margin)
                y2 = min(image.shape[0], y2 + margin)
                
                cropped_image = image[y1:y2, x1:x2]
                
                # Create a folder for the image results
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                output_dir = os.path.join(os.path.dirname(image_path), base_name)
                os.makedirs(output_dir, exist_ok=True)
                
                # Save the original image with detection box
                image_with_box = image.copy()
                cv2.rectangle(image_with_box, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(image_with_box, largest_detection['category'], 
                           (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                cv2.imwrite(os.path.join(output_dir, "00_detection.jpg"), image_with_box)
                
                # --- Step 4: Run the OCR pipeline on the cropped image ---
                category = largest_detection['category']
                final_ocr_result = run_ocr_pipeline(cropped_image, category, image_path)
                
                # Add detection info to the result
                final_ocr_result['detection'] = {
                    'box': largest_detection['box'],
                    'confidence': largest_detection['confidence']
                }
            else:
                log.warning("No valid detections found.")
                final_ocr_result = "No valid detections"

        return final_ocr_result
        
    except Exception as e:
        log.error(f"Error processing image {image_path}: {e}", exc_info=True)
        return {"error": str(e)}