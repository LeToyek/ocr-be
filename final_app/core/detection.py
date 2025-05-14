# core/detection.py
from ultralytics import YOLO
from utils.logger import log
import numpy as np
import cv2
import os # Import os to construct the path relative to this file if needed, or use absolute path

# --- Configuration ---
# Path to the folder containing YOLO models
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
YOLO_MODEL_FOLDER = os.path.join(PROJECT_ROOT, 'assets','models')
# Name of your specific model file within that folder
YOLO_MODEL_NAME = "localization_model.pt" # <<< IMPORTANT: Replace this with your actual model file name
YOLO_MODEL_PATH = os.path.join(YOLO_MODEL_FOLDER, YOLO_MODEL_NAME)


# --- Model Loading ---
model = None # Initialize model as None
if not os.path.exists(YOLO_MODEL_PATH):
    log.error(f"YOLO model file not found at: {YOLO_MODEL_PATH}")
    log.error("Please ensure the model file exists in the 'yolo' folder and the name is correct in 'core/detection.py'.")
else:
    try:
        # Load the YOLO model from the specified path
        model = YOLO(YOLO_MODEL_PATH)
        log.info(f"Successfully loaded YOLO model from: {YOLO_MODEL_PATH}")
    except Exception as e:
        log.error(f"Failed to load YOLO model from {YOLO_MODEL_PATH}: {e}")
        model = None # Ensure model is None if loading fails

# --- Detection Function ---
def detect_objects(image_path: str):
    """
    Performs object detection on the given image using the loaded YOLO model.

    Args:
        image_path (str): The path to the image file.

    Returns:
        tuple: A tuple containing:
            - results: The detection results from the YOLO model.
            - image: The loaded image (NumPy array).
        Returns (None, None) if the model isn't loaded or the image can't be read.
    """
    if model is None:
        log.error("YOLO model is not loaded or failed to load. Cannot perform detection.")
        return None, None

    try:
        # Read the image using OpenCV
        img = cv2.imread(image_path)
        if img is None:
            log.error(f"Could not read image file for detection: {image_path}")
            return None, None

        log.info(f"Performing YOLO detection on: {image_path}")
        # Perform detection
        results = model(img) # Pass the loaded image (NumPy array) to the model
        log.info(f"Detection complete. Found {len(results[0].boxes)} potential objects.") # Example for ultralytics results

        return results, img,model

    except Exception as e:
        log.error(f"An error occurred during YOLO detection: {e}")
        return None, None

def detect_objects_by_image(image):
    """
    Performs object detection on the given image using the loaded YOLO model.

    Args:
        image_path (str): The path to the image file.

    Returns:
        tuple: A tuple containing:
            - results: The detection results from the YOLO model.
            - image: The loaded image (NumPy array).
        Returns (None, None) if the model isn't loaded or the image can't be read.
    """
    if model is None:
        log.error("YOLO model is not loaded or failed to load. Cannot perform detection.")
        return None, None

    try:
        # Read the image using OpenCV
        img = image
        if img is None:
            return None, None

        # Perform detection
        results = model(img) # Pass the loaded image (NumPy array) to the model
        log.info(f"Detection complete. Found {len(results[0].boxes)} potential objects.") # Example for ultralytics results

        return results, img,model

    except Exception as e:
        log.error(f"An error occurred during YOLO detection: {e}")
        return None, None


