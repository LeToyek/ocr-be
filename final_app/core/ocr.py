# core/ocr.py
import easyocr
import numpy as np
from utils.logger import log
import os
import cv2
import re # Import the regular expression module

# --- EasyOCR Initialization ---
# Initialize EasyOCR reader only once. Specify languages needed.
# Use GPU if available (cuda=True), otherwise CPU (cuda=False)
try:
    log.info("Initializing EasyOCR Reader...")
    # Add languages needed, e.g., ['en'] for English
    reader = easyocr.Reader(['en'], gpu=False) # Or gpu=False if no CUDA/GPU
    log.info("EasyOCR Reader initialized successfully.")
    EASYOCR_AVAILABLE = True
except Exception as e:
    log.error(f"Failed to initialize EasyOCR: {e}. EasyOCR will not be available.")
    log.warning("Ensure PyTorch and CUDA (if using GPU) are correctly installed.")
    reader = None
    EASYOCR_AVAILABLE = False

# --- YOLO OCR Model Initialization (Placeholder) ---
# TODO: Implement loading and inference for your CAP YOLO character model
# This will be similar to core/detection.py but for a different model
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
YOLO_MODEL_FOLDER = os.path.join(PROJECT_ROOT, 'assets','models')
# CAP_OCR_MODEL_PATH = r".\assets\models\cap_character_model.pt" # <<< IMPORTANT: Replace with your CAP character model path
CAP_OCR_MODEL_PATH = os.path.join(YOLO_MODEL_FOLDER, 'cap_character_model.pt') # <<< IMPORTANT: Replace with your CAP character model path
CAP_OCR_MODEL = None
CAP_OCR_AVAILABLE = False
try:
    if os.path.exists(CAP_OCR_MODEL_PATH):
        from ultralytics import YOLO # Assuming same library
        CAP_OCR_MODEL = YOLO(CAP_OCR_MODEL_PATH)
        log.info(f"Successfully loaded CAP OCR YOLO model from: {CAP_OCR_MODEL_PATH}")
        CAP_OCR_AVAILABLE = True
    else:
        log.warning(f"CAP OCR YOLO model not found at: {CAP_OCR_MODEL_PATH}")
except Exception as e:
    log.error(f"Failed to load CAP OCR YOLO model: {e}")

# log.warning("CAP OCR YOLO model loading is currently commented out/placeholder.") # Placeholder warning # Removed this line

# --- OCR Functions ---

def perform_easyocr(image: np.ndarray) -> list:
    """
    Performs OCR using EasyOCR.

    Args:
        image (np.ndarray): The image array (output from preprocessing/extraction).

    Returns:
        list: A list of tuples, where each tuple contains (bounding_box, text, confidence).
              Returns empty list if EasyOCR is unavailable or fails.
              Text is cleaned to contain only alphanumeric characters with O->0 and I->1 substitutions.
    """
    if not EASYOCR_AVAILABLE or reader is None:
        log.error("EasyOCR is not available.")
        return []

    log.info("Performing OCR using EasyOCR...")
    try:
        # EasyOCR works best with BGR images, ensure input format if needed
        results = reader.readtext(image)
        # Format results slightly for consistency
        formatted_results = []
        
        # Debug the raw results
        log.debug(f"Raw EasyOCR results: {results}")
        
        for (bbox, text, prob) in results:
            # bbox is [[tl_x, tl_y], [tr_x, tr_y], [br_x, br_y], [bl_x, bl_y]]
            # Keep the original polygon format for drawing
            # Also add a simplified box format for text splitting
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            simple_box = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
            
            cleaned_text_final = text
            
            # Only add if the cleaned text is not empty
            if cleaned_text_final:
                formatted_results.append({
                    'box': simple_box,  # For text splitting
                    'bbox': bbox,       # Original polygon for drawing
                    'text': cleaned_text_final, 
                    'confidence': prob
                })
                log.debug(f"EasyOCR detected: '{text}' at box={simple_box}, bbox={bbox}")
            else:
                log.debug(f"EasyOCR detected: '{text}' -> Discarded after cleaning")

        log.info(f"EasyOCR finished. Found {len(formatted_results)} valid text blocks.")
        return formatted_results
    except Exception as e:
        log.error(f"Error during EasyOCR execution: {e}", exc_info=True)
        return []

