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
CAP_OCR_MODEL_PATH = r"d:\SKRIPSI\CODE\ocr-lotno-model\final_app\assets\models\cap_character_model.pt" # <<< IMPORTANT: Replace with your CAP character model path
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
        # It expects HWC format
        results = reader.readtext(image)
        # Format results slightly for consistency: [[x1,y1,x2,y2], text, conf]
        formatted_results = []
        for (bbox, text, prob) in results:
            # bbox is [[tl_x, tl_y], [tr_x, tr_y], [br_x, br_y], [bl_x, bl_y]]
            # Convert to simple [x_min, y_min, x_max, y_max]
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            box = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]

            # # --- Text Cleaning Start ---
            # # 1. Filter out non-alphanumeric characters
            # cleaned_text = re.sub(r'[^a-zA-Z0-9]', '', text)

            # # 2. Convert to uppercase for consistent substitution
            # cleaned_text_upper = cleaned_text.upper()

            # # 3. Perform substitutions: O -> 0, I -> 1
            # cleaned_text_final = cleaned_text_upper.replace('O', '0').replace('I', '1')
            cleaned_text_final = text
            # # --- Text Cleaning End ---

            # Only add if the cleaned text is not empty
            if cleaned_text_final:
                formatted_results.append({'box': box, 'text': cleaned_text_final, 'confidence': prob})
                log.debug(f"EasyOCR detected: '{text}' -> Cleaned: '{cleaned_text_final}' (Conf: {prob:.2f}) at {box}")
            else:
                log.debug(f"EasyOCR detected: '{text}' -> Discarded after cleaning (Conf: {prob:.2f}) at {box}")


        log.info(f"EasyOCR finished. Found {len(formatted_results)} valid text blocks after cleaning.")
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

        # Process YOLO results (assuming results is a list or similar iterable)
        if results:
             # Assuming the first element contains the detections for the single image
            yolo_result_obj = results[0]
            boxes = yolo_result_obj.boxes
            if boxes: # Check if any boxes were detected
                for box in boxes:
                    # Get bounding box coordinates [x1, y1, x2, y2]
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                    # Get confidence
                    confidence = float(box.conf[0].item())

                    # Get class name (character)
                    class_id = int(box.cls[0].item())
                    # Ensure class_id is valid for the model's names list
                    if class_id < len(yolo_result_obj.names):
                         char = yolo_result_obj.names[class_id]
                    else:
                         log.warning(f"Detected class_id {class_id} is out of bounds for model names.")
                         char = "?" # Assign a placeholder if class_id is invalid

                    formatted_results.append({'box': [x1, y1, x2, y2], 'text': char, 'confidence': confidence})
                    log.debug(f"CAP YOLO OCR detected: '{char}' (Conf: {confidence:.2f}) at {[x1, y1, x2, y2]}")
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
    return final_result


def draw_ocr_results(image: np.ndarray, results: list) -> np.ndarray:
    """
    Draws bounding boxes and text from OCR results onto an image.

    Args:
        image (np.ndarray): The input image (BGR format).
        results (list): A list of dictionaries, where each dictionary contains
                        at least 'box' (list of 4 points [tl, tr, br, bl])
                        and 'text' (string).

    Returns:
        np.ndarray: A copy of the image with OCR results drawn on it.
    """
    output_image = image.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    text_color = (0, 255, 0) # Green
    box_color = (0, 0, 255) # Red
    thickness = 1

    if not results:
        log.warning("No OCR results provided to draw.")
        return output_image

    for item in results:
        try:
            # Extract box and text
            box = item.get('box')
            text = item.get('text', '')

            if box is None:
                log.warning(f"Skipping item due to missing 'box': {item}")
                continue

            # Ensure box is in the expected format (list of 4 points)
            if not isinstance(box, list) or len(box) != 4:
                 # Handle potential EasyOCR format (list of lists) or other formats
                 if isinstance(box, list) and len(box) > 0 and isinstance(box[0], list) and len(box[0]) == 2:
                     # Assuming [[x1,y1],[x2,y1],[x2,y2],[x1,y2]] format from EasyOCR
                     pts = np.array(box, dtype=np.int32)
                 elif isinstance(box, list) and len(box) == 4 and all(isinstance(p, (int, float)) for p in box):
                     # Assuming [x_min, y_min, x_max, y_max] format from YOLO? Adjust if needed.
                     x_min, y_min, x_max, y_max = map(int, box)
                     pts = np.array([[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]], dtype=np.int32)
                 else:
                     log.warning(f"Skipping item due to unexpected 'box' format: {box}")
                     continue
            else:
                 # Assuming the format is already list of 4 points [[x,y], [x,y], [x,y], [x,y]]
                 pts = np.array(box, dtype=np.int32)


            # Draw the bounding box polygon
            cv2.polylines(output_image, [pts], isClosed=True, color=box_color, thickness=thickness)

            # Put the recognized text near the top-left corner of the box
            text_position = (pts[0][0], pts[0][1] - 5) # Position text slightly above the top-left corner
            cv2.putText(output_image, text, text_position, font, font_scale, text_color, thickness, cv2.LINE_AA)

        except Exception as e:
            log.error(f"Error drawing result item {item}: {e}", exc_info=True)

    return output_image