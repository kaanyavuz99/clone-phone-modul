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
            
            # Debug: Print lines 80-90 to see exactly what is there
            lines = content.splitlines()
            print("--- [ANTIGRAVITY] DEBUG: spinlock.h content around line 83: ---")
            for i in range(max(0, 75), min(len(lines), 90)):
                 print(f"{i+1}: {lines[i]}")
            
            # Patch attempts with regex to be safer?
            # Let's try to match case-insensitive or partial
            if "rsr.PRID" in content:
                print(f"--- [ANTIGRAVITY] PATCHING 'rsr.PRID' to 'rsr.prid'... ---")
                new_content = content.replace("rsr.PRID", "rsr.prid")
                with open(spinlock_path, "w") as f:
                    f.write(new_content)
            elif "RSR.PRID" in content:
                print(f"--- [ANTIGRAVITY] PATCHING 'RSR.PRID' to 'rsr.prid'... ---")
                new_content = content.replace("RSR.PRID", "rsr.prid")
                with open(spinlock_path, "w") as f:
                    f.write(new_content)
            else:
                 print(f"--- [ANTIGRAVITY] WARNING: Exact 'rsr.PRID' string not found. See debug output above. ---")

    except Exception as e:
        print(f"--- [ANTIGRAVITY] EXCEPTION: {e} ---")

disable_component(env, "app_trace")
disable_component(env, "esp_gdbstub")
patch_spinlock(env)
