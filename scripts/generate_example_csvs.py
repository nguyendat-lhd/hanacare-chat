"""
Script to generate example CSV files for upload
Creates steps.csv, heart_rate.csv, sleep.csv, workouts.csv in a folder
These can be zipped and uploaded as example data
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "streamlit"))

from utils.sample_data import generate_sample_data

def main():
    """Generate example CSV files in examples/ folder"""
    # Create examples directory
    examples_dir = project_root / "examples"
    examples_dir.mkdir(exist_ok=True)
    
    print("🎲 Generating example CSV files...")
    print(f"📁 Output directory: {examples_dir}")
    
    # Generate sample data
    result = generate_sample_data("example_user", examples_dir)
    
    print("\n✅ Generated example CSV files:")
    print(f"  • steps.csv: {result.get('steps', 0)} records")
    print(f"  • heart_rate.csv: {result.get('heart_rate', 0)} records")
    print(f"  • sleep.csv: {result.get('sleep', 0)} records")
    print(f"  • workouts.csv: {result.get('workouts', 0)} records")
    print(f"\n💡 You can now:")
    print(f"  1. Zip these files: cd {examples_dir} && zip example_health_data.zip *.csv")
    print(f"  2. Upload the ZIP file in the Upload page")
    print(f"  3. Or use these CSV files directly for testing")

if __name__ == "__main__":
    main()

