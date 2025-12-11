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
    # Locate source file
    package_dir_idf = platform.get_package_dir("framework-espidf")
    package_dir_arduino = platform.get_package_dir("framework-arduinoespressif32")
    
    target_files = []
    
    # SEARCH EVERYWHERE. NUCLEAR OPTION.
    
    if package_dir_arduino:
         print(f"--- [ANTIGRAVITY] SCANNING ARDUINO FRAMEWORK: {package_dir_arduino} ---")
         for root, dirs, files in os.walk(package_dir_arduino):
            if "spinlock.h" in files:
                full_path = os.path.join(root, "spinlock.h")
                # Filter for useful paths to avoid patching unrelated stuff if any
                if "soc" in root or "esp_hw_support" in root:
                    target_files.append(full_path)
                    print(f"--- [ANTIGRAVITY] TARGET ACQUIRED: {full_path} ---")

    if package_dir_idf:
        print(f"--- [ANTIGRAVITY] SCANNING IDF FRAMEWORK: {package_dir_idf} ---")
        for root, dirs, files in os.walk(package_dir_idf):
            if "spinlock.h" in files:
                full_path = os.path.join(root, "spinlock.h")
                if "soc" in root or "esp_hw_support" in root:
                    target_files.append(full_path)
                    print(f"--- [ANTIGRAVITY] TARGET ACQUIRED: {full_path} ---")
    
    if not target_files:
        print("--- [ANTIGRAVITY] FATAL: CAUSE LOST. No spinlock.h found anywhere. ---")
        return

    # PATCH THEM ALL
    asm_replacement = '    __asm__ __volatile__("rsr %0, 235" : "=r"(core_id));'
    
    for source_path in target_files:
        print(f"--- [ANTIGRAVITY] PROCESSING: {source_path} ---")
        try:
            with open(source_path, "r") as f:
                content = f.read()
                
            lines = content.splitlines()
            patched_lines = []
            needs_patching = False
            
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if "rsr" in line_lower and ("prid" in line_lower or "0xeb" in line_lower):
                    # print(f"--- [ANTIGRAVITY] PATCHING Line {i+1} in {os.path.basename(source_path)} ---") # Reduce noise
                    patched_lines.append(asm_replacement)
                    needs_patching = True
                else:
                    patched_lines.append(line)
            
            if needs_patching:
                patched_content = "\n".join(patched_lines)
                with open(source_path, "w") as f:
                    f.write(patched_content)
                print(f"--- [ANTIGRAVITY] NUCLEAR STRIKE CONFIRMED: Patched {source_path} ---")
            else:
                 print(f"--- [ANTIGRAVITY] File already clean: {source_path} ---")

        except Exception as e:
            print(f"--- [ANTIGRAVITY] FAILED TO PATCH {source_path}: {e} ---")

    # Override logic: Just copy the first valid one we found/patched to local include for good measure
    if target_files:
         last_path = target_files[0]
         # ... copy logic ...
         with open(last_path, "r") as f:
             content = f.read() # Read the (now patched) content
         
         project_include = env.get("PROJECT_INCLUDE_DIR", os.path.join(env.get("PROJECT_DIR"), "include"))
         dest_dir = os.path.join(project_include, "soc")
         dest_path = os.path.join(dest_dir, "spinlock.h")
         
         if not os.path.exists(dest_dir):
             os.makedirs(dest_dir)
         
         with open(dest_path, "w") as f:
             f.write(content)
         print(f"--- [ANTIGRAVITY] Local override updated from {last_path} ---")

    # Ensure build flags prioritize this directory
    env.Prepend(CPPPATH=[project_include])
    print(f"--- [ANTIGRAVITY] Prepended {project_include} to CPPPATH (Priority Override) ---")

disable_component(env, "app_trace")
disable_component(env, "esp_gdbstub")

# Execute the Override Strategy
copy_and_patch_spinlock(env)
