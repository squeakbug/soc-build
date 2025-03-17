# soc-build


## Example


```sh
# Export environment variables
source site-setup.sh
# Build environment
./build.sh env create
source ${SYNTH}/venv/bin/activate
./build.sh install-tool litex
./build.sh install-tool verilator
# Download IP-block source
./build.sh install-core polyphony
# Run SoC sumulation with litex CLI
./build.sh litex-sim polyphony

# After litex CLI loaded, data from configuration address space can be read:
mem_read 0x80010050 0x8
```

## Sources

- https://github.com/gvsoc/gvsoc
- https://github.com/fossi-foundation/nix-eda

