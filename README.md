# NotateIt Viewer Remake

**A modern, cross-platform viewer and extractor for the old, proprietary NotateIt (`.nat`) presentation format.**

[![PyPI version](https://img.shields.io/pypi/v/notateit.svg?style=flat-square)](https://pypi.org/project/notateit/)
[![Python versions](https://img.shields.io/pypi/pyversions/notateit.svg?style=flat-square)](https://pypi.org/project/notateit/)
[![PyPI Downloads](https://static.pepy.tech/badge/notateit?style=flat-square)](https://pepy.tech/project/notateit)
[![License](https://img.shields.io/pypi/l/notateit.svg?style=flat-square)](https://github.com/ndenissov/notateit/blob/main/LICENSE)
<img src="https://raw.githubusercontent.com/ndenissov/notateit/main/notateit/notateit_remake.png" alt="Notateit Logo" height="20" align="right">

---

## About

**NotateIt Viewer Remake** is a feature-rich tool designed to rescue and interact with `.nat` files—an old, unsupported,
and proprietary presentation format originally created for *NotateIt*.

Built with Python and PySide6, this remake offers both a user-friendly graphical interface with a dedicated presentation
mode and a powerful command-line interface (CLI) for parsing and exporting embedded assets (images and text) into
standard JSON format.

## Features

* **Interactive GUI:** Easily navigate through slides. Double-click to inspect text blocks and images.
* **Presentation Mode:** Distraction-free, fullscreen presentation viewing with keyboard navigation.
* **Data Rescue (CLI Extractor):** Headless extraction of internal text and embedded PNGs to structured JSON files.
* **Asset Exporting:** Instantly copy text to your clipboard or save embedded images directly to your disk.
* **Cross-Platform:** Works seamlessly on Windows, macOS, and Linux (including NixOS support).

---

## Installation

### 1. From PyPI (Recommended)

You can install the viewer and its dependencies directly via `pip`. Python 3.10+ is required.

```bash
pip install notateit
```

### 2. Pre-compiled Binaries (Standalone)

If you don't have Python installed, you can download pre-compiled standalone executables from
the [GitHub Releases](https://github.com/ndenissov/notateit/releases):

* **Windows (.exe):** Download `NotateitViewerRemake.exe`
* **Linux (AppImage):** Download `NotateIt_Viewer_Remake-x86_64.AppImage`

### 3. Nix / NixOS

The repository includes a `flake.nix` for declarative development and usage on Nix-based systems:

```bash
# Run directly from GitHub
nix run github:ndenissov/notateit

# Or drop into a development shell
nix develop
```

---

## Usage

### Graphical User Interface (GUI)

Simply run the application from your terminal. You can optionally pass the path to a `.nat` file to open it immediately:

```bash
notateit
# or
notateit path/to/presentation.nat
```

### Command-Line Interface (CLI) Extraction

NotateIt includes a built-in extractor to unpack the proprietary `.nat` files into raw assets and a readable JSON
structure without opening the GUI.

```bash
notateit path/to/presentation.nat --extract --output ./extracted_assets
```

**CLI Arguments:**

* `input`: Path to the input `.nat` file.
* `-x`, `--extract`: Enable extraction mode.
* `-o`, `--output`: Target directory for extracted `.png` files and the final `.json` map.
* `-m`, `--minimize`: Output minified JSON (removes indentation to save space).

---

## Keyboard Shortcuts

NotateIt is designed for efficiency. Here are the default keybindings available in the GUI:

| Action                 | Shortcut                           | Context                                |
|:-----------------------|:-----------------------------------|:---------------------------------------|
| **Open File**          | <kbd>Ctrl</kbd> + <kbd>O</kbd>     | Global                                 |
| **Close File**         | <kbd>Ctrl</kbd> + <kbd>X</kbd>     | Global                                 |
| **Next Slide**         | <kbd>Shift</kbd> + <kbd>N</kbd>    | Main Window                            |
| **Previous Slide**     | <kbd>Shift</kbd> + <kbd>P</kbd>    | Main Window                            |
| **Start Presentation** | <kbd>F5</kbd>                      | Main Window                            |
| **Minimize / Exit**    | <kbd>Esc</kbd>                     | Presentation Mode / Main Window        |
| **Inspect Object**     | <kbd>Ctrl</kbd> + <kbd>Enter</kbd> | When an image or text block is focused |
| **Copy Text**          | <kbd>Ctrl</kbd> + <kbd>C</kbd>     | When a text block is focused           |
| **Save Image**         | <kbd>Ctrl</kbd> + <kbd>S</kbd>     | When an image block is focused         |

---

## Contributing

Contributions, issues, and feature requests are welcome.
Feel free to check out the [issues page](https://github.com/ndenissov/notateit/issues). If you're modifying the code, we
recommend using `poetry` for dependency management:

```bash
poetry install
poetry run notateit
```

## License

Distributed under the MIT License. See `LICENSE` for more information.

*Developed by Nikita Denissov*
