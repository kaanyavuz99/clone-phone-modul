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
    # We will search the entire packages directory to be sure
    packages_dir = platform.get_package_dir("framework-espidf")
    if packages_dir:
        pass # packages_dir = os.path.dirname(packages_dir) # REMOVED: Do not scan entire packages dir!
    
    target_files = []
    
    if packages_dir:
         print(f"--- [ANTIGRAVITY] DEEP SCANNING PACKAGES DIR: {packages_dir} ---")
         for root, dirs, files in os.walk(packages_dir):
            if "spinlock.h" in files:
                full_path = os.path.join(root, "spinlock.h")
                if "soc" in root or "esp_hw_support" in root:
                     target_files.append(full_path)
            # FALLBACK: Search for backups if we are in "Already Renamed" state
            elif "spinlock.h.bak" in files:
                 full_path = os.path.join(root, "spinlock.h.bak")
                 if "soc" in root or "esp_hw_support" in root:
                     target_files.append(full_path)
                     print(f"--- [ANTIGRAVITY] FOUND BACKUP: {full_path} ---")
            # FALLBACK LEVEL 2: Recover from recursive rename mess
            elif "spinlock.h.bak.bak" in files:
                 full_path = os.path.join(root, "spinlock.h.bak.bak")
                 if "soc" in root or "esp_hw_support" in root:
                     target_files.append(full_path)
                     print(f"--- [ANTIGRAVITY] FOUND DEEP BACKUP: {full_path} ---")

    if not target_files:
        print("--- [ANTIGRAVITY] FATAL: No spinlock.h found anywhere. ---")
        return

    # Rename Strategy: Move them out of the way!
    asm_replacement = '    core_id = 0; // [ANTIGRAVITY] PATCHED TO BYPASS ASM ERROR'
    
    local_source_content = ""

    for source_path in target_files:
        try:
            # Read content first to save for our local override
            if not local_source_content:
                with open(source_path, "r") as f:
                    content = f.read()
                    
                # ALWAYS process line-by-line to ensure we catch it
                lines = content.splitlines()
                patched_lines = []
                for line in lines:
                    line_lower_val = line.lower()
                    if "rsr" in line_lower_val and ("prid" in line_lower_val or "0xeb" in line_lower_val):
                        print(f"--- [ANTIGRAVITY] MATCH FOUND! Patching line: {line.strip()} ---")
                        patched_lines.append(asm_replacement)
                    else:
                        # Optional: Print lines that look suspicious but failed match?
                        if "rsr" in line_lower_val:
                             print(f"--- [ANTIGRAVITY] IGNORED (No PRID/0xEB): {line.strip()} ---")
                        patched_lines.append(line)
                
                # PREPEND LINE SHIFT TEST
                patched_lines.insert(0, "// [ANTIGRAVITY] LINE SHIFT TEST - ERROR SHOULD BE AT LINE 84")
                
                local_source_content = "\n".join(patched_lines)
                print(f"--- [ANTIGRAVITY] Local Source Content Generated from: {source_path} ---")
                print("--- [ANTIGRAVITY] Local Source Content Generated (Size: %d bytes) ---" % len(local_source_content))
                
                # Verify content immediately
                print("--- [ANTIGRAVITY] VERIFICATION DUMP (Lines 80-90) ---")
                verification_lines = local_source_content.splitlines()[80:91]
                for v_line in verification_lines:
                    print(f"[VERIFY] {v_line}")
                print("--- [ANTIGRAVITY] END VERIFICATION DUMP ---")

            # NOW RENAME IT - BUT ONLY IF IT IS THE ORIGINAL
            # If it already ends in .bak or .bak.bak, leave it alone!
            if not source_path.endswith(".bak") and not source_path.endswith(".bak.bak"):
                backup_path = source_path + ".bak"
                if os.path.exists(source_path):
                    print(f"--- [ANTIGRAVITY] RENAMING (Hiding): {source_path} -> {backup_path} ---")
                    os.rename(source_path, backup_path)
            else:
                 print(f"--- [ANTIGRAVITY] Backup file preserved: {source_path} ---")

        except Exception as e:
            print(f"--- [ANTIGRAVITY] FAILED TO RENAME source_path: {e} ---")

    # Local Override Creation
    project_include = env.get("PROJECT_INCLUDE_DIR", os.path.join(env.get("PROJECT_DIR"), "include"))
    dest_dir = os.path.join(project_include, "soc")
    dest_path = os.path.join(dest_dir, "spinlock.h")
    
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    if local_source_content:
        with open(dest_path, "w") as f:
            f.write(local_source_content)
        print(f"--- [ANTIGRAVITY] Local override created at {dest_path} ---")
     
    # Ensure build flags prioritize this directory
    env.Prepend(CPPPATH=[project_include])
    print(f"--- [ANTIGRAVITY] Prepended {project_include} to CPPPATH ---")

# disable_component(env, "app_trace") # RE-ENABLED: Needed for esp_system
disable_component(env, "esp_gdbstub")

# Execute the Override Strategy
copy_and_patch_spinlock(env)
