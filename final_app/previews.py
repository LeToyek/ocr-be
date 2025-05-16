import streamlit as st
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../final_app/.env')
BE_URL = os.getenv('BE_URL', 'localhost:4091')

def format_datetime(dt_str):
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def main():
    st.title('OCR Results Viewer')
    
    try:
        response = requests.get(f'{BE_URL}/api/folder')
        if response.status_code == 200:
            data = response.json()
            
            if data['error'] == False and 'data' in data:
                folders = [folder for folder in data['data'] if folder is not None]
                
                for folder in folders:
                    with st.expander(f"📁 {folder['name']} - {format_datetime(folder['modified'])}"):
                        if 'files' in folder:
                            files = sorted(folder['files'], key=lambda x: x['name'])
                            
                            # Grid view with 3 columns
                            cols = st.columns(3)
                            for idx, file in enumerate(files):
                                with cols[idx % 3]:
                                    image_url = f"http://{BE_URL}{file['path']}"
                                    st.image(image_url, caption=file['name'], use_container_width=True)
                                    st.write(f"Size: {file['size']/1024:.2f} KB")
                                    st.write(f"Modified: {format_datetime(file['modified'])}")
        else:
            st.error(f"Error fetching data: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to the server: {str(e)}")
        
if __name__ == "__main__":
    main()