# core/preprocessing.py
import cv2
import numpy as np
import json
import os
from utils.logger import log

# --- Configuration for Preset Paths ---
PRESET_BASE_PATH = r"d:\SKRIPSI\CODE\ocr-lotno-model\final_app\assets\pipeline_presets"
PRESET_FILES = {
    "CAP": os.path.join(PRESET_BASE_PATH, "morphed pipeline.json"),
    "BOX": os.path.join(PRESET_BASE_PATH, "final_lotno_box_preproc (used).json"),
    "SOYJOY": os.path.join(PRESET_BASE_PATH, "final_lotno_soyjoy_preproc (used).json"),
}

# --- Mapping from JSON function names to OpenCV functions ---
# Each function here should accept the image and a dictionary of parameters
def apply_grayscale(image, params):
    log.debug("Applying Grayscale")
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def apply_bilateral_filter(image, params):
    d = params.get("d", 9)
    sigmaColor = params.get("sigmaColor", 75)
    sigmaSpace = params.get("sigmaSpace", 75)
    log.debug(f"Applying Bilateral Filter: d={d}, sigmaColor={sigmaColor}, sigmaSpace={sigmaSpace}")
    return cv2.bilateralFilter(image, d, sigmaColor, sigmaSpace)

def apply_fast_nl_means_denoising(image, params):
    h = params.get("h", 10)
    templateWindowSize = params.get("templateWindowSize", 7)
    searchWindowSize = params.get("searchWindowSize", 21)
    log.debug(f"Applying Fast NL Means Denoising: h={h}, templateWindowSize={templateWindowSize}, searchWindowSize={searchWindowSize}")
    # Check if image is grayscale, as denoising function signature differs
    if len(image.shape) == 2: # Grayscale
        return cv2.fastNlMeansDenoising(image, None, h, templateWindowSize, searchWindowSize)
    else: # Color - needs hColor parameter, using h for it as common practice
        return cv2.fastNlMeansDenoisingColored(image, None, h, h, templateWindowSize, searchWindowSize)

def apply_convert_scale_abs(image, params):
    alpha = params.get("alpha", 1.0)
    beta = params.get("beta", 0)
    log.debug(f"Applying Convert Scale Abs: alpha={alpha}, beta={beta}")
    return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

def apply_adaptive_threshold(image, params):
    block_size = params.get("block_size", 11)
    C = params.get("C", 2)
    # Ensure block_size is odd and > 1
    if block_size <= 1: block_size = 3
    if block_size % 2 == 0: block_size += 1
    log.debug(f"Applying Adaptive Threshold: block_size={block_size}, C={C}")
    # Adaptive threshold requires grayscale image
    if len(image.shape) > 2:
        log.warning("Adaptive Threshold requires grayscale image, converting...")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY_INV, block_size, C) # Using INV often good for OCR

def apply_morph_opening(image, params):
    kernel_size = params.get("kernel_size", 3)
    log.debug(f"Applying Morphological Opening: kernel_size={kernel_size}")
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

def apply_morph_closing(image, params):
    kernel_size = params.get("kernel_size", 3)
    log.debug(f"Applying Morphological Closing: kernel_size={kernel_size}")
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)

def apply_dilate(image, params):
    kernel_size = params.get("kernel_size", 3)
    iterations = params.get("iterations", 1)
    log.debug(f"Applying Dilate: kernel_size={kernel_size}, iterations={iterations}")
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    return cv2.dilate(image, kernel, iterations=iterations)

# Add other functions as needed...

PROCESSING_FUNCTIONS = {
    "Grayscale": apply_grayscale,
    "Bilateral Filtered Image": apply_bilateral_filter,
    "Fast Non-Local Means Denoising": apply_fast_nl_means_denoising,
    "Convert Scale Abs": apply_convert_scale_abs,
    "Adaptive Threshold": apply_adaptive_threshold,
    "Morphological Opening": apply_morph_opening,
    "Morphological Closing": apply_morph_closing,
    "Dilate": apply_dilate,
    # Add mappings for any other functions defined in your JSON files
}

# --- Main Pipeline Function ---
def apply_preprocessing_pipeline(image: np.ndarray, category: str) -> np.ndarray:
    """
    Loads the preprocessing pipeline JSON for the category and applies the steps.
    """
    log.info(f"Starting preprocessing pipeline for category: {category}")
    preset_path = PRESET_FILES.get(category)

    if not preset_path:
        log.error(f"No preset file defined for category: {category}")
        return image # Return original image if no preset found

    if not os.path.exists(preset_path):
        log.error(f"Preset file not found: {preset_path}")
        return image # Return original image if file is missing

    try:
        with open(preset_path, 'r') as f:
            pipeline_steps = json.load(f)
    except Exception as e:
        log.error(f"Failed to load or parse JSON preset file {preset_path}: {e}")
        return image

    processed_image = image.copy() # Work on a copy

    for step in pipeline_steps:
        func_name = step.get("function")
        params = step.get("params", {})

        if func_name in PROCESSING_FUNCTIONS:
            try:
                log.debug(f"Applying step: {func_name} with params: {params}")
                processing_func = PROCESSING_FUNCTIONS[func_name]
                processed_image = processing_func(processed_image, params)
            except Exception as e:
                log.error(f"Error applying step '{func_name}' for category '{category}': {e}", exc_info=True)
                # Decide if you want to stop or continue on error
                # return image # Option: return original image on error
                continue # Option: skip failed step and continue
        else:
            log.warning(f"Preprocessing function '{func_name}' not implemented or mapped.")

    log.info(f"Preprocessing pipeline for category {category} completed.")
    return processed_image