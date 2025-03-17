#!/usr/bin/env bash

set -e
#set -x

SCRIPTNAME=$0
CMDNAME=$1

NUM_THREADS=$(nproc --ignore 1)
total_mem=$(grep MemTotal < /proc/meminfo | awk '{print $2}')
total_mem_gb=$((total_mem / 1024 / 1024))

ROOT=$( [ "${EUID:=$(id -u)}" == 0 ] && echo true || echo false);
if [ "$ROOT" == true ]; then
    export SYNTH="/opt/synth"
else
    export SYNTH="$HOME/synth"
fi

_check_system_req()
{
    echo "Running as root: $ROOT"
    echo "Installation path: $SYNTH"
    echo "Number of cores: $(nproc)"
    echo "Total memory: $total_mem_gb GB"
    if ((total_mem < 8400000 )) ; then
        NUM_THREADS=1
        echo -e "Detected less than or equal to 8 GB of memory. Using a single thread for compiling tools. This may take a while."
    fi
    echo "Using $NUM_THREADS thread(s) for compilation"
}

env()
{
    local command="$1"

    case "${command}" in
    create)
        mkdir -p ${SYNTH}
        if [[ -e ${SYNTH}/venv ]]; then
            echo "${SYNTH}/venv already exists";
        else
            python3 -m venv ${SYNTH}/venv;
        fi
        echo -e "Activate with command:\nsource ${SYNTH}/venv/bin/activate"
        ;;
    activate)
        echo -e "Activate with command:\nsource ${SYNTH}/venv/bin/activate"
        ;;
    remove)
        rm -rf ${SYNTH}/${venvname}
        ;;
    *)
        echo "No command ${command}"
        usage
        ;;
    esac
}

_check_venv()
{
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo "Virtual environment is active: $VIRTUAL_ENV"
    else
        echo "No virtual environment active."
        echo -e "Activate with command:\nsource ${SYNTH}/venv/bin/activate"
        exit 2
    fi
}

init_tool()
{
    local toolname="$1"

    _check_system_req

    export CROSS_COMPILE=riscv32-unknown-linux-gnu-
    export ARCH=riscv
    export PLATFORM=generic

    case "${toolname}" in
    litex)
        _check_venv
        mkdir -p ${SYNTH}/litex
        pushd ${SYNTH}/litex
        wget https://raw.githubusercontent.com/enjoy-digital/litex/master/litex_setup.py
        chmod +x litex_setup.py
        ./litex_setup.py --init --install --config=full
        ./litex_setup.py --update
        pip3 install meson ninja
        popd
        ;;
    fusesoc)
        _check_venv
        pip3 install --upgrade fusesoc
        ;;
    yosys)
        pushd ${SYNTH}
        wget https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-04-02/oss-cad-suite-linux-x64-20260402.tgz
        tar -xzf oss-cad-suite-linux-x64-20260402.tgz
        popd
        ;;
    gtkwave)
        apt install gtkwave
        ;;
    verilator)
        apt install libevent-dev libjson-c-dev verilator
        ;;
    renode)
        ;;
    qemu)
        _check_system_req
        pushd ${SYNTH}
        if [[ ! -e qemu ]]; then
            git clone https://gitlab.com/qemu-project/qemu.git
        fi
        cd qemu
        git checkout stable-9.0
        mkdir -p build && cd build
        ../configure \
            --prefix=${SYNTH} \
            --extra-cflags=-fPIC \
            --target-list=arm-softmmu,aarch64-softmmu,riscv32-softmmu,riscv64-softmmu
        make -j ${NUM_THREADS}
        popd
        ;;
    opensbi)
        _check_system_req
        pushd ${SYNTH}
        if [[ ! -e opensbi ]]; then
            git clone https://github.com/riscv-software-src/opensbi
        fi
        cd opensbi
        make -j ${NUM_THREADS}
        ;;
    barebox)
        _check_system_req
        pushd ${SYNTH}
        if [[ ! -e barebox ]]; then
            git clone https://github.com/barebox/barebox
        fi
        cd barebox
        make virt32_defconfig
        make -j ${NUM_THREADS}
        ;;
    zephyr)
        _check_system_req
        _check_venv
        pushd ${SYNTH}
        pip install west

        if [[ ! -e zephyrproject ]]; then
            west init zephyrproject && cd zephyrproject
            west update
            west zephyr-export
            west packages pip --install
            cd -
        fi
        cd zephyrproject

        cd zephyr
        west sdk install -t riscv64-zephyr-elf
        west build --pristine -b qemu_riscv32 samples/synchronization
        ;;
     riot)
        ;;
    nuttx)
        ;;
    linux)
        _check_system_req
        pushd ${SYNTH}
        if [[ ! -e linux ]]; then
            git clone git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git
        fi
        ;;
    buildroot)
        git clone https://gitlab.com/buildroot.org/buildroot/ ${SYNTH}/buidroot
        ;;
    yocto)
        pushd ${SYNTH}
        mkdir -p yocto
        cd yocto
        git clone https://git.openembedded.org/bitbake
        ./bitbake/bin/bitbake-setup init
        popd
        ;;
    openocd)
        apt install openocd
        ;;
    riscv32)
        pushd ${SYNTH}
        wget https://github.com/riscv-collab/riscv-gnu-toolchain/releases/download/2026.07.15/riscv32-elf-ubuntu-22.04-gcc.tar.xz
        tar -xvf riscv32-elf-ubuntu-22.04-gcc.tar.xz
        popd
        ;;
    riscv32-linux)
        pushd ${SYNTH}
        wget https://github.com/riscv-collab/riscv-gnu-toolchain/releases/download/2026.07.15/riscv32-glibc-ubuntu-22.04-gcc.tar.xz
        tar -xvf riscv32-glibc-ubuntu-22.04-gcc.tar.xz
        popd
        ;;
    riscv64)
        pushd ${SYNTH}
        wget https://github.com/riscv-collab/riscv-gnu-toolchain/releases/download/2026.07.15/riscv64-elf-ubuntu-22.04-gcc.tar.xz
        tar -xvf riscv64-elf-ubuntu-22.04-gcc.tar.xz
        popd
        ;;
    riscv64-linux)
        pushd ${SYNTH}
        wget https://github.com/riscv-collab/riscv-gnu-toolchain/releases/download/2026.07.15/riscv64-glibc-ubuntu-22.04-gcc.tar.xz
        tar -xvf riscv64-glibc-ubuntu-22.04-gcc.tar.xz
        popd
        ;;
    arm32)
        ;;
    aarch32)
        ;;
    *)
        echo -e "\nNo tool with name ${toolname}"
        usage
        ;;
    esac
}

