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


def copy_and_patch_spinlock(env):
    """
    Finds the framework spinlock.h, patches it, and saves it to local include/soc/spinlock.h
    to override the framework version.
    """
    platform = env.PioPlatform()
    
    # Locate source file
    package_dir = platform.get_package_dir("framework-espidf")
    if not package_dir:
        print("--- [ANTIGRAVITY] ERROR: framework-espidf not found! ---")
        return

    # Typical path: components/esp_hw_support/include/soc/spinlock.h
    source_path = os.path.join(package_dir, "components", "esp_hw_support", "include", "soc", "spinlock.h")
    
    if not os.path.exists(source_path):
         print(f"--- [ANTIGRAVITY] ERROR: Source spinlock.h not found at {source_path} ---")
         # Fallback search
         for root, dirs, files in os.walk(package_dir):
            if "spinlock.h" in files and "soc" in root:
                source_path = os.path.join(root, "spinlock.h")
                break
    
    if not os.path.exists(source_path):
        print("--- [ANTIGRAVITY] FATAL: Could not find spinlock.h anywhere. ---")
        return

    print(f"--- [ANTIGRAVITY] Found source spinlock.h at {source_path} ---")

    # Define destination: {project}/include/soc/spinlock.h
    project_include = env.get("PROJECT_INCLUDE_DIR", os.path.join(env.get("PROJECT_DIR"), "include"))
    dest_dir = os.path.join(project_include, "soc")
    dest_path = os.path.join(dest_dir, "spinlock.h")
    
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        
    # Read source
    with open(source_path, "r") as f:
        content = f.read()
        
    # Apply ASM Patch
    asm_replacement = '__asm__ __volatile__("rsr %0, 235" : "=r"(core_id));'
    
    patched_content = content
    # Replace RSR(PRID, ...)
    patched_content = re.sub(r'RSR\s*\(\s*PRID\s*,\s*core_id\s*\)\s*;', asm_replacement, patched_content, flags=re.IGNORECASE)
    # Replace RSR(0xEB, ...) just in case
    patched_content = re.sub(r'RSR\s*\(\s*0xEB\s*,\s*core_id\s*\)\s*;', asm_replacement, patched_content, flags=re.IGNORECASE)
    
    # Write to local include
    with open(dest_path, "w") as f:
        f.write(patched_content)
        
    print(f"--- [ANTIGRAVITY] CREATED LOCAL OVERRIDE: {dest_path} ---")
    
    # Ensure build flags prioritize this directory
    # PlatformIO adds include/ by default, but verify
    env.Append(CPPPATH=[project_include])
    print(f"--- [ANTIGRAVITY] Added {project_include} to CPPPATH ---")

disable_component(env, "app_trace")
disable_component(env, "esp_gdbstub")

# Execute the Override Strategy
copy_and_patch_spinlock(env)
