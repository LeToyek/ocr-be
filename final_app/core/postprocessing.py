# core/postprocessing.py
import re
from utils.logger import log

def _validate_chars(text: str, valid_chars: set, ignore_chars: set = None) -> bool:
    """Checks if all characters in the text are valid, ignoring specified characters."""
    if ignore_chars is None:
        ignore_chars = set()
    for char in text:
        if char in ignore_chars:
            continue
        if char not in valid_chars:
            return False
    return True

def format_cap_text(split_texts: dict) -> dict:
    """
    Applies formatting rules for the CAP category based on Lokal/Ekspor format.

    Args:
        split_texts (dict): A dictionary with 'top_text' and 'bottom_text'.

    Returns:
        dict: A dictionary with 'status' ('success' or 'error'), 'message' (string description),
              'formatted_top', and 'formatted_bottom'.
    """
    teks_atas_raw_input = split_texts.get('top_text', '') # Keep original raw input if needed
    teks_bawah_raw_input = split_texts.get('bottom_text', '') # Keep original raw input if needed

    # Processed raw text (uppercase, no spaces) - used for logic
    teks_atas_processed = teks_atas_raw_input.replace(" ", "").upper()
    teks_bawah_processed = teks_bawah_raw_input.replace(" ", "").upper()

    # print("TEKS ATASSSSS ",teks_atas_processed)


    if not teks_atas_processed:
        # Removed raw_top and raw_bottom
        return {'status': 'error', 'message': 'Missing top text', 'formatted_top': '', 'formatted_bottom': ''}
    if not teks_bawah_processed:
        # Removed raw_top and raw_bottom
        return {'status': 'error', 'message': 'Missing bottom text', 'formatted_top': teks_atas_processed, 'formatted_bottom': ''}

    # Use processed versions for logic from here
    teks_atas = teks_atas_processed
    teks_bawah = teks_bawah_processed

    log.debug(f"Processed CAP text - Top: '{teks_atas}', Bottom: '{teks_bawah}'")

    # Determine format based on the second-to-last character of the original top text
    # Need to handle potential short strings
    format_type = "Unknown"
    if len(teks_atas) >= 2:
        if teks_atas[-2] == 'K':
            format_type = "Lokal"
        else:
            # Assuming anything not ending in 'K' at position -2 is Ekspor for now
            format_type = "Ekspor"
    else:
         # If text is too short to determine, default or raise error? Let's default to Ekspor check
         log.warning(f"Top text '{teks_atas}' too short to reliably determine format based on K[-2]. Assuming Ekspor.")
         format_type = "Ekspor"


    log.info(f"Determined CAP format: {format_type}")

    # --- Lokal Format ---
    if format_type == "Lokal":
        valid_chars_atas = set("0123456789K")
        valid_chars_bawah = set("0123456789")
        ignore_chars_validation = set(".: ")

        # 1. Validate length (before formatting)
        if len(teks_atas) != 8:
            msg = f'Invalid length for teksAtas Lokal (expected 8, got {len(teks_atas)})'
            # Removed raw_top and raw_bottom
            return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}
        if len(teks_bawah) != 4:
            msg = f'Invalid length for teksBawah Lokal (expected 4, got {len(teks_bawah)})'
            # Removed raw_top and raw_bottom
            return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}

        # 2. Validate characters (before formatting)
        if not _validate_chars(teks_atas, valid_chars_atas):
             msg = 'Invalid characters in teksAtas Lokal'
             # Removed raw_top and raw_bottom
             return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}
        if not _validate_chars(teks_bawah, valid_chars_bawah):
             msg = 'Invalid characters in teksBawah Lokal'
             # Removed raw_top and raw_bottom
             return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}

        # 3. Apply formatting
        try:
            # Format top: XX.XX.XX K
            formatted_top = f"{teks_atas[0:2]}.{teks_atas[2:4]}.{teks_atas[4:6]} {teks_atas[6:8]}"
            # Format bottom: XX:XX
            formatted_bottom = f"{teks_bawah[0:2]}:{teks_bawah[2:4]}"
        except IndexError:
             msg = 'Error during Lokal formatting (Index out of bounds)'
             # Removed raw_top and raw_bottom
             return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}

        # Success case for Lokal
        # Removed raw_top and raw_bottom
        return {'status': 'success', 'message': 'Valid Lokal format', 'formatted_top': formatted_top, 'formatted_bottom': formatted_bottom}

    # --- Ekspor Format ---
    elif format_type == "Ekspor":
        log.debug("Applying CAP Ekspor formatting rules V2")

        # Remove all non-digit characters
        numeric_atas_full = re.sub(r'\D', '', teks_atas)
        numeric_bawah_full = re.sub(r'\D', '', teks_bawah)
        log.debug(f"Digits only - Top: '{numeric_atas_full}', Bottom: '{numeric_bawah_full}'")

        # Validate length (must have at least 6 digits)
        if len(numeric_atas_full) < 6:
             msg = f"Invalid length for teksAtas Ekspor after removing non-digits (Expected at least 6 digits, got {len(numeric_atas_full)})"
             return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}
        if len(numeric_bawah_full) < 6:
             msg = f"Invalid length for teksBawah Ekspor after removing non-digits (Expected at least 6 digits, got {len(numeric_bawah_full)})"
             return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}

        # Take the first 6 digits
        numeric_atas_6 = numeric_atas_full[:6]
        numeric_bawah_6 = numeric_bawah_full[:6]
        log.debug(f"First 6 digits - Top: '{numeric_atas_6}', Bottom: '{numeric_bawah_6}'")

        # Validate the 6 digits (redundant check if re.sub worked correctly, but safe)
        if not numeric_atas_6.isdigit():
            msg = f"Invalid characters in first 6 digits of teksAtas Ekspor ('{numeric_atas_6}')"
            return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}
        if not numeric_bawah_6.isdigit():
            msg = f"Invalid characters in first 6 digits of teksBawah Ekspor ('{numeric_bawah_6}')"
            return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}

        # Format numeric part with slashes: DD/DD/DD
        # Note: Your final example uses the 6 digits directly, not the slash-formatted version.
        # Following the final example:
        formatted_numeric_atas = f"{numeric_atas_6[0:2]}/{numeric_atas_6[2:4]}/{numeric_atas_6[4:6]}"
        formatted_numeric_bawah = f"{numeric_bawah_6[0:2]}/{numeric_bawah_6[2:4]}/{numeric_bawah_6[4:6]}"

        # Reconstruct the final strings with NSX and HSD prefixes
        formatted_top = f"NSX {formatted_numeric_atas}"
        formatted_bottom = f"HSD {formatted_numeric_bawah}"

        log.debug(f"Final formatted Ekspor - Top: '{formatted_top}', Bottom: '{formatted_bottom}'")

        # Success case for Ekspor
        return {'status': 'success', 'message': 'Valid Ekspor format', 'formatted_top': formatted_top, 'formatted_bottom': formatted_bottom}

    else:
        # Should not happen if logic above is correct
        msg = 'Error: Unknown format type determined'
        # Removed raw_top and raw_bottom
        return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}


