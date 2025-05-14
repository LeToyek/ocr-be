import streamlit as st
from PIL import Image
import numpy as np
import cv2
import io
import sys
import os

# Add the project root to the Python path to allow imports from core and utils
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Import necessary functions from your project structure
from utils.logger import log # Optional: Use Streamlit's logging instead if preferred
# Import detection and processing helpers
from utils.logger import log
# --- MODIFIED IMPORTS ---
from core.detection import detect_objects, detect_objects_by_image # Import detection

# --- END MODIFIED IMPORTS ---
from core.preprocessing import apply_preprocessing_pipeline
from core.ocr import perform_easyocr, perform_cap_ocr_yolo, split_text_top_bottom, draw_ocr_results
from core.postprocessing import apply_post_processing
from core.ocr_pipeline import OCR_FUNCTIONS, PIPELINE_STEPS, extract_characters

# --- Streamlit App UI ---
st.set_page_config(layout="wide")
st.title("OCR Lot Number Pipeline Visualization")

# --- Initialize Session State ---
if 'image_cv' not in st.session_state:
    st.session_state.image_cv = None
if 'image_pil' not in st.session_state:
    st.session_state.image_pil = None
if 'processing_triggered' not in st.session_state:
    st.session_state.processing_triggered = False


# --- Input Section ---
col1, col2 = st.columns([2, 1]) # Adjust column ratio if needed

