import os
from SCons.Script import Import

Import("env")

def disable_component(env, component_name):
    try:
        platform = env.PioPlatform()
        package_dir = platform.get_package_dir("framework-espidf")
        
        if not package_dir:
            print(f"--- [ANTIGRAVITY] SKIP: framework-espidf not found. ---")
            return

        cmake_path = os.path.join(package_dir, "components", component_name, "CMakeLists.txt")
        
        if os.path.isfile(cmake_path):
            print(f"--- [ANTIGRAVITY] FOUND: {cmake_path} ---")
            dummy_content = 'idf_component_register()'
            
            with open(cmake_path, "r") as f:
                content = f.read()
            
            if content.strip() == dummy_content:
                print(f"--- [ANTIGRAVITY] {component_name} ALREADY PATCHED. ---")
            else:
                print(f"--- [ANTIGRAVITY] OVERWRITING {component_name} CMakeLists.txt... ---")
                with open(cmake_path, "w") as f:
                    f.write(dummy_content)
                print(f"--- [ANTIGRAVITY] SUCCESS: {component_name} disabled. ---")
        else:
            print(f"--- [ANTIGRAVITY] ERROR: File not found: {cmake_path} ---")

    except Exception as e:
        print(f"--- [ANTIGRAVITY] EXCEPTION: {e} ---")

def patch_spinlock(env):
    try:
        platform = env.PioPlatform()
        package_dir = platform.get_package_dir("framework-espidf")
        if not package_dir: return

        # Target file: components/esp_hw_support/include/soc/spinlock.h
        spinlock_path = os.path.join(package_dir, "components", "esp_hw_support", "include", "soc", "spinlock.h")
        
        if os.path.isfile(spinlock_path):
            print(f"--- [ANTIGRAVITY] FOUND: {spinlock_path} ---")
            with open(spinlock_path, "r") as f:
                content = f.read()
            
            import re
            
            # Aggressive patch using Regex to handle spacing and case
            # Target: RSR(PRID, ...) or RSR(prid, ...)
            # Replace with: RSR(0xEB, ...)
            
            pattern = r'RSR\s*\(\s*PRID\s*,'
            if re.search(pattern, content, re.IGNORECASE):
                print(f"--- [ANTIGRAVITY] FOUND 'RSR(PRID)' pattern (Regex). Patching to 0xEB... ---")
                new_content = re.sub(pattern, 'RSR(0xEB,', content, flags=re.IGNORECASE)
                
                with open(spinlock_path, "w") as f:
                    f.write(new_content)
                
                # VERIFICATION: Read back and check
                with open(spinlock_path, "r") as f:
                    final_content = f.read()
                
                if "RSR(0xEB," in final_content:
                     print("--- [ANTIGRAVITY] VERIFICATION SUCCESS: File on disk contains RSR(0xEB, ---")
                     # Print the line to be sure
                     lines = final_content.splitlines()
                     print(f"--- [ANTIGRAVITY] Line 83: {lines[82]}")
                else:
                     print("--- [ANTIGRAVITY] VERIFICATION FAILED: File on disk DOES NOT contain RSR(0xEB, ! ---")
            
            elif "RSR(0xEB," in content:
                 print(f"--- [ANTIGRAVITY] spinlock.h ALREADY PATCHED (numeric). ---")
                 # Verify anyway
                 lines = content.splitlines()
                 print(f"--- [ANTIGRAVITY] Line 83: {lines[82]}")
            else:
                 print(f"--- [ANTIGRAVITY] WARNING: 'RSR(PRID,' pattern not found via Regex. ---")
                 # Debug print again if missed
                 lines = content.splitlines()
                 print(f"Top 90 lines snippet:")
                 print(lines[82])

    except Exception as e:
        print(f"--- [ANTIGRAVITY] EXCEPTION: {e} ---")

disable_component(env, "app_trace")
disable_component(env, "esp_gdbstub")
patch_spinlock(env)
