# core/ocr_pipeline.py
from utils.logger import log
import numpy as np
import os
import cv2
from core.preprocessing import apply_preprocessing_pipeline
from core.ocr import perform_easyocr, perform_cap_ocr_yolo, split_text_top_bottom, draw_ocr_results
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
    # If you have specific segmentation logic before OCR, implement it here.
    # Otherwise, just return the image for the OCR step.
    return image # Return the preprocessed image directly to OCR

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

def run_ocr_pipeline(image: np.ndarray, category: str, image_path: str = None) -> dict:
    """
    Runs the appropriate OCR pipeline based on the category, splits text,
    and applies post-processing.
    """
    if category not in PIPELINE_STEPS:
        return {'category': category, 'status': 'Error: Unknown category', 'formatted_top': '', 'formatted_bottom': ''}

    pipeline = PIPELINE_STEPS[category]
    current_data = image # Start with the cropped image
    
    # Create output directory for intermediate images if image_path is provided
    output_dir = None
    if image_path:
        # Get the base filename without extension
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        # Create output directory
        output_dir = os.path.join(os.path.dirname(image_path), base_name)
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the original cropped image
        cv2.imwrite(os.path.join(output_dir, "01_raw.jpg"), image)

    try:
        # Step 1: Preprocessing
        preprocessed_image = pipeline[0](current_data, category)
        if output_dir:
            cv2.imwrite(os.path.join(output_dir, "02_preprocessed.jpg"), preprocessed_image)

        # Step 2: Character Extraction (currently pass-through)
        image_for_ocr = pipeline[1](preprocessed_image, category)
        if output_dir:
            cv2.imwrite(os.path.join(output_dir, "03_extraction.jpg"), image_for_ocr)

        # Step 3: Perform OCR using the category-specific function
        ocr_function = pipeline[2]
        ocr_results = ocr_function(image_for_ocr) # Returns list of {'box':..., 'text':..., 'conf':...}
        
        log.debug(f"OCR Results for {category}: {len(ocr_results)} items found")
        if len(ocr_results) > 0:
            log.debug(f"First result sample: {ocr_results[0]}")
        
        # Draw bounding boxes on the image and save
        if output_dir and ocr_results:
            try:
                # Draw boxes and save
                image_with_boxes = draw_ocr_results(image_for_ocr.copy(), ocr_results)
                cv2.imwrite(os.path.join(output_dir, "04_ocr_results.jpg"), image_with_boxes)
            except Exception as e:
                log.error(f"Error drawing or saving OCR results: {e}", exc_info=True)

        # Step 4: Split text based on position
        image_height = image_for_ocr.shape[0]
        split_texts = split_text_top_bottom(ocr_results, image_height) # Returns {'top_text': ..., 'bottom_text': ...}
        log.debug(f"Splitssssss texts for {category}: {split_texts}")
        # print("SPLIT TEXTSSSS ",split_texts)
        # print("SPLIT TEXTSSSS ",split_texts['top_text'])
        # print("CATEGORYYY ",category)

        # Step 5: Apply post-processing to the split text
        post_processing_result = apply_post_processing(category,split_texts)
        
        # Combine all results into a single dictionary
        result = {
            'category': category,
            **post_processing_result, # Unpack the post-processing result (status, formatted_top, formatted_bottom)
        }
        
        return result
        
    except Exception as e:
        error_msg = f"Error in OCR pipeline for {category}: {str(e)}"
        log.error(error_msg, exc_info=True)
        return {
            'category': category,
            'status': f'Error: {str(e)}',
            'formatted_top': '',
            'formatted_bottom': ''
        }