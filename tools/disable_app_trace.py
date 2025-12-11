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
            
            try:
                with open(spinlock_path, "r") as f:
                    content = f.read()
                
                import re
                pattern = r'RSR\s*\(\s*PRID\s*,'
                
                # DEBUG: Print file content to understand the Macro definition
                lines = content.splitlines()
                print(f"--- [ANTIGRAVITY] FILE HEAD ({spinlock_path}): ---")
                for i in range(min(50, len(lines))):
                     print(f"{i+1}: {lines[i]}")
                
                print(f"--- [ANTIGRAVITY] CONTEXT AROUND LINE 83: ---")
                if len(lines) > 85:
                    for i in range(80, 86):
                        print(f"{i+1}: {lines[i]}")
                
                # Define the detailed ASM replacement
                asm_replacement = '__asm__ __volatile__("rsr %0, 235" : "=r"(core_id));'
                
                # Check for original RSR(PRID...)
                if re.search(pattern, content, re.IGNORECASE):
                    print(f"--- [ANTIGRAVITY] FOUND 'RSR(PRID)' in {spinlock_path}. Patching to ASM... ---")
                    new_content = re.sub(r'RSR\s*\(\s*PRID\s*,\s*core_id\s*\)\s*;', asm_replacement, content, flags=re.IGNORECASE)
                    with open(spinlock_path, "w") as f:
                        f.write(new_content)
                    print(f"--- [ANTIGRAVITY] SUCCESS: {spinlock_path} patched with ASM (from PRID). ---")
                    # Update content for next check
                    content = new_content

                # Check for previously failed patch RSR(0xEB...)
                pattern_0xeb = r'RSR\s*\(\s*0xEB\s*,\s*core_id\s*\)\s*;'
                if re.search(pattern_0xeb, content, re.IGNORECASE):
                    print(f"--- [ANTIGRAVITY] FOUND 'RSR(0xEB)' in {spinlock_path}. upgrading to ASM... ---")
                    new_content = re.sub(pattern_0xeb, asm_replacement, content, flags=re.IGNORECASE)
                    with open(spinlock_path, "w") as f:
                        f.write(new_content)
                    print(f"--- [ANTIGRAVITY] SUCCESS: {spinlock_path} patched with ASM (from 0xEB). ---")
                
                if 'rsr %0, 235' in content:
                     print(f"--- [ANTIGRAVITY] ALREADY PATCHED WITH ASM: {spinlock_path} ---")

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
