import os
from SCons.Script import Import

Import("env")

def disable_app_trace():
    print("--- [ANTIGRAVITY] STARTING PATCH: DISABLE APP_TRACE ---")
    try:
        platform = env.PioPlatform()
        # Locate the framework-espidf package
        package_dir = platform.get_package_dir("framework-espidf")
        
        if not package_dir:
            print("--- [ANTIGRAVITY] SKIP: framework-espidf not found. ---")
            return

        # Path to app_trace component CMakeLists.txt
        # Adjust path structure if needed (components/app_trace or components/esp32/app_trace?)
        # Standard IDF 4.4 structure: components/app_trace/CMakeLists.txt
        cmake_path = os.path.join(package_dir, "components", "app_trace", "CMakeLists.txt")
        
        if os.path.isfile(cmake_path):
            print(f"--- [ANTIGRAVITY] FOUND: {cmake_path} ---")
            
            # Content to effectively disable the component build
            # We register it as a component but with NO sources.
            dummy_content = 'idf_component_register()'
            
            # Read first to check if already patched (optional, but good for idempotency)
            with open(cmake_path, "r") as f:
                content = f.read()
            
            if content.strip() == dummy_content:
                print("--- [ANTIGRAVITY] ALREADY PATCHED. ---")
            else:
                print("--- [ANTIGRAVITY] OVERWRITING CMakeLists.txt... ---")
                with open(cmake_path, "w") as f:
                    f.write(dummy_content)
                print("--- [ANTIGRAVITY] SUCCESS: app_trace disabled. ---")
        else:
            print(f"--- [ANTIGRAVITY] ERROR: File not found: {cmake_path} ---")

    except Exception as e:
        print(f"--- [ANTIGRAVITY] EXCEPTION: {e} ---")

disable_app_trace()
