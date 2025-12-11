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

def patch_spinlock_in_dir(package_dir):
    if not package_dir: return

    for root, dirs, files in os.walk(package_dir):
        if "spinlock.h" in files:
            spinlock_path = os.path.join(root, "spinlock.h")
            # Only target the specific soc/spinlock.h file to avoid patching unrelated files
            if "soc" not in spinlock_path and "include" not in spinlock_path:
                 continue
            
            print(f"--- [ANTIGRAVITY] CHECKING: {spinlock_path} ---")
            
            try:
                with open(spinlock_path, "r") as f:
                    content = f.read()
                
                import re
                pattern = r'RSR\s*\(\s*PRID\s*,'
                
                if re.search(pattern, content, re.IGNORECASE):
                    print(f"--- [ANTIGRAVITY] FOUND 'RSR(PRID)' in {spinlock_path}. Patching to 0xEB... ---")
                    # Force all occurrences
                    new_content = re.sub(pattern, 'RSR(0xEB,', content, flags=re.IGNORECASE)
                    with open(spinlock_path, "w") as f:
                        f.write(new_content)
                    print(f"--- [ANTIGRAVITY] SUCCESS: {spinlock_path} patched. ---")
                
                # Double check verification for logging
                if "RSR(0xEB," in content:
                     print(f"--- [ANTIGRAVITY] INFO: {spinlock_path} contains patched RSR(0xEB). ---")

            except Exception as e:
                print(f"--- [ANTIGRAVITY] EXCEPTION processing {spinlock_path}: {e} ---")

def patch_spinlock(env):
    platform = env.PioPlatform()
    
    # Patch in framework-espidf
    patch_spinlock_in_dir(platform.get_package_dir("framework-espidf"))
    
    # Patch in framework-arduinoespressif32
    patch_spinlock_in_dir(platform.get_package_dir("framework-arduinoespressif32"))

disable_component(env, "app_trace")
disable_component(env, "esp_gdbstub")
patch_spinlock(env)
