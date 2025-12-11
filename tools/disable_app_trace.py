import os
from SCons.Script import Import
import re
import sys

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
    package_dir_idf = platform.get_package_dir("framework-espidf")
    package_dir_arduino = platform.get_package_dir("framework-arduinoespressif32")
    
    source_path = None
    
    # Priority: Check Arduino first as it might be the rogue one
    if package_dir_arduino:
         print(f"--- [ANTIGRAVITY] Checking Arduino Framework at {package_dir_arduino} ---")
         # We specifically want the ESP32 (not s2, s3, c3) version.
         # Path usually: tools/sdk/esp32/include/esp_hw_support/include/soc/spinlock.h
         expected_path = os.path.join(package_dir_arduino, "tools", "sdk", "esp32", "include", "esp_hw_support", "include", "soc", "spinlock.h")
         
         if os.path.exists(expected_path):
             source_path = expected_path
             print(f"--- [ANTIGRAVITY] Found CORRECT ARDUINO ESP32 spinlock.h at {source_path} ---")
         else:
             # Fallback explicit search
             for root, dirs, files in os.walk(package_dir_arduino):
                if "spinlock.h" in files and "soc" in root and "/esp32/" in root.replace("\\", "/"):
                    source_path = os.path.join(root, "spinlock.h")
                    print(f"--- [ANTIGRAVITY] Found ARDUINO spinlock.h (Walk) at {source_path} ---")
                    break
                
    if not source_path and package_dir_idf:
        # Fallback to IDF
        source_path = os.path.join(package_dir_idf, "components", "esp_hw_support", "include", "soc", "spinlock.h")
        if not os.path.exists(source_path):
             for root, dirs, files in os.walk(package_dir_idf):
                if "spinlock.h" in files and "soc" in root:
                    source_path = os.path.join(root, "spinlock.h")
                    break

    if not source_path or not os.path.exists(source_path):
        print("--- [ANTIGRAVITY] FATAL: Could not find spinlock.h anywhere. ---")
        return

    print(f"--- [ANTIGRAVITY] Using source spinlock.h at {source_path} ---")
    
    # Debug CPPPATH
    print("--- [ANTIGRAVITY] Current CPPPATH: ---")
    for p in env.get("CPPPATH", []):
        print(f"  - {p}")

    # Define destination: {project}/include/soc/spinlock.h
    project_include = env.get("PROJECT_INCLUDE_DIR", os.path.join(env.get("PROJECT_DIR"), "include"))
    dest_dir = os.path.join(project_include, "soc")
    dest_path = os.path.join(dest_dir, "spinlock.h")
    
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        
    # Read source
    with open(source_path, "r") as f:
        content = f.read()
        
    # Apply Patch by iterating lines to avoid regex pitfalls
    lines = content.splitlines()
    patched_lines = []
    
    # TRACER REMOVED
    # patched_lines.append('#error "ANTIGRAVITY_ACCESS_CONFIRMED: I CAN WRITE THIS FILE"')
    
    asm_replacement = '    __asm__ __volatile__("rsr %0, 235" : "=r"(core_id));'
    
    print(f"--- [ANTIGRAVITY] SCANNING {len(lines)} lines in spinlock.h ---")
    
    for i, line in enumerate(lines):
        # Case insensitive check
        line_lower = line.lower()
        if "rsr" in line_lower and ("prid" in line_lower or "0xeb" in line_lower):
            print(f"--- [ANTIGRAVITY] PATCHING Line {i+1}: {line.strip()} ---")
            patched_lines.append(asm_replacement)
        else:
            # Debug: Print potential misses
            if "rsr" in line_lower or "prid" in line_lower:
                 print(f"--- [ANTIGRAVITY] SKIPPING Line {i+1} (No match): {line.strip()} ---")
            patched_lines.append(line)
            
    patched_content = "\n".join(patched_lines)
    
    # Write to local include
    with open(dest_path, "w") as f:
        f.write(patched_content)
        
    print(f"--- [ANTIGRAVITY] CREATED LOCAL OVERRIDE: {dest_path} ---")
    
    # Ensure build flags prioritize this directory
    # CRITICAL: Use Prepend to force this directory to be searched BEFORE frameowrk includes
    env.Prepend(CPPPATH=[project_include])
    print(f"--- [ANTIGRAVITY] Prepended {project_include} to CPPPATH (Priority Override) ---")
    
    # FINAL VERIFICATION: Read back what we wrote
    print(f"--- [ANTIGRAVITY] VERIFYING CONTENT OF: {dest_path} ---")
    with open(dest_path, "r") as f:
        final_lines = f.readlines()
        for i, line in enumerate(final_lines):
            if "rsr" in line.lower() and "prid" in line.lower():
                 print(f"CRITICAL ERROR: Line {i+1} still contains PRID: {line.strip()}")
            if "rsr" in line.lower() and "235" in line:
                 print(f"SUCCESS: Line {i+1} matches ASM: {line.strip()}")

disable_component(env, "app_trace")
disable_component(env, "esp_gdbstub")

# Execute the Override Strategy
copy_and_patch_spinlock(env)
