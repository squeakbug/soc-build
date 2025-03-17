{
  description = "Example C++ development environment for Zero to Nix";

  # Flake inputs
  inputs = {
    nixpkgs.url = "https://flakehub.com/f/NixOS/nixpkgs/0.2405.*.tar.gz";
  };

  # Flake outputs
  outputs = { self, nixpkgs }:
    let
      # Systems supported
      allSystems = [
        "x86_64-linux" # 64-bit Intel/AMD Linux
      ];

      # Helper to provide system-specific attributes
      forAllSystems = f: nixpkgs.lib.genAttrs allSystems (system: f {
        pkgs = import nixpkgs { inherit system; };
      });
    in
    {
      # Development environment output
      devShells = forAllSystems ({ pkgs }: {
        default = pkgs.mkShell {
          # The Nix packages provided in the environment
          packages = with pkgs; [
            cmake
            circt
            boost # The Boost libraries
            gcc # The GNU Compiler Collection (~1.3 GB)
            verilog # iverilog
            verilator
            python3
            systemc
          ];
        };
      });

        packages = forAllSystems ({ pkgs }: {
          default =
            let
              binName = "tlm";
              cppDependencies = with pkgs; [ boost gcc systemc ];
            in
            pkgs.stdenv.mkDerivation {
              name = "tlm";
              src = self;
              buildInputs = cppDependencies;
              buildPhase = ''
                cd sim/tlm-sc
                mkdir -p build && cd build
                cmake ..
                cmake --build .
              '';
              installPhase = ''
                cmake --install .
              '';
            };
        });
    };
}