# --- Add functions for other categories later ---
def format_box_text(split_texts: dict) -> dict:
    """
    Applies formatting rules for the BOX category based on Lokal/Ekspor format.

    Args:
        split_texts (dict): A dictionary with 'top_text' and 'bottom_text'.

    Returns:
        dict: A dictionary with 'status' ('success' or 'error'), 'message' (string description),
              'formatted_top', and 'formatted_bottom'.
    """
    teks_atas_raw_input = split_texts.get('top_text', '')
    teks_bawah_raw_input = split_texts.get('bottom_text', '')

    # Processed raw text (uppercase, no spaces) - used for logic
    teks_atas_processed = teks_atas_raw_input.replace(" ", "").upper()
    teks_bawah_processed = teks_bawah_raw_input.replace(" ", "").upper()

    # throw away special character (only accept number and alphabet)
    teks_atas_processed = re.sub(r'[^A-Z0-9]', '', teks_atas_processed)
    teks_bawah_processed = re.sub(r'[^A-Z0-9]', '', teks_bawah_processed)

    # Huruf menjadi angka "O" => 0, "I" => 1, "Z" => 2, dst.
    teks_atas_processed = teks_atas_processed.replace("O", "0")
    teks_atas_processed = teks_atas_processed.replace("I", "1")
    teks_atas_processed = teks_atas_processed.replace("Z", "2")

    teks_bawah_processed = teks_bawah_processed.replace("O", "0")
    teks_bawah_processed = teks_bawah_processed.replace("I", "1")
    teks_bawah_processed = teks_bawah_processed.replace("Z", "2")
    
    if not teks_atas_processed:
        return {'status': 'error', 'message': 'Missing top text', 'formatted_top': '', 'formatted_bottom': ''}
    if not teks_bawah_processed:
        return {'status': 'error', 'message': 'Missing bottom text', 'formatted_top': teks_atas_processed, 'formatted_bottom': ''}

    # Use processed versions for logic from here
    teks_atas = teks_atas_processed
    teks_bawah = teks_bawah_processed

    log.debug(f"Processed BOX text - Top: '{teks_atas}', Bottom: '{teks_bawah}'")

    # Determine format based on the second-to-last character of the original top text
    format_type = "Unknown"
    if len(teks_atas) >= 2:
        if teks_atas[-2] == 'K':
            format_type = "Lokal"
        else:
            format_type = "Ekspor"
    else:
         log.warning(f"Top text '{teks_atas}' too short to reliably determine format based on K[-2]. Assuming Ekspor.")
         format_type = "Ekspor"

    log.info(f"Determined BOX format: {format_type}")

    # --- Lokal Format ---
    if format_type == "Lokal":
        valid_chars_atas = set("0123456789K")
        valid_chars_bawah = set("0123456789")
        # ignore_chars_validation = set(".: ") # Not used in BOX Lokal formatting

        # 1. Validate length (before formatting)
        if len(teks_atas) != 8:
            msg = f'Invalid length for teksAtas Lokal (expected 8, got {len(teks_atas)})'
            return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}

        # Adjust teks_bawah length
        if len(teks_bawah) == 1:
            teks_bawah = teks_bawah + "0000"
            log.debug(f"Padded teks_bawah to 5 digits: {teks_bawah}")
        elif len(teks_bawah) != 5:
            msg = f'Invalid length for teksBawah Lokal (expected 5 or 1, got {len(teks_bawah)})'
            return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}

        # 2. Validate characters (after potential padding)
        if not _validate_chars(teks_atas, valid_chars_atas):
             msg = 'Invalid characters in teksAtas Lokal'
             return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}
        if not _validate_chars(teks_bawah, valid_chars_bawah):
             msg = 'Invalid characters in teksBawah Lokal'
             return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}

        # 3. Apply formatting
        try:
            # Format top: XX.XX.XX K
            formatted_top = f"{teks_atas[0:2]}.{teks_atas[2:4]}.{teks_atas[4:6]} {teks_atas[6:8]}"
            # Format bottom: XXXXX (no changes needed after length adjustment)
            formatted_bottom = teks_bawah
        except IndexError:
             msg = 'Error during Lokal formatting (Index out of bounds)'
             return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}

        return {'status': 'success', 'message': 'Valid Lokal format', 'formatted_top': formatted_top, 'formatted_bottom': formatted_bottom}

    # --- Ekspor Format ---
    elif format_type == "Ekspor":
        # Remove all non-digit characters
        numeric_atas_full = re.sub(r'\D', '', teks_atas)
        numeric_bawah_full = re.sub(r'\D', '', teks_bawah)
        log.debug(f"Digits only - Top: '{numeric_atas_full}', Bottom: '{numeric_bawah_full}'")

        # Validate length (must have at least 6 digits)
        if len(numeric_atas_full) < 6:
             msg = f"Invalid length for teksAtas Ekspor after removing non-digits (Expected at least 6 digits, got {len(numeric_atas_full)})"
             return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}
        if len(numeric_bawah_full) < 6:
             msg = f"Invalid length for teksBawah Ekspor after removing non-digits (Expected at least 6 digits, got {len(numeric_bawah_full)})"
             return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}

        # Take the first 6 digits
        numeric_atas_6 = numeric_atas_full[:6]
        numeric_bawah_6 = numeric_bawah_full[:6]
        log.debug(f"First 6 digits - Top: '{numeric_atas_6}', Bottom: '{numeric_bawah_6}'")

        # Validate the 6 digits (redundant check if re.sub worked correctly, but safe)
        if not numeric_atas_6.isdigit():
            msg = f"Invalid characters in first 6 digits of teksAtas Ekspor ('{numeric_atas_6}')"
            return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}
        if not numeric_bawah_6.isdigit():
            msg = f"Invalid characters in first 6 digits of teksBawah Ekspor ('{numeric_bawah_6}')"
            return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}

        # Format numeric part with slashes: DD/DD/DD
        # Note: Your final example uses the 6 digits directly, not the slash-formatted version.
        # Following the final example:
        formatted_numeric_atas = f"{numeric_atas_6[0:2]}/{numeric_atas_6[2:4]}/{numeric_atas_6[4:6]}"
        formatted_numeric_bawah = f"{numeric_bawah_6[0:2]}/{numeric_bawah_6[2:4]}/{numeric_bawah_6[4:6]}"

        # Reconstruct the final strings with NSX and HSD prefixes
        formatted_top = f"NSX {formatted_numeric_atas}"
        formatted_bottom = f"HSD {formatted_numeric_bawah}"

        log.debug(f"Final formatted Ekspor - Top: '{formatted_top}', Bottom: '{formatted_bottom}'")


        return {'status': 'success', 'message': 'Valid Ekspor format', 'formatted_top': formatted_top, 'formatted_bottom': formatted_bottom}

    else:
        # Should not happen if logic above is correct
        msg = 'Error: Unknown format type determined'
        return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}