def perform_cap_ocr_yolo(image: np.ndarray) -> list:
    """
    Performs OCR using a custom YOLO character model for CAP.

    Args:
        image (np.ndarray): The image array.

    Returns:
        list: A list of dictionaries [{'box': [x1,y1,x2,y2], 'text': char, 'confidence': conf}].
              Returns empty list if model unavailable or fails.
    """
    if not CAP_OCR_AVAILABLE or CAP_OCR_MODEL is None:
        log.error("CAP OCR YOLO model is not available.")
        return []

    log.info("Performing OCR using CAP YOLO model...")
    try:
        # --- Implement YOLO inference for characters ---
        # Ensure image is in the right format for YOLO (usually BGR for OpenCV-based models)
        if len(image.shape) == 2:
            # Convert grayscale to BGR if needed by the model
            ocr_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            log.debug("Converted grayscale image to BGR for CAP YOLO OCR.")
        else:
            ocr_image = image # Assume it's already BGR

        # Perform detection
        log.debug("Running inference with CAP YOLO model...")
        results = CAP_OCR_MODEL(ocr_image)
        log.debug("Inference complete.")

        formatted_results = []

        # Process YOLO results
        if results:
            yolo_result_obj = results[0]
            boxes = yolo_result_obj.boxes
            if boxes:
                for box in boxes:
                    # Get bounding box coordinates [x1, y1, x2, y2]
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                    # Get confidence
                    confidence = float(box.conf[0].item())

                    # Get class name (character)
                    class_id = int(box.cls[0].item())
                    if class_id < len(yolo_result_obj.names):
                        char = yolo_result_obj.names[class_id]
                    else:
                        log.warning(f"Detected class_id {class_id} is out of bounds for model names.")
                        char = "?"

                    # Create both box and bbox formats for consistency
                    simple_box = [x1, y1, x2, y2]
                    polygon_bbox = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]  # Convert to polygon format
                    
                    formatted_results.append({
                        'box': simple_box,
                        'bbox': polygon_bbox,  # Add polygon format for drawing
                        'text': char, 
                        'confidence': confidence
                    })
                    log.debug(f"CAP YOLO OCR detected: '{char}' at box={simple_box}, bbox={polygon_bbox}")
            else:
                log.info("No character boxes detected by CAP YOLO model in this image.")
        else:
            log.info("CAP YOLO model returned no results for this image.")
        # --- End of YOLO Implementation ---

        # Note: Sorting is handled later in split_text_top_bottom by y then x coordinate
        # If specific left-to-right sorting is needed *before* splitting, it could be done here:
        # print("Formatted results before sorting: ", formatted_results)
        formatted_results.sort(key=lambda det: det['box'][0])
        # print("Formatted results after sorting: ", formatted_results)

        log.info(f"CAP YOLO OCR finished. Found {len(formatted_results)} characters.")
        return formatted_results
    except Exception as e:
        log.error(f"Error during CAP YOLO OCR execution: {e}", exc_info=True)
        return []


# --- Text Splitting Logic ---
def split_text_top_bottom(ocr_results: list, image_height: int) -> dict:
    """
    Splits OCR text results into top and bottom sections based on bounding box position.

    Args:
        ocr_results (list): List of OCR detection dictionaries, each with 'box' and 'text'.
                            Box format: [x_min, y_min, x_max, y_max]
        image_height (int): The height of the image the OCR was performed on.

    Returns:
        dict: A dictionary {'top_text': str, 'bottom_text': str}.
              Text within each section is joined by spaces.
    """
    if not ocr_results:
        return {'top_text': '', 'bottom_text': ''}

    threshold_y = image_height / 3.0

    top_texts = []
    bottom_texts = []

    # Sort results by y then x coordinate for potentially better reading order
    # ocr_results.sort(key=lambda r: (r['box'][1], r['box'][0]))

    for result in ocr_results:
        y_min = result['box'][1]
        text = result['text']

        if y_min < threshold_y:
            top_texts.append(text)
        else:
            bottom_texts.append(text)

    # Join the texts with spaces
    final_result = {
        'top_text': " ".join(top_texts),
        'bottom_text': " ".join(bottom_texts)
    }
    log.info(f"Split text results: Top='{final_result['top_text']}', Bottom='{final_result['bottom_text']}'")
    log.info(f"Split text resultsssssssssssssss: Top='{final_result['top_text']}'")
    return final_result


def draw_ocr_results(image: np.ndarray, results: list) -> np.ndarray:
    """
    Draws bounding boxes and text from OCR results onto an image.
    """
    # Make a copy and ensure it's in color format (BGR)
    if image is None:
        log.error("Input image is None")
        return np.zeros((300, 300, 3), dtype=np.uint8)
        
    output_image = image.copy()
    
    # Ensure image is in color format for visible boxes
    if len(output_image.shape) == 2:  # If grayscale
        output_image = cv2.cvtColor(output_image, cv2.COLOR_GRAY2BGR)
    
    h, w = output_image.shape[:2]
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    text_color = (0, 255, 0)  # Green
    box_color = (0, 0, 255)   # Red - more visible
    thickness = 2
    
    log.debug(f"Drawing boxes for {len(results)} OCR results")
    
    for i, item in enumerate(results):
        try:
            text = item.get('text', '')
            
            # First try to use bbox (polygon format) if available
            if 'bbox' in item and item['bbox'] is not None:
                bbox = item['bbox']
                log.debug(f"Drawing polygon bbox for item {i}: {bbox}")
                
                # Convert to numpy array for drawing
                pts = np.array(bbox, dtype=np.int32)
                
                # Draw the polygon
                cv2.polylines(output_image, [pts], isClosed=True, color=box_color, thickness=thickness)
                
                # Add text near the top-left corner
                text_x, text_y = bbox[0]
                text_y = max(text_y - 10, 10)  # Position text above the box
                cv2.putText(output_image, text, (int(text_x), int(text_y)), 
                            font, font_scale, text_color, thickness)
            
            # Fall back to box format if bbox not available
            elif 'box' in item and item['box'] is not None:
                box = item['box']
                log.debug(f"Drawing rectangle box for item {i}: {box}")
                
                # Ensure we have 4 coordinates
                if len(box) == 4:
                    x_min, y_min, x_max, y_max = map(int, box)
                    
                    # Ensure coordinates are within image boundaries
                    x_min = max(0, min(x_min, w-1))
                    y_min = max(0, min(y_min, h-1))
                    x_max = max(0, min(x_max, w-1))
                    y_max = max(0, min(y_max, h-1))
                    
                    # Draw the rectangle
                    cv2.rectangle(output_image, (x_min, y_min), (x_max, y_max), 
                                 box_color, thickness)
                    
                    # Add text above the box
                    text_y = max(y_min - 10, 10)  # Position text above the box
                    cv2.putText(output_image, text, (x_min, text_y), 
                                font, font_scale, text_color, thickness)
            else:
                log.warning(f"No valid box format found for item {i}")
        
        except Exception as e:
            log.error(f"Error drawing item {i}: {e}", exc_info=True)
    
    # Add a count of boxes drawn
    cv2.putText(output_image, f"Processed: {len(results)} boxes", 
                (10, h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return output_image