_check_core()
{
    local corename="$1"

    case "${corename}" in
    polyphony|wf3d|vortex|skybox)
        ;;
    *)
        echo "No core with name ${corename}"
        usage
        ;;
    esac
}

init_core()
{
    local corename="$1"

    _check_core "${corename}"

    case "${corename}" in
    polyphony)
        git clone https://github.com/Kenji-Ishimaru/polyphony cores/polyphony
        ;;
    wf3d)
        wget https://opencores.org/download/wf3d -O cores/wf3d/wf3d
        ;;
    skybox)
        git clone https://github.com/vortexgpgpu/skybox cores/skybox/skybox
        ;;
    vortex)
        git clone https://github.com/vortexgpgpu/vortex cores/vortex/vortex
        ;;
    esac
}

# TODO: pass litex arguments, as '-Wl,<linter_parameter>' in clang/gcc:
#       xargs + awk
# TODO: litex runs simulator with root rights, when --with-etherbone enabled
#       (due to TAP interface creation). So sim artifacts, like sim.vcd,
#       have root as owner.
# TODO: cannot generate fst trace. Only vcd + vcd2fst works
litex_sim()
{
    local corename="$1"
    local trace_end=10000000000000 # 10s

    _check_core "${corename}"

    ./litex_sim.py \
        --prefix-cores="./cores" \
        --integrated-main-ram-size=0x10000 \
        --cpu-type=vexriscv \
        --sim-debug \
        --trace \
        --trace-start 0 \
        --trace-end ${trace_end} \
        --gtkwave-savefile \
        --with-${corename}
}

litex_sim_zip()
{
    local sim="build/sim/"

    vcd2fst -p -v ${sim}/gateware/sim.vcd -f ${sim}/gateware/sim.fst
    rm ${sim}/gateware/sim.vcd
    tar -C "${sim}" -cvzf gateware.tar.gz gateware
}

usage()
{
    cat << EOF
Usage:
    $SCRIPTNAME env (create|activate|remove)

    $SCRIPTNAME install-tool <tool-name>
    $SCRIPTNAME install-core <core-name>

    $SCRIPTNAME litex-sim <core-name>
    $SCRIPTNAME litex-sim-zip

Available values for <tool-name>:
    litex         - full litex setup
    fusesoc       - fusesoc client
    verilator     - RTL simulator
    gtkwave       - Wave viewer and trace tools
    qemu          - emulator
    renode        - emulator
    openocd       - debugger + scripts
    opensbi       - system execution environment
    barebox       - barebox sources
    zephyr        - zephyr sources
    linux         - linux sources
    riscv32       - prebuilt baremetal toolchain for RV
    riscv32-linux - prebuilt RV toolchain for linux env
    riscv64       - prebuilt baremetal toolchain for RV
    riscv64-linux - prebuilt RV toolchain for linux env
    arm32         - prebuilt baremetal toolchain for ARMv7
    aarch32       - prebuilt baremetal toolchain for ARMv8

Available values for <core-name>:
    wf3d      - Wireframe rasterizer with fixed pipeline
    polyphony - Polygon rasterizer with fixed pipeline
    vortex    - GPGPU
    skybox    - GPGPU + Polygon rasterizer with shaders

EOF
}

case $CMDNAME in
    env)
        ENVCOMMAND="$2"
        env "$ENVCOMMAND"
        ;;
    install-tool)
        TOOLNAME="$2"
        init_tool "${TOOLNAME}"
        ;;
    install-core)
        CORENAME="$2"
        init_core "${CORENAME}"
        ;;
    litex-sim)
        CORENAME="$2"
        litex_sim "${CORENAME}"
        ;;
    litex-sim-zip)
        litex_sim_zip
        ;;
    *)
        usage
        exit 2
        ;;
esac