# --- Add functions for other categories later
def format_soyjoy_text(split_texts: dict) -> dict:
    """
    Applies formatting rules for the SOYJOY category.

    Args:
        split_texts (dict): A dictionary with 'top_text' and 'bottom_text'.

    Returns:
        dict: A dictionary with 'status' ('success' or 'error'), 'message' (string description),
              'formatted_top', and 'formatted_bottom'.
    """
    teks_atas_raw_input = split_texts.get('top_text', '')
    teks_bawah_raw_input = split_texts.get('bottom_text', '')

    # Processed raw text (uppercase, no spaces) - used for logic
    teks_atas_processed = teks_atas_raw_input.replace(" ", "").upper()
    teks_bawah_processed = teks_bawah_raw_input.replace(" ", "").upper()

    # throw away special character (only accept number and alphabet)
    teks_atas_processed = re.sub(r'[^A-Z0-9]', '', teks_atas_processed)
    teks_bawah_processed = re.sub(r'[^A-Z0-9]', '', teks_bawah_processed)

    # Huruf menjadi angka "O" => 0, "I" => 1, "Z" => 2, dst.
    teks_atas_processed = teks_atas_processed.replace("O", "0")
    teks_atas_processed = teks_atas_processed.replace("I", "1")
    teks_atas_processed = teks_atas_processed.replace("Z", "2")

    teks_bawah_processed = teks_bawah_processed.replace("O", "0")
    teks_bawah_processed = teks_bawah_processed.replace("I", "1")
    teks_bawah_processed = teks_bawah_processed.replace("Z", "2")

    if not teks_atas_processed:
        return {'status': 'error', 'message': 'Missing top text', 'formatted_top': '', 'formatted_bottom': ''}
    if not teks_bawah_processed:
        return {'status': 'error', 'message': 'Missing bottom text', 'formatted_top': teks_atas_processed, 'formatted_bottom': ''}

    # Use processed versions for logic from here
    teks_atas = teks_atas_processed
    teks_bawah = teks_bawah_processed

    log.debug(f"Processed SOYJOY text - Top: '{teks_atas}', Bottom: '{teks_bawah}'")

    valid_chars = set("0123456789")
    # ignore_chars_validation = set(".:") # Not used directly in validation

    # 1. Validate length (before formatting)
    if len(teks_atas) != 6:
        msg = f'Invalid length for teksAtas SOYJOY (expected 6, got {len(teks_atas)})'
        return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}
    if len(teks_bawah) != 4:
        msg = f'Invalid length for teksBawah SOYJOY (expected 4, got {len(teks_bawah)})'
        return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}

    # 2. Validate characters
    if not _validate_chars(teks_atas, valid_chars):
         msg = 'Invalid characters in teksAtas SOYJOY (only digits allowed)'
         return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}
    if not _validate_chars(teks_bawah, valid_chars):
         msg = 'Invalid characters in teksBawah SOYJOY (only digits allowed)'
         return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}

    # 3. Apply formatting
    try:
        # Format top: XX.XX.XX
        formatted_top = f"{teks_atas[0:2]}.{teks_atas[2:4]}.{teks_atas[4:6]}"
        # Format bottom: XX:XX
        formatted_bottom = f"{teks_bawah[0:2]}:{teks_bawah[2:4]}"
    except IndexError:
         # This should ideally not happen if length checks passed, but good practice
         msg = 'Error during SOYJOY formatting (Index out of bounds)'
         return {'status': 'error', 'message': msg, 'formatted_top': teks_atas, 'formatted_bottom': teks_bawah}

    return {'status': 'success', 'message': 'Valid SOYJOY format', 'formatted_top': formatted_top, 'formatted_bottom': formatted_bottom}


POST_PROCESSING_FUNCTIONS = {
    "CAP": format_cap_text,
    "BOX": format_box_text,
    "SOYJOY": format_soyjoy_text, # Add SOYJOY function here
}

def apply_post_processing(category: str, split_texts) -> dict:
    # print("KATEGORIII ",category)
    """Applies the appropriate post-processing function based on the category."""
    if category in POST_PROCESSING_FUNCTIONS:
        formatter = POST_PROCESSING_FUNCTIONS[category]
        log.info(f"Applying post-processing for category: {category}")
        # print("KATEGORIII ",category)
        return formatter(split_texts)
    else:
        # print("FAILEDDDD")
        msg = f"No post-processing function defined for category: {category}"
        log.warning(f"{msg}. Returning raw split text.")
        # Return a consistent dictionary format even if no processing is done
        raw_top = split_texts.get('top_text', '')
        raw_bottom = split_texts.get('bottom_text', '')
        # Removed raw_top and raw_bottom keys
        return {
            'status': 'error', # Treat no formatting as an error/incomplete state
            'message': msg,
            'formatted_top': raw_top,
            'formatted_bottom': raw_bottom
        }