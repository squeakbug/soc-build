#!/usr/bin/env python3
"""
Build script for Polyphony demo apps targeting RISC-V/LiteX simulation.
"""

import os
import subprocess
import sys
import shutil

# Paths
POLY_ROOT = "/home/user/repos/cva6/soc-build/cores/polyphony"
DEMO_DIR = os.path.join(POLY_ROOT, "demo_app")
CLIB_DIR = os.path.join(POLY_ROOT, "clib")
BUILD_DIR = "/home/user/repos/cva6/soc-build/build/polyphony_demos"
TOOLCHAIN = "/home/user/synth/riscv/bin/riscv32-unknown-elf-"

# RISC-V compiler flags for bare metal
CFLAGS = [
    "-march=rv32imac",
    "-mabi=ilp32",
    "-O2",
    "-g",
    "-ffreestanding",
    "-nostdlib",
    "-I" + CLIB_DIR,
    "-I" + os.path.join(CLIB_DIR, "pplib"),
    "-I" + os.path.join(CLIB_DIR, "hw_dep", "litex"),
    "-I" + os.path.join(CLIB_DIR, "GL"),
    "-I" + os.path.join(CLIB_DIR, "GLES"),
    "-I" + os.path.join(CLIB_DIR, "KHR"),
    "-D__LITEX__",
    "-DRISCV",
]

LDFLAGS = [
    "-march=rv32imac",
    "-mabi=ilp32",
    "-nostdlib",
    "-Wl,--build-id=none",
    "-Wl,--gc-sections",
    "-T", os.path.join(BUILD_DIR, "linker.ld"),
]

# Source files
DEMO_APPS = [
    "app_anaglyph.c",
    "app_cook_torrance.c", 
    "app_earth.c",
    "app_moving_lights.c",
    "app_skinning.c",
]

# Common source files
COMMON_SOURCES = [
    os.path.join(CLIB_DIR, "pplib", "pplib.c"),
    os.path.join(CLIB_DIR, "pplib", "pplib_gl.c"),
    os.path.join(CLIB_DIR, "pplib", "pl_matrix3.c"),
    os.path.join(CLIB_DIR, "pplib", "pl_matrix4.c"),
    os.path.join(CLIB_DIR, "pplib", "pl_romtbl.c"),
    os.path.join(CLIB_DIR, "pplib", "pl_vector3.c"),
    os.path.join(CLIB_DIR, "pplib", "pl_vector4.c"),
    os.path.join(CLIB_DIR, "pplib", "pl_vertex3.c"),
    os.path.join(CLIB_DIR, "pplib", "pl_vertex4.c"),
    os.path.join(CLIB_DIR, "pplib", "pl_vu.c"),
    os.path.join(CLIB_DIR, "hw_dep", "litex", "hwdep.c"),
]

def run_cmd(cmd, cwd=None):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(result.stdout)
    return True

def create_build_dir():
    os.makedirs(BUILD_DIR, exist_ok=True)

def create_linker_script():
    linker_script = """
ENTRY(_start)

MEMORY
{
    rom (rx)  : ORIGIN = 0x00000000, LENGTH = 128K
    sram (rw) : ORIGIN = 0x10000000, LENGTH = 8K
    ram (rwx) : ORIGIN = 0x40000000, LENGTH = 64K
}

SECTIONS
{
    .text :
    {
        *(.text .text.*)
        *(.rodata .rodata.*)
    } > rom

    .data :
    {
        *(.data .data.*)
    } > ram AT > rom

    .bss :
    {
        *(.bss .bss.*)
        *(COMMON)
    } > ram

    .stack :
    {
        . = ALIGN(16);
        __stack_top = .;
        . += 4K;
    } > ram
}
"""
    with open(os.path.join(BUILD_DIR, "linker.ld"), "w") as f:
        f.write(linker_script)

def create_startup():
    """Create startup code."""
    startup = """
.section .text._start
.global _start
_start:
    /* Initialize stack pointer */
    la sp, __stack_top
    
    /* Call main */
    call main
    
    /* Infinite loop after main returns */
1:  wfi
    j 1b
"""
    with open(os.path.join(BUILD_DIR, "startup.s"), "w") as f:
        f.write(startup)

def compile_demo(demo_name):
    demo_src = os.path.join(DEMO_DIR, demo_name)
    demo_base = os.path.splitext(demo_name)[0]
    output_elf = os.path.join(BUILD_DIR, f"{demo_base}.elf")
    output_bin = os.path.join(BUILD_DIR, f"{demo_base}.bin")
    
    objects = []
    
    startup_obj = os.path.join(BUILD_DIR, "startup.o")
    if not run_cmd([TOOLCHAIN + "gcc", "-c"] + CFLAGS + ["-o", startup_obj, os.path.join(BUILD_DIR, "startup.s")]):
        return False
    objects.append(startup_obj)
    
    for src in COMMON_SOURCES:
        obj = os.path.join(BUILD_DIR, os.path.basename(src).replace(".c", ".o"))
        if not run_cmd([TOOLCHAIN + "gcc", "-c"] + CFLAGS + ["-o", obj, src]):
            return False
        objects.append(obj)
    
    demo_obj = os.path.join(BUILD_DIR, f"{demo_base}.o")
    if not run_cmd([TOOLCHAIN + "gcc", "-c"] + CFLAGS + ["-o", demo_obj, demo_src]):
        return False
    objects.append(demo_obj)
    
    link_cmd = [TOOLCHAIN + "gcc"] + LDFLAGS + ["-o", output_elf] + objects
    if not run_cmd(link_cmd):
        return False
    
    if not run_cmd([TOOLCHAIN + "objcopy", "-O", "binary", output_elf, output_bin]):
        return False
    
    print(f"Built {demo_name} -> {output_elf}, {output_bin}")
    return True


def main():
    create_build_dir()
    create_linker_script()
    create_startup()
    
    print("Building Polyphony demo apps for RISC-V...")
    
    for demo in DEMO_APPS:
        if not compile_demo(demo):
            print(f"Failed to build {demo}")
            sys.exit(1)
    
    print("All demos built successfully!")
    print(f"Output in: {BUILD_DIR}")

if __name__ == "__main__":
    main()
