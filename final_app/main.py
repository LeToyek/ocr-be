import argparse
from core.processing import process_image
from utils.logger import log
import config
import time

def main():
    """Main function to parse arguments and trigger processing for a single image."""
    parser = argparse.ArgumentParser(description="OCR Lot No Application - Single Image Processing")
    parser.add_argument(
        "--image-path",
        type=str,
        required=True,
        help="Path to the image file to be processed."
    )

    args = parser.parse_args()
    log.disabled = True
    log.info("Application started.")
    log.debug(f"Arguments received: {args}")

    image_path = args.image_path
    start_time = time.perf_counter()

    try:
        result = process_image(image_path)
        processing_duration = time.perf_counter() - start_time
        log.info(f"Processing completed in {processing_duration:.3f} seconds")
        print("Processing Result:", result)
        
    except Exception as e:
        log.error(f"Failed to process image {image_path}: {e}", exc_info=True)
        print(f"Error processing image: {e}")

    log.info("Application finished.")

if __name__ == "__main__":
    main()