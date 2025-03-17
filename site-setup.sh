ROOT=$( [ "${EUID:=$(id -u)}" == 0 ] && echo true || echo false);

if [ "$ROOT" == true ]; then
    export SYNTH="/opt/synth"
else
    export SYNTH="$HOME/synth"
fi

export PATH=$SYNTH/riscv/bin:$PATH
export PATH=$SYNTH/oss-cad-suite/bin:$PATH
