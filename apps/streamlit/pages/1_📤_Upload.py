"""
Upload Health Data Page
Upload ZIP file from Simple Health Export CSV app
"""
import streamlit as st
import zipfile
import os
from pathlib import Path
from datetime import datetime
from utils.db import save_file_metadata, get_file_metadata

st.set_page_config(
    page_title="Upload - HealthSync AI",
    page_icon="📤",
    layout="wide"
)

st.title("📤 Upload Health Data")

if not st.session_state.get("authenticated"):
    st.warning("⚠️ Please login first!")
    st.info("Go to the main page to login")
    st.stop()

user_id = st.session_state.user_id
# Get project root (3 levels up from pages/)
project_root = Path(__file__).parent.parent.parent.parent
storage_path = project_root / "storage" / "user_data" / user_id
storage_path.mkdir(parents=True, exist_ok=True)

# Instructions
with st.expander("📖 How to Export Health Data", expanded=False):
    st.markdown("""
    **Steps to export your health data:**
    
    1. Download the **"Simple Health Export CSV"** app from the App Store
    2. Open the app and select **"All"** data types
    3. Choose **"Export as ZIP"**
    4. Transfer the ZIP file to your computer (via AirDrop, email, or Files app)
    5. Upload the ZIP file below
    
    **Note:** The ZIP file should contain CSV files with your health metrics.
    """)

# Check existing data
existing_files = get_file_metadata(user_id)
csv_files = list(storage_path.glob("*.csv")) if storage_path.exists() else []

# Check if using sample data
is_sample_data = len(csv_files) > 0 and len(csv_files) <= 4 and all(
    f.stem in ['steps', 'heart_rate', 'sleep', 'workouts'] for f in csv_files
)

if csv_files:
    if is_sample_data:
        st.info("💡 Currently using **sample data** for demo. Upload your real health data below to replace it.")
    else:
        st.info(f"📁 You have {len(csv_files)} data file(s)")
    
    if existing_files:
        with st.expander("View previous uploads"):
            for file_info in existing_files:
                st.text(f"📄 {file_info.get('filename', 'Unknown')} - {file_info.get('upload_date', 'Unknown date')}")
    
    # Option to clear existing data
    if st.button("🗑️ Clear All Data", help="This will delete all existing data files"):
        import shutil
        if storage_path.exists():
            shutil.rmtree(storage_path)
            storage_path.mkdir(parents=True, exist_ok=True)
            st.session_state.health_data_loaded = False
            st.success("✅ All data cleared!")
            st.rerun()

st.divider()

# File uploader
uploaded_file = st.file_uploader(
    "Upload ZIP file from Simple Health Export CSV app",
    type=["zip"],
    help="Select the ZIP file exported from Simple Health Export CSV app"
)

if uploaded_file:
    with st.spinner("Processing your health data..."):
        try:
            # Save uploaded file
            zip_path = storage_path / uploaded_file.name
            with open(zip_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Unzip
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(storage_path)
            
            # Count CSV files
            csv_files = list(storage_path.glob("*.csv"))
            
            # List CSV files
            csv_names = [f.name for f in csv_files]
            
            # Validate CSV files can be loaded into DuckDB
            from utils.csv_validator import validate_csv_files
            validation_result = validate_csv_files(storage_path, max_files=min(20, len(csv_files)))
            
            # Save metadata to MongoDB
            file_metadata = {
                "user_id": user_id,
                "filename": uploaded_file.name,
                "csv_count": len(csv_files),
                "csv_files": csv_names,
                "upload_date": datetime.now().isoformat(),
                "file_size": uploaded_file.size,
                "validation": {
                    "validated": validation_result.get("validated", 0),
                    "failed": validation_result.get("failed", 0),
                    "total": validation_result.get("total_files", 0)
                }
            }
            
            save_file_metadata(user_id, file_metadata)
            
            # Update session state
            st.session_state.health_data_loaded = True
            
            # Success message
            if validation_result.get("success"):
                st.success(f"✅ Uploaded successfully! {validation_result.get('validated', 0)} CSV file(s) validated and ready to query.")
            else:
                st.warning(f"⚠️ Uploaded but {validation_result.get('failed', 0)} file(s) had issues. Some files may not be queryable.")
            
            if validation_result.get("failed_files"):
                with st.expander("⚠️ Files with issues", expanded=False):
                    for failed_file in validation_result["failed_files"][:5]:
                        st.text(f"  • {failed_file['file']}: {failed_file.get('error', 'Unknown error')[:100]}")
            
            st.info("💡 Your real health data has been uploaded. You can now chat about your actual data!")
            
            # Display summary
            col1, col2 = st.columns(2)
            with col1:
                st.metric("CSV Files", len(csv_files))
            with col2:
                st.metric("File Size", f"{uploaded_file.size / 1024 / 1024:.2f} MB")
            
            # Show CSV files
            with st.expander("📋 View uploaded CSV files"):
                for csv_file in csv_files[:20]:  # Show first 20
                    st.text(f"  • {csv_file.name}")
                if len(csv_files) > 20:
                    st.text(f"  ... and {len(csv_files) - 20} more files")
            
            st.info("💡 You can now go to the **Chat** page to start asking questions about your health data!")
        
        except zipfile.BadZipFile:
            st.error("❌ Invalid ZIP file. Please make sure you uploaded a valid ZIP file.")
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.exception(e)

