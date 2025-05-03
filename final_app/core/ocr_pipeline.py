# core/ocr_pipeline.py
from utils.logger import log
import numpy as np
from core.preprocessing import apply_preprocessing_pipeline
from core.ocr import perform_easyocr, perform_cap_ocr_yolo, split_text_top_bottom
# Import the new post-processing function
from core.postprocessing import apply_post_processing

# --- Placeholder Functions ---
# Keep extract_characters for now, unless OCR handles it directly
def extract_characters(image: np.ndarray, category: str) -> np.ndarray:
    """
    Placeholder/Pass-through for character extraction.
    For EasyOCR, this might just return the preprocessed image.
    For CAP YOLO OCR, this might also just return the preprocessed image,
    as the YOLO model handles character localization.
    """
    log.info(f"Character extraction step for category: {category} (currently pass-through)")
    # If you have specific segmentation logic before OCR, implement it here.
    # Otherwise, just return the image for the OCR step.
    return image # Return the preprocessed image directly to OCR

# Remove the old perform_ocr placeholder
# def perform_ocr(character_data: list, category: str) -> str:
#    ... (removed) ...


# --- Pipeline Mapping ---
# Map categories to their specific OCR functions
# The 'character_data' from extract_characters is now just the image for OCR
OCR_FUNCTIONS = {
    "CAP": perform_cap_ocr_yolo,
    "BOX": perform_easyocr,
    "SOYJOY": perform_easyocr,
}

# Define the processing steps for each category
# Note: Post-processing is handled *after* the main pipeline steps
PIPELINE_STEPS = {
    "CAP": [apply_preprocessing_pipeline, extract_characters, OCR_FUNCTIONS["CAP"]],
    "BOX": [apply_preprocessing_pipeline, extract_characters, OCR_FUNCTIONS["BOX"]],
    "SOYJOY": [apply_preprocessing_pipeline, extract_characters, OCR_FUNCTIONS["SOYJOY"]],
}

# Change the return type hint to dict
def run_ocr_pipeline(image: np.ndarray, category: str) -> dict:
    """
    Runs the appropriate OCR pipeline based on the category, splits text,
    and applies post-processing.

    Returns:
        dict: A dictionary containing the category, post-processing status, and formatted text,
              e.g., {'category': 'BOX', 'status': 'Valid Lokal', 'formatted_top': '...', 'formatted_bottom': '...'}.
              Returns error info in the dictionary on failure.
    """
    if category not in PIPELINE_STEPS:
        log.error(f"No defined OCR pipeline for category: {category}")
        # Return consistent error format, including category
        return {'category': category, 'status': 'Error: Unknown category', 'formatted_top': '', 'formatted_bottom': ''}

    log.info(f"Starting OCR pipeline for category: {category}")
    pipeline = PIPELINE_STEPS[category]
    current_data = image # Start with the cropped image

    try:
        # Step 1: Preprocessing
        preprocessed_image = pipeline[0](current_data, category)

        # Step 2: Character Extraction (currently pass-through)
        image_for_ocr = pipeline[1](preprocessed_image, category)

        # Step 3: Perform OCR using the category-specific function
        ocr_function = pipeline[2]
        ocr_results = ocr_function(image_for_ocr) # Returns list of {'box':..., 'text':..., 'conf':...}

        # Step 4: Split text based on position
        image_height = image_for_ocr.shape[0]
        split_texts = split_text_top_bottom(ocr_results, image_height) # Returns {'top_text': ..., 'bottom_text': ...}

        # --- Step 5: Apply Post-Processing ---
        final_formatted_result = apply_post_processing(category, split_texts)

        # --- Step 6: Add category to the final result ---
        final_formatted_result['category'] = category

        log.info(f"OCR pipeline and post-processing for {category} finished successfully.")
        return final_formatted_result # Return the dictionary from post-processing (now including category)

    except Exception as e:
        log.error(f"Error during OCR pipeline execution for {category}: {e}", exc_info=True)
        # Return consistent error format, including category
        return {'category': category, 'status': f'Error during {category} pipeline', 'formatted_top': '', 'formatted_bottom': ''}