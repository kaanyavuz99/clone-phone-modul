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

disable_component(env, "app_trace")
disable_component(env, "esp_gdbstub")
