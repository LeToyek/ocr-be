import argparse
from core.processing import process_image
from utils.logger import log
import config # Import config to potentially use defaults
import os # Import os module for directory operations
import glob # Import glob to find files matching a pattern
import pandas as pd # Import pandas for Excel export
import matplotlib.pyplot as plt # Import matplotlib for plotting
from collections import Counter # Import Counter for statistics
import time # Import the time module

def main():
    """Main function to parse arguments and trigger processing for a folder."""
    parser = argparse.ArgumentParser(description="OCR Lot No Application - Folder Processing")
    # Remove the old --image-path argument
    # parser.add_argument(
    #     "--image-path",
    #     type=str,
    #     required=True,
    #     help="Path to the image file to be processed."
    # )
    # Add a new argument for the folder path
    parser.add_argument(
        "--folder-path",
        type=str,
        required=True,
        help="Path to the folder containing image files to be processed."
    )
    # Add argument for output Excel file path (optional)
    parser.add_argument(
        "--output-excel",
        type=str,
        default=None, # Default to None, meaning don't save unless specified
        help="Optional path to save the processing results as an Excel file."
    )
    # Add argument to show statistics plot (optional flag)
    parser.add_argument(
        "--show-stats",
        action='store_true', # Makes it a flag, True if present, False otherwise
        help="Optional flag to display a plot of error message statistics."
    )

    args = parser.parse_args()

    log.info("Application started.")
    log.debug(f"Arguments received: {args}")

    folder_path_to_process = args.folder_path
    output_excel_path = args.output_excel
    show_statistics = args.show_stats

    # Validate the folder path
    if not os.path.isdir(folder_path_to_process):
        log.error(f"Error: Provided path '{folder_path_to_process}' is not a valid directory.")
        print(f"Error: Provided path '{folder_path_to_process}' is not a valid directory.")
        return # Exit if the path is invalid

    log.info(f"Processing images in folder: {folder_path_to_process}")

    # Define allowed image extensions
    allowed_extensions = ('*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tiff')
    image_files = []
    for ext in allowed_extensions:
        image_files.extend(glob.glob(os.path.join(folder_path_to_process, ext)))

    if not image_files:
        log.warning(f"No image files found in folder: {folder_path_to_process}")
        print(f"No image files found in folder: {folder_path_to_process}")
        return

    results_list = [] # Store results for all images
    total_start_time = time.perf_counter() # Start timer for overall processing

    # Process each image file found
    for i, image_path in enumerate(image_files):
        image_basename = os.path.basename(image_path)
        log.info(f"--- [{i+1}/{len(image_files)}] Processing image: {image_basename} ---")
        iteration_start_time = time.perf_counter() # Start timer for this iteration
        processing_duration = None # Initialize duration
        try:
            # Capture the returned dictionary for the current image
            result_dict = process_image(image_path)
            # Add image path to the result for context
            result_dict['source_image'] = image_basename # Store only basename for cleaner Excel

        except Exception as e:
            log.error(f"Failed to process image {image_path}: {e}", exc_info=True)
            # Optionally add an error entry to the results list
            error_msg = f'Processing failed: {e}'
            result_dict = { # Create a result dict even on failure to store duration
                'source_image': image_basename,
                'status': 'error',
                'message': error_msg,
                'category': 'N/A',
                'formatted_top': 'N/A',
                'formatted_bottom': 'N/A'
            }
            print(f"Error processing {image_basename}: {e}")
        finally:
            iteration_end_time = time.perf_counter() # End timer for this iteration
            processing_duration = iteration_end_time - iteration_start_time
            # Add processing duration to the result dictionary
            result_dict['processing_time_seconds'] = round(processing_duration, 3)
            results_list.append(result_dict) # Append result after adding duration
            log.info(f"--- Finished processing: {image_basename} in {processing_duration:.3f} seconds ---")


    total_end_time = time.perf_counter() # End timer for overall processing
    total_duration = total_end_time - total_start_time
    log.info(f"Finished processing all {len(image_files)} images in {total_duration:.3f} seconds.")
    if image_files: # Avoid division by zero if no images were found
        avg_duration = total_duration / len(image_files)
        log.info(f"Average processing time per image: {avg_duration:.3f} seconds.")


    # --- Save results to Excel if path provided ---
    if output_excel_path:
        try:
            log.info(f"Saving results to Excel file: {output_excel_path}")
            df = pd.DataFrame(results_list)
            # Define column order for better readability, adding the new time column
            column_order = ['source_image', 'status', 'message', 'category', 'formatted_top', 'formatted_bottom', 'processing_time_seconds']
            # Ensure all expected columns exist, add if missing
            for col in column_order:
                if col not in df.columns:
                    df[col] = None # Or pd.NA
            df = df[column_order] # Reorder columns
            df.to_excel(output_excel_path, index=False)
            log.info(f"Successfully saved results to {output_excel_path}")
            print(f"Results saved to: {output_excel_path}")
        except Exception as e:
            log.error(f"Failed to save results to Excel file {output_excel_path}: {e}", exc_info=True)
            print(f"Error saving results to Excel: {e}")

    # --- Show error statistics if flag provided ---
    if show_statistics:
        try:
            log.info("Generating error statistics...")
            error_messages = [r['message'] for r in results_list if r.get('status') == 'error' and 'message' in r]

            if not error_messages:
                log.info("No errors found to generate statistics.")
                print("No errors found to generate statistics.")
            else:
                message_counts = Counter(error_messages)
                messages = list(message_counts.keys())
                counts = list(message_counts.values())

                plt.figure(figsize=(10, max(6, len(messages) * 0.5))) # Adjust figure size
                plt.barh(range(len(messages)), counts, tick_label=messages)
                plt.xlabel('Count')
                plt.ylabel('Error Message')
                plt.title('Error Message Frequency')
                plt.tight_layout() # Adjust layout to prevent labels overlapping
                log.info("Displaying error statistics plot...")
                print("Displaying error statistics plot...")
                plt.show()
                log.info("Plot closed.")

        except Exception as e:
            log.error(f"Failed to generate or display statistics plot: {e}", exc_info=True)
            print(f"Error generating statistics plot: {e}")


    log.info(f"Application finished processing folder: {folder_path_to_process}")

if __name__ == "__main__":
    main()