with col1:
    st.header("Input Image")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "bmp", "tiff"])

    # Load image when uploaded and store in session state
    if uploaded_file is not None:
        # Check if it's a new file upload
        if st.session_state.image_pil is None or uploaded_file.getvalue() != st.session_state.get('uploaded_file_bytes', None):
            st.session_state.uploaded_file_bytes = uploaded_file.getvalue()
            image_pil = Image.open(io.BytesIO(st.session_state.uploaded_file_bytes)).convert('RGB')
            st.session_state.image_pil = image_pil
            st.session_state.image_cv = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
            st.session_state.processing_triggered = False # Reset processing trigger on new image
            log.info("New image loaded into session state.")

    # Display the current image from session state
    if st.session_state.image_pil is not None:
        st.subheader("Current Image")
        st.image(st.session_state.image_pil, caption="Image for Processing", use_column_width=True)

        # --- ADDED: Rotation Controls ---
        st.markdown("---")
        st.subheader("Rotate Image (Optional)")
        rotate_col1, rotate_col2, rotate_col3 = st.columns(3)
        with rotate_col1:
            if st.button("Rotate 90° CW"):
                if st.session_state.image_cv is not None:
                    st.session_state.image_cv = cv2.rotate(st.session_state.image_cv, cv2.ROTATE_90_CLOCKWISE)
                    st.session_state.image_pil = Image.fromarray(cv2.cvtColor(st.session_state.image_cv, cv2.COLOR_BGR2RGB))
                    st.session_state.processing_triggered = False # Reset processing if rotated
                    log.info("Image rotated 90 CW.")
                    st.rerun() # Rerun to update the displayed image immediately
        with rotate_col2:
             if st.button("Rotate 90° CCW"):
                if st.session_state.image_cv is not None:
                    st.session_state.image_cv = cv2.rotate(st.session_state.image_cv, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    st.session_state.image_pil = Image.fromarray(cv2.cvtColor(st.session_state.image_cv, cv2.COLOR_BGR2RGB))
                    st.session_state.processing_triggered = False
                    log.info("Image rotated 90 CCW.")
                    st.rerun()
        with rotate_col3:
             if st.button("Rotate 180°"):
                if st.session_state.image_cv is not None:
                    st.session_state.image_cv = cv2.rotate(st.session_state.image_cv, cv2.ROTATE_180)
                    st.session_state.image_pil = Image.fromarray(cv2.cvtColor(st.session_state.image_cv, cv2.COLOR_BGR2RGB))
                    st.session_state.processing_triggered = False
                    log.info("Image rotated 180.")
                    st.rerun()
        # --- END ADDED Rotation Controls ---

with col2:
    st.header("Processing")
    # --- MODIFIED: Process Button ---
    # Show process button only if an image is loaded
    if st.session_state.image_cv is not None:
        if st.button("Process Current Image"):
            st.session_state.processing_triggered = True
            log.info("Processing button clicked.")
            # No rerun needed here, the rest of the script will execute below
    else:
        st.info("Upload an image to enable processing.")
    # --- END MODIFIED Process Button ---


# --- Processing and Output Section ---
# --- MODIFIED Condition ---
# Run processing only if the button was clicked in this run
if st.session_state.processing_triggered and st.session_state.image_cv is not None:
# --- END MODIFIED Condition ---
    st.markdown("---")
    st.header("Pipeline Steps & Results")

    # Use the image from session state for processing
    image_to_process = st.session_state.image_cv.copy() # Use a copy from session state

    try:
        # --- Step 1: Object Detection and Cropping (using image_to_process) ---
        st.markdown("---")
        st.subheader("1. Object Detection (Localization)") # Renumbered
        detected_category = None # Initialize detected_category
        cropped_image = None     # Initialize cropped_image
        pipeline = None          # Initialize pipeline

        try: # Wrap detection and cropping logic
            # Pass the potentially rotated image from session state
            detections, image_from_detection, model = detect_objects_by_image(image_to_process) # Use image_to_process

            # Note: image_from_detection should be the same as image_to_process if detection doesn't modify it
            # We will use image_from_detection for cropping just in case

            if image_from_detection is None:
                st.error("Failed to load image during detection. Aborting processing.")
                st.stop()

            # --- Step 2: Find the detection with the largest area ---
            largest_detection = None
            max_area = -1
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
                detected_category = largest_detection['class_name'].upper()
                log.info(f"Largest object found: {detected_category} (Area: {largest_detection['area']})")
                st.write(f"Largest object detected: **{detected_category}** (Area: {largest_detection['area']:.0f})")

                # --- Step 2: Crop the image based on the largest bounding box ---
                x1, y1, x2, y2 = largest_detection['bbox']
                # Crop from the image returned by detection function
                cropped_image = image_from_detection[int(y1):int(y2), int(x1):int(x2)]

                if cropped_image.size == 0:
                    st.error("Cropped image is empty. Check bounding box coordinates.")
                    st.stop()

                # Display the cropped image
                st.image(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB), caption=f"Cropped Image ({detected_category})", use_column_width=True)

                # --- *** ADDED: Get the pipeline AFTER successful detection and cropping *** ---
                if detected_category not in PIPELINE_STEPS:
                    st.error(f"Error: Detected category '{detected_category}' not found in PIPELINE_STEPS configuration.")
                    st.stop()
                pipeline = PIPELINE_STEPS[detected_category]
                # --- *** END ADDED SECTION *** ---

            else:
                st.warning("No valid objects ('CAP', 'BOX', 'SOYJOY') found among detections.")
                st.stop() # Stop if no valid largest object is found

        except Exception as e:
            st.error(f"An error occurred during Detection or Cropping: {e}")
            log.error(f"Detection/Cropping Error: {e}", exc_info=True)
            st.stop()
        # --- END Detection/Cropping Section ---

        # --- Check if pipeline was successfully assigned ---
        if pipeline is None:
             st.error("Pipeline could not be determined. Aborting.")
             st.stop()

        # --- Step 3: Preprocessing (on CROPPED image) --- # Renumbered
        st.markdown("---")
        st.subheader("2. Preprocessing")
        try:
            # Now 'pipeline' is guaranteed to be defined if this point is reached
            preprocess_func = pipeline[0]
            # Pass the CROPPED image and DETECTED category
            preprocessed_image = preprocess_func(cropped_image.copy(), detected_category)
            st.image(cv2.cvtColor(preprocessed_image, cv2.COLOR_BGR2RGB), caption=f"After Preprocessing ({detected_category})", use_column_width=True)
        except Exception as e:
            st.error(f"Error during Preprocessing: {e}")
            log.error(f"Preprocessing Error: {e}", exc_info=True)
            st.stop()

        # --- Step 3 -> 4: Character Extraction (on preprocessed CROPPED image) ---
        st.markdown("---")
        st.subheader("3. Character Extraction (Pass-through)")
        try:
            extract_func = pipeline[1]
             # Pass the preprocessed CROPPED image and DETECTED category
            image_for_ocr = extract_func(preprocessed_image.copy(), detected_category)
            st.image(cv2.cvtColor(image_for_ocr, cv2.COLOR_BGR2RGB), caption="Image for OCR (After Extraction Step)", use_column_width=True)
        except Exception as e:
            st.error(f"Error during Character Extraction: {e}")
            st.stop()

        # --- Step 4 -> 5: Perform OCR (on image_for_ocr) ---
        st.markdown("---")
        st.subheader("4. OCR Execution")
        ocr_results = None
        try:
            # Get the correct OCR function based on the DETECTED category
            ocr_function = pipeline[2]
            ocr_results = ocr_function(image_for_ocr.copy())
            st.write("Raw OCR Results:")
            st.json(ocr_results)

            # Visualize OCR results
            try:
                image_with_ocr_boxes = draw_ocr_results(image_for_ocr.copy(), ocr_results)
                st.image(cv2.cvtColor(image_with_ocr_boxes, cv2.COLOR_BGR2RGB), caption="OCR Results Visualization", use_column_width=True)
            except NameError:
                 st.warning("`draw_ocr_results` function not found. Skipping OCR visualization.")
            except Exception as draw_e:
                 st.warning(f"Could not visualize OCR results: {draw_e}")

        except Exception as e:
            st.error(f"Error during OCR Execution: {e}")
            st.stop()

        # --- Step 5 -> 6: Split Text ---
        st.markdown("---")
        st.subheader("6. Split Text (Top/Bottom)")
        split_texts = None
        try:
            image_height = image_for_ocr.shape[0] # Height of the cropped+preprocessed image
            split_texts = split_text_top_bottom(ocr_results, image_height)
            st.write("Split Text Results:")
            st.json(split_texts)
        except Exception as e:
            st.error(f"Error during Text Splitting: {e}")
            st.stop()

        # --- Step 6 -> 7: Post-Processing ---
        st.markdown("---")
        st.subheader("7. Post-Processing")
        final_formatted_result = None
        try:
            # Use DETECTED category for post-processing rules
            final_formatted_result = apply_post_processing(detected_category, split_texts)
            final_formatted_result['category'] = detected_category # Add detected category
            st.write("Final Formatted Result:")
            st.json(final_formatted_result)
        except Exception as e:
            st.error(f"Error during Post-Processing: {e}")
            st.stop()

        st.markdown("---")
        st.success("Pipeline execution completed!")

        # Reset the trigger after processing is done
        st.session_state.processing_triggered = False

    except Exception as e:
        st.error(f"An unexpected error occurred during pipeline execution: {e}")
        log.error(f"Pipeline Error: {e}", exc_info=True)
        st.session_state.processing_triggered = False # Also reset trigger on error

# --- Removed the elif process_button: st.warning(...) as it's handled by the button logic ---