import math
import sys
import os
import subprocess
import tempfile
from datetime import datetime

def clean_json(obj):
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_json(i) for i in obj]
    return obj

def execute_visualization_code(code: str, df, output_dir: str = "visualizations"):
    """
    Safely execute visualization code and return the image path
    """

    replacements = {
        """: '"', """: '"',
        "'": "'", "'": "'",
        "–": "-", "—": "-",
        "•": "*", "…": "...",
    }
    for bad, good in replacements.items():
        code = code.replace(bad, good)

    # Fix backslashes in visualization code
    code = code.replace("\\", "/")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_filename = f"viz_{timestamp}.png"
    image_path = os.path.abspath(os.path.join(output_dir, image_filename))
    image_path = image_path.replace("\\", "/")
    
    # Create temporary Python file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        temp_script = f.name
        pickle_path = f"{temp_script}_data.pkl"
        pickle_path = pickle_path.replace("\\", "/")
    
    # Save dataframe to temporary pickle FIRST
    df.to_pickle(pickle_path)
    
    try:
        # Build the script in correct order
        script_parts = []
        
        # 1. Add matplotlib backend FIRST (before any matplotlib imports)
        script_parts.append("import matplotlib")
        script_parts.append("matplotlib.use('Agg')")
        
        # 2. Add required imports
        script_parts.append("import pandas as pd")
        script_parts.append("import matplotlib.pyplot as plt")
        script_parts.append("import numpy as np")
        
        # 3. Add data loading
        script_parts.append("")
        script_parts.append("# Load data")
        script_parts.append(f"df = pd.read_pickle('{pickle_path}')")
        script_parts.append("")
        
        # 4. Clean the generated code
        clean_code = code
        
        # Remove encoding declarations
        clean_code = clean_code.replace("# -*- coding: utf-8 -*-", "")
        clean_code = clean_code.replace("# coding: utf-8", "")
        
        # Remove import lines to avoid duplicates
        lines_to_remove = [
            "import matplotlib.pyplot as plt",
            "import pandas as pd",
            "import matplotlib",
            "matplotlib.use('Agg')",
            "matplotlib.use(\"Agg\")",
            "import numpy as np",
            "import numpy"
        ]
        
        code_lines = clean_code.split('\n')
        filtered_lines = []
        for line in code_lines:
            stripped = line.strip()
            should_skip = False
            
            # Skip empty lines at the beginning
            if not stripped and not filtered_lines:
                continue
                
            # Skip import lines
            for remove in lines_to_remove:
                if stripped.startswith(remove):
                    should_skip = True
                    break
            
            if not should_skip:
                filtered_lines.append(line)
        
        clean_code = '\n'.join(filtered_lines)
        
        # 5. Replace the save path in the code
        clean_code = clean_code.replace(
            "plt.savefig('visualization.png'",
            f"plt.savefig('{image_path}'"
        )
        
        # Handle different quote styles
        clean_code = clean_code.replace(
            'plt.savefig("visualization.png"',
            f'plt.savefig("{image_path}"'
        )
        
        # Also check for variations
        clean_code = clean_code.replace(
            "plt.savefig('visualization.png',",
            f"plt.savefig('{image_path}',"
        )
        clean_code = clean_code.replace(
            'plt.savefig("visualization.png",',
            f'plt.savefig("{image_path}",'
        )
        
        # 6. Add the cleaned code
        script_parts.append(clean_code)
        
        # Combine all parts
        final_script = '\n'.join(script_parts)
        
        # Write to file
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(final_script)
        
        print(f"📝 Executing script: {temp_script}")
        print(f"📊 Data file: {pickle_path}")
        print(f"🎨 Output image: {image_path}")
        print(f"🐍 Using Python: {sys.executable}")
        
        # Execute the script using the SAME Python executable as the main app
        result = subprocess.run(
            [sys.executable, temp_script],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(temp_script)  # Set working directory
        )
        
        if result.returncode != 0:
            print(f"❌ Script execution failed")
            print(f"stderr: {result.stderr}")
            print(f"stdout: {result.stdout}")
            # Print the script for debugging
            try:
                with open(temp_script, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                    print(f"📜 Generated script:\n{script_content}")
                    print(f"📏 Script length: {len(script_content)} chars")
            except Exception as read_error:
                print(f"Could not read script: {read_error}")
            raise Exception(f"Visualization execution failed: {result.stderr}")
        
        # Check if image was created
        if not os.path.exists(image_path):
            raise Exception("Visualization file was not created")
        
        print(f"✅ Visualization created: {image_path}")
        return image_path
    
    except subprocess.TimeoutExpired:
        raise Exception("Visualization execution timed out (30s limit)")
    
    except Exception as e:
        raise Exception(f"Error executing visualization: {str(e)}")
    
    finally:
        # Cleanup temporary files
        try:
            if os.path.exists(temp_script):
                os.unlink(temp_script)
            if os.path.exists(pickle_path):
                os.unlink(pickle_path)
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup warning: {cleanup_error}")