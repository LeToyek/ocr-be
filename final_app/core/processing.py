from utils.logger import log
# Import the updated detection function
from core.detection import detect_objects
# Import the OCR pipeline runner
from core.ocr_pipeline import run_ocr_pipeline
import cv2 # Needed for cropping

def process_image(image_path: str):
    """
    Processes the image: detects objects, finds the largest, crops, and runs OCR pipeline.
    """
    if not image_path:
        log.error("No image path provided.")
        return

    # log.info(f"Starting image processing for: {image_path}")

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
                    
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    area = (x2 - x1) * (y2 - y1)
                    name = model.names[int(box.cls)]
                    if area > max_area and name.upper() in valid_categories:
                        max_area = area
                        largest_detection = {
                            'class_name': name,
                            'bbox': (x1, y1, x2, y2),
                            'area': area
                        }
        
            if largest_detection:
                # Use the uppercase version for logging consistency if desired
                # log.info(f"Largest object found: {largest_detection['class_name'].upper()} (Area: {largest_detection['area']})")

                # --- Step 3: Crop the image based on the largest bounding box ---
                x1, y1, x2, y2 = largest_detection['bbox']
                # Add some padding if needed, ensure coordinates are within image bounds
                cropped_image = image[
                    # int(bbox[0][1]) : int(bbox[0][3]), int(bbox[0][0]) : int(bbox[0][2])
                    int(y1) : int(y2), int(x1) : int(x2)
                ]
                
                if cropped_image.size == 0:
                    log.error("Cropped image is empty. Check bounding box coordinates.")
                    # Ensure the default error result is a dictionary for consistency
                    final_ocr_result = {'error': 'Cropped image empty', 'top_text': '', 'bottom_text': ''}
                else:
                    # --- Step 4: Run the category-specific OCR pipeline ---
                    # Use the uppercase category name when calling the pipeline runner
                    category = largest_detection['class_name'].upper()
                    # Save cropped image for debugging (optional)
                    # cv2.imwrite(f"debug_cropped_{category}.png", cropped_image)

                    final_ocr_result = run_ocr_pipeline(cropped_image, category)
                    # Log using the uppercase category name
                    log.info(f"Final OCR Result for {category}: Top='{final_ocr_result.get('top_text', '')}', Bottom='{final_ocr_result.get('bottom_text', '')}'")


            else:
                log.warning(f"No objects of categories {valid_categories} found in the detections.")
                # Ensure the default error result is a dictionary for consistency
                final_ocr_result = {'error': 'No target objects detected', 'top_text': '', 'bottom_text': ''}


        # Log the final dictionary result
        log.info(f"Processing finished for {image_path}. Final Result: {final_ocr_result}")


    except Exception as e:
        log.error(f"An error occurred during the main processing workflow: {e}", exc_info=True) # Add traceback
        # Ensure the default error result is a dictionary for consistency
        final_ocr_result = {'error': 'Processing Error', 'top_text': '', 'bottom_text': ''}

    # Return the final result dictionary
    return final_ocr_result