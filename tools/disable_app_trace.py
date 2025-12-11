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
            # ULTRA-AGGRESSIVE: Patch EVERY spinlock.h found, no path validation.
            # if "soc" not in spinlock_path and "include" not in spinlock_path:
            #      continue
            
            print(f"--- [ANTIGRAVITY] CHECKING: {spinlock_path} ---")
            
            # Check for symlinks
            if os.path.islink(spinlock_path):
                real_path = os.path.realpath(spinlock_path)
                print(f"--- [ANTIGRAVITY] DETECTED SYMLINK: {spinlock_path} -> {real_path} ---")
                spinlock_path = real_path
            else:
                print(f"--- [ANTIGRAVITY] REALPATH: {os.path.realpath(spinlock_path)} ---")
            
            try:
                with open(spinlock_path, "r") as f:
                    content = f.read()
                
                import re
                pattern = r'RSR\s*\(\s*PRID\s*,'
                
                # FORCE CLEAN BUILD once to clear artifacts
                # if not os.path.exists("flag_clean_done"):
                #    print("--- [ANTIGRAVITY] FORCING CLEAN BUILD... ---")
                #    env.Execute("rm -rf .pio/build")
                #    with open("flag_clean_done", "w") as f: f.write("done")

                # Prepare the correct content
                # 1. Replace RSR(PRID...)
                # 2. Replace RSR(0xEB...)
                # 3. Use ASM
                
                asm_replacement = '__asm__ __volatile__("rsr %0, 235" : "=r"(core_id));'
                new_content = content
                
                if re.search(r'RSR\s*\(\s*PRID\s*,\s*core_id\s*\)\s*;', new_content, re.IGNORECASE):
                     new_content = re.sub(r'RSR\s*\(\s*PRID\s*,\s*core_id\s*\)\s*;', asm_replacement, new_content, flags=re.IGNORECASE)
                
                if re.search(r'RSR\s*\(\s*0xEB\s*,\s*core_id\s*\)\s*;', new_content, re.IGNORECASE):
                     new_content = re.sub(r'RSR\s*\(\s*0xEB\s*,\s*core_id\s*\)\s*;', asm_replacement, new_content, flags=re.IGNORECASE)
                
                if new_content != content:
                    print(f"--- [ANTIGRAVITY] PATCHING {spinlock_path} (Atomir Rewrite)... ---")
                    
                    # ATOMIC REWRITE: Delete then Write to break caching/links
                    try:
                        os.remove(spinlock_path)
                        print(f"--- [ANTIGRAVITY] DELETED original file. ---")
                    except Exception as ex:
                        print(f"--- [ANTIGRAVITY] WARNING: Could not delete file: {ex} ---")

                    with open(spinlock_path, "w") as f:
                        f.write(new_content)
                    print(f"--- [ANTIGRAVITY] WROTE new content. ---")
                    
                    # Verify
                    with open(spinlock_path, "r") as f:
                        check = f.read()
                    if asm_replacement in check:
                         print(f"--- [ANTIGRAVITY] VERIFIED: File contains ASM on disk. ---")
                    else:
                         print(f"--- [ANTIGRAVITY] ERROR: WRITE FAILED TO PERSIST! ---")

                elif asm_replacement in content:
                     print(f"--- [ANTIGRAVITY] ALREADY PATCHED (Verified ASM): {spinlock_path} ---") 
                else:
                     print(f"--- [ANTIGRAVITY] NO MATCH FOUND in {spinlock_path} ---")

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
