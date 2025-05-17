import streamlit as st
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import json # Import json for pretty printing

# Load environment variables
load_dotenv('../final_app/.env')
BE_URL = os.getenv('BE_URL', 'http://localhost:4091') # Ensure http:// or https:// is included

# Initialize session state for token and user info
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

def format_datetime(dt_str):
    """Formats datetime string to a readable format."""
    try:
        # Handle potential timezone info or lack thereof
        if dt_str.endswith('Z'):
             dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        else:
             dt = datetime.fromisoformat(dt_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        return dt_str # Return original if parsing fails

def view_ocr_results():
    """Displays the existing OCR results viewer."""
    st.title('OCR Results Viewer')

    try:
        # Use the BE_URL environment variable
        response = requests.get(f'{BE_URL}/api/folder')
        if response.status_code == 200:
            data = response.json()

            if data.get('error') is False and 'data' in data:
                folders = [folder for folder in data['data'] if folder is not None]

                # Sort folders by modified date descending
                folders.sort(key=lambda x: x.get('modified', ''), reverse=True)

                for folder in folders:
                    # Use folder name and modified date in expander title
                    folder_name = folder.get('name', 'Unnamed Folder')
                    modified_date = folder.get('modified')
                    expander_title = f"📁 {folder_name}"
                    if modified_date:
                         expander_title += f" - {format_datetime(modified_date)}"

                    with st.expander(expander_title):
                        files = folder.get('files', [])
                        # Sort files by name
                        files.sort(key=lambda x: x.get('name', ''))

                        if files:
                            # Grid view with 3 columns
                            cols = st.columns(3)
                            for idx, file in enumerate(files):
                                with cols[idx % 3]:
                                    # Ensure file path is correctly constructed
                                    file_path = file.get('path')
                                    if file_path:
                                        image_url = f"{BE_URL}{file_path}"
                                        st.image(image_url, caption=file.get('name', 'No Name'), use_container_width=True)
                                        st.write(f"Size: {file.get('size', 0)/1024:.2f} KB")
                                        file_modified = file.get('modified')
                                        if file_modified:
                                             st.write(f"Modified: {format_datetime(file_modified)}")
                                    else:
                                        st.warning(f"Could not get path for file: {file.get('name', 'Unknown')}")
                        else:
                            st.info("No files found in this folder.")
            else:
                st.error(f"API returned an error: {data.get('message', 'Unknown error')}")

        else:
            st.error(f"Error fetching data: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to the server at {BE_URL}: {str(e)}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")


def login_page():
    """Displays the login form."""
    st.title("Login")

    if st.session_state.token:
        st.success("You are already logged in.")
        if st.session_state.user_info:
             st.write(f"Logged in as: {st.session_state.user_info.get('lg_name', 'Unknown User')}")
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.user_info = None
            st.experimental_rerun() # Rerun to clear the page

    else:
        with st.form("login_form"):
            lg_nik = st.text_input("NIK")
            lg_password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")

            if submit_button:
                try:
                    login_data = {
                        "lg_nik": lg_nik,
                        "lg_password": lg_password
                    }
                    # Use the BE_URL environment variable
                    response = requests.post(f'{BE_URL}/api/auth/login', json=login_data)

                    if response.status_code == 200:
                        data = response.json()
                        if data.get('error') is False and 'data' in data and 'token' in data['data']:
                            st.session_state.token = data['data']['token']
                            st.session_state.user_info = data['data'].get('user', {}) # Store user info if available
                            st.success("Login successful!")
                            st.experimental_rerun() # Rerun to show logged-in state
                        else:
                            st.error(f"Login failed: {data.get('message', 'Invalid credentials')}")
                    else:
                        st.error(f"Login failed: {response.status_code} - {response.text}")

                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to connect to the server at {BE_URL}: {str(e)}")
                except Exception as e:
                    st.error(f"An unexpected error occurred during login: {str(e)}")

def create_product_batch_page():
    """Displays the form to create a product batch with document."""
    st.title("Create Product Batch")

    if not st.session_state.token:
        st.warning("Please login first to create a product batch.")
        login_page() # Show login form if not logged in
        return

    st.success("You are logged in. You can now create a product batch.")
    if st.session_state.user_info:
         st.write(f"Logged in as: {st.session_state.user_info.get('lg_name', 'Unknown User')}")

    with st.form("create_product_batch_form"):
        st.subheader("Product Batch Details")
        category_id = st.number_input("Category ID", min_value=1, step=1)
        issued_date = st.date_input("Issued Date")
        top_text = st.text_area("Top Text")
        bottom_text = st.text_area("Bottom Text")

        submit_button = st.form_submit_button("Create Product Batch")

        if submit_button:
            if not category_id or not issued_date or not top_text or not bottom_text:
                st.warning("Please fill in all fields.")
            else:
                try:
                    batch_data = {
                        "category_id": category_id,
                        "issued_date": issued_date.strftime('%Y-%m-%d'), # Format date to YYYY-MM-DD
                        "top_text": top_text,
                        "bottom_text": bottom_text
                    }

                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"{st.session_state.token}" # Include the token
                    }

                    # Use the BE_URL environment variable
                    response = requests.post(f'{BE_URL}/api/product-batch/with-document', json=batch_data, headers=headers)

                    if response.status_code == 201:
                        data = response.json()
                        st.success("Product batch created successfully!")
                        st.write("Response Data:")
                        st.json(data) # Display the response data
                    else:
                        st.error(f"Failed to create product batch: {response.status_code} - {response.text}")
                        try:
                            error_data = response.json()
                            st.json(error_data) # Display error details if available
                        except json.JSONDecodeError:
                            pass # Ignore if response is not JSON

                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to connect to the server at {BE_URL}: {str(e)}")
                except Exception as e:
                    st.error(f"An unexpected error occurred during product batch creation: {str(e)}")


# Main application logic with navigation
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["OCR Results Viewer", "Create Product Batch", "Login"])

    if page == "OCR Results Viewer":
        view_ocr_results()
    elif page == "Create Product Batch":
        create_product_batch_page()
    elif page == "Login":
        login_page()

if __name__ == "__main__":
    main()