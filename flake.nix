{
  description = "Notateit Viewer Remake";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };
  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      pythonPackages = pkgs.python313Packages;
      runtimeLibs = with pkgs; [
        dbus fontconfig freetype glib libGL libxcb-cursor libxft libxkbcommon
        qt6.qtwayland stdenv.cc.cc.lib wayland xorg.libX11 xorg.libXcursor
        xorg.libxcb zlib zstd
      ];
    in {
      packages.${system}.default = pythonPackages.buildPythonApplication {
        pname = "notateit";
        version = "1.0.2";
        pyproject = true;
        src = ./.;
        nativeBuildInputs = [
          pythonPackages.poetry-core
          pythonPackages.setuptools
          pkgs.qt6.wrapQtAppsHook
        ];
        buildInputs = [
          pkgs.qt6.qtbase
          pkgs.qt6.qtwayland
        ];
        propagatedBuildInputs = [
          pythonPackages.pyside6
          pythonPackages.pillow
        ];
        postInstall = ''
          mkdir -p $out/share/applications
          mkdir -p $out/share/icons/hicolor/512x512/apps

          if [ -d AppDir ]; then
            [ -f AppDir/usr/share/applications/notateit.viewer.remake.desktop ] && \
              cp AppDir/usr/share/applications/notateit.viewer.remake.desktop $out/share/applications/
            [ -f AppDir/usr/share/hicolor/512x512/apps/notateit_remake.png ] && \
              cp AppDir/usr/share/hicolor/512x512/apps/notateit_remake.png $out/share/icons/hicolor/512x512/apps/
          fi
        '';
        meta = with pkgs.lib; {
          description = "Notateit Viewer Remake";
          platforms = platforms.linux;
          mainProgram = "notateit";
        };
        qtWrapperArgs = [
          "--set QT_QPA_PLATFORM wayland;xcb"
        ];
      };
      devShells.${system}.default = pkgs.mkShell {
          buildInputs = [
            pkgs.poetry
            pkgs.python313
          ];
          shellHook = ''
          export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath runtimeLibs}:$LD_LIBRARY_PATH"
          export QT_PLUGIN_PATH=""
          '';
        };
    };
}