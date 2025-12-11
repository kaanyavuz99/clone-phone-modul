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
    
    # Read source
    with open(source_path, "r") as f:
        content = f.read()
        
    # Apply Patch by iterating lines
    lines = content.splitlines()
    patched_lines = []
    
    asm_replacement = '    __asm__ __volatile__("rsr %0, 235" : "=r"(core_id));'
    
    needs_patching = False
    
    print(f"--- [ANTIGRAVITY] SCANNING {len(lines)} lines in spinlock.h ---")
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if "rsr" in line_lower and ("prid" in line_lower or "0xeb" in line_lower):
            print(f"--- [ANTIGRAVITY] PATCHING Line {i+1}: {line.strip()} ---")
            patched_lines.append(asm_replacement)
            needs_patching = True
        else:
            patched_lines.append(line)
            
    patched_content = "\n".join(patched_lines)

    # STRATEGY CHANGE: DIRECT OVERWRITE
    # We overwrite the framework file itself to ensure compiler picks it up.
    if needs_patching:
        print(f"--- [ANTIGRAVITY] OVERWRITING FRAMEWORK FILE: {source_path} ---")
        try:
            with open(source_path, "w") as f:
                f.write(patched_content)
            print("--- [ANTIGRAVITY] OVERWRITE SUCCESSFUL ---")
        except Exception as e:
            print(f"--- [ANTIGRAVITY] ERROR OVERWRITING FRAMEWORK FILE: {e} ---")
    else:
        print("--- [ANTIGRAVITY] Framework file appears already patched or didn't match. ---")

    # FINAL VERIFICATION: Read back the FRAMEWORK file
    print(f"--- [ANTIGRAVITY] VERIFYING CONTENT OF: {source_path} ---")
    with open(source_path, "r") as f:
        final_lines = f.readlines()
        for i, line in enumerate(final_lines):
            if "rsr" in line.lower() and "prid" in line.lower():
                 print(f"CRITICAL ERROR: Line {i+1} still contains PRID: {line.strip()}")
            if "rsr" in line.lower() and "235" in line:
                 print(f"SUCCESS: Line {i+1} matches ASM: {line.strip()}")
    
    # Keep local override logic just in case (Belt and Suspenders)
    # Define destination: {project}/include/soc/spinlock.h
    project_include = env.get("PROJECT_INCLUDE_DIR", os.path.join(env.get("PROJECT_DIR"), "include"))
    dest_dir = os.path.join(project_include, "soc")
    dest_path = os.path.join(dest_dir, "spinlock.h")
    
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    with open(dest_path, "w") as f:
        f.write(patched_content)

    # Ensure build flags prioritize this directory
    env.Prepend(CPPPATH=[project_include])
    print(f"--- [ANTIGRAVITY] Prepended {project_include} to CPPPATH (Priority Override) ---")

disable_component(env, "app_trace")
disable_component(env, "esp_gdbstub")

# Execute the Override Strategy
copy_and_patch_spinlock(env)
