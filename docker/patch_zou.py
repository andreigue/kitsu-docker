#!/usr/bin/env python3
"""
Patch script to add Telegram notification fields to Zou Person model
"""

import os
import sys
import glob

def find_zou_installation():
    """Find the Zou installation path"""
    
    # First try the direct source path since we kept it
    zou_src_path = "/opt/zou/zou-src"
    if os.path.exists(zou_src_path):
        person_model_path = os.path.join(zou_src_path, 'zou', 'app', 'models', 'person.py')
        if os.path.exists(person_model_path):
            print(f"Found Zou installation at: {zou_src_path}")
            return zou_src_path
    
    # Check if it's an editable installation by looking for .pth files
    print("Checking for editable installation...")
    pth_files = glob.glob("/opt/zou/env/lib/python3.10/site-packages/__editable__*.pth")
    for pth_file in pth_files:
        print(f"Found .pth file: {pth_file}")
        try:
            with open(pth_file, 'r') as f:
                content = f.read().strip()
                print(f"  .pth content: {content}")
                
                # For editable installations, try to find the finder module
                if "__editable__" in content and "finder" in content:
                    # Try common editable installation paths
                    editable_paths = [
                        "/opt/zou/zou-src",
                        "/opt/zou/zou-src/zou",
                        "/opt/zou"
                    ]
                    
                    for editable_path in editable_paths:
                        if os.path.exists(editable_path):
                            person_model_path = os.path.join(editable_path, 'zou', 'app', 'models', 'person.py')
                            if os.path.exists(person_model_path):
                                print(f"Found Zou installation at: {editable_path}")
                                return editable_path
                            # Also try without the zou subdirectory
                            person_model_path = os.path.join(editable_path, 'app', 'models', 'person.py')
                            if os.path.exists(person_model_path):
                                print(f"Found Zou installation at: {editable_path}")
                                return editable_path
                
                # Old logic for direct path in .pth files
                if os.path.exists(content):
                    # Check if this path contains the person model
                    person_model_path = os.path.join(content, 'app', 'models', 'person.py')
                    if os.path.exists(person_model_path):
                        print(f"Found Zou installation at: {content}")
                        return content
        except Exception as e:
            print(f"  Error reading .pth file: {e}")
    
    # Try multiple possible paths
    possible_paths = [
        "/opt/zou/env/lib/python3.10/site-packages/zou",
        "/opt/zou/env/lib/python3.10/site-packages/*/zou",
        "/opt/zou/env/lib/python3.10/site-packages/*/dist-packages/zou",
        "/opt/zou/env/lib/python3.10/site-packages/*/src/zou",
        "/opt/zou/env/lib/python3.10/site-packages/zou-*",
        "/opt/zou/env/lib/python3.10/site-packages/*/zou-*"
    ]
    
    for pattern in possible_paths:
        matches = glob.glob(pattern)
        for match in matches:
            person_model_path = os.path.join(match, 'app', 'models', 'person.py')
            if os.path.exists(person_model_path):
                print(f"Found Zou installation at: {match}")
                return match
    
    # If no matches found, try to find it by searching
    print("Searching for Zou installation...")
    search_paths = [
        "/opt/zou/env/lib/python3.10/site-packages",
        "/opt/zou/env/lib/python3.10/dist-packages"
    ]
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            print(f"Searching in: {search_path}")
            for root, dirs, files in os.walk(search_path):
                for dir_name in dirs:
                    if 'zou' in dir_name.lower():
                        zou_path = os.path.join(root, dir_name)
                        person_model_path = os.path.join(zou_path, 'app', 'models', 'person.py')
                        if os.path.exists(person_model_path):
                            print(f"Found Zou installation at: {zou_path}")
                            return zou_path
    
    # Debug: list all directories in site-packages
    print("Debug: Listing all directories in site-packages:")
    for search_path in search_paths:
        if os.path.exists(search_path):
            print(f"Contents of {search_path}:")
            try:
                for item in os.listdir(search_path):
                    item_path = os.path.join(search_path, item)
                    if os.path.isdir(item_path):
                        print(f"  DIR: {item}")
                    else:
                        print(f"  FILE: {item}")
            except Exception as e:
                print(f"  Error listing {search_path}: {e}")
    
    return None

def patch_person_model():
    """Add Telegram fields to the Person model"""
    
    try:
        # Find the zou installation
        zou_path = find_zou_installation()
        
        if not zou_path:
            print("ERROR: Could not find Zou installation")
            return False
        
        # Try different possible locations for person.py
        possible_person_paths = [
            os.path.join(zou_path, 'zou', 'app', 'models', 'person.py'),
            os.path.join(zou_path, 'app', 'models', 'person.py'),
            os.path.join(zou_path, 'src', 'zou', 'app', 'models', 'person.py')
        ]
        
        person_model_path = None
        for path in possible_person_paths:
            if os.path.exists(path):
                person_model_path = path
                break
        
        if not person_model_path:
            print(f"ERROR: Person model not found in any of these locations:")
            for path in possible_person_paths:
                print(f"  - {path}")
            
            # Debug: show what's actually in the zou path
            print(f"Contents of {zou_path}:")
            try:
                for item in os.listdir(zou_path):
                    item_path = os.path.join(zou_path, item)
                    if os.path.isdir(item_path):
                        print(f"  DIR: {item}")
                    else:
                        print(f"  FILE: {item}")
            except Exception as e:
                print(f"  Error listing {zou_path}: {e}")
            return False
        
        print(f"Patching Person model at: {person_model_path}")
        
        # Read the current file
        with open(person_model_path, 'r') as f:
            content = f.read()
        
        # Check if already patched
        if 'notifications_telegram_enabled' in content:
            print("Person model already patched with Telegram fields")
            return True
        
        # Find the line after notifications_discord_userid
        target_line = 'notifications_discord_userid = db.Column(db.String(60), default="")'
        
        if target_line not in content:
            print("ERROR: Could not find target line to patch")
            print("Available lines containing 'notifications_discord':")
            for i, line in enumerate(content.split('\n')):
                if 'notifications_discord' in line:
                    print(f"  Line {i+1}: {line.strip()}")
            return False
        
        # Add Telegram fields after the Discord fields
        telegram_fields = '''    notifications_telegram_enabled = db.Column(db.Boolean(), default=False)
    notifications_telegram_chat_id = db.Column(db.String(255), default="")'''
        
        # Insert the new fields
        new_content = content.replace(
            target_line,
            target_line + '\n' + telegram_fields
        )
        
        # Write the patched file
        with open(person_model_path, 'w') as f:
            f.write(new_content)
        
        print("✅ Successfully patched Person model with Telegram fields")
        return True
        
    except Exception as e:
        print(f"ERROR during patching: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = patch_person_model()
    if not success:
        sys.exit(1)
    print("Patch completed successfully") 