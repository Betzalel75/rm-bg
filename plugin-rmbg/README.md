# GIMP 3.0 – Remove Background Plugin (rembg)

A **GIMP 3.0 Python plugin** that removes the background of the active layer using the AI-powered [`rembg`](https://github.com/danielgatis/rembg) library.

The plugin exports the selected layer to a temporary PNG file, processes it with `rembg`, and re-imports the transparent result as a new layer.

---

## 🚀 Features

* Works with **GIMP 3.0 (Python API / GI)**
* Adds a menu entry under:

```
Image → Filters → Detourage → Supprimer l'arrière-plan (rembg)...
```

* Processes **RGB and GRAY images**
* Inserts the result as a **new layer with transparency**
* Uses **CPU inference** for maximum Flatpak compatibility

---

## 📦 Requirements

* GIMP 3.0 (Flatpak version supported)
* Python 3 (embedded in GIMP)
* `rembg`
* `pillow`
* `numpy`

---

# 🧩 Installation (Flatpak Version of GIMP 3.0)

Because the Flatpak version of GIMP runs in a sandboxed environment, you must install Python dependencies inside the Flatpak container.

---

## 1️⃣ Install pip inside the Flatpak environment

```bash
# Download pip installer
flatpak run --command=curl org.gimp.GIMP -L https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py

# Install pip inside GIMP Flatpak environment
flatpak run --command=python3 org.gimp.GIMP /tmp/get-pip.py --user
```

---

## 2️⃣ Install required Python packages

```bash
flatpak run --command=python3 org.gimp.GIMP -m pip install rembg pillow numpy --user
```

---

## 3️⃣ Install CPU support (Recommended for Flatpak)

```bash
flatpak run --command=python3 org.gimp.GIMP -m pip install "rembg[cpu]" --user
```

---

# ⚙️ Why We Use `rembg[cpu]` in Flatpak

Flatpak environments are sandboxed and have limited access to GPU drivers, CUDA libraries, and NVIDIA runtime bindings. GPU-based inference (`rembg[gpu]`) requires CUDA and ONNX GPU providers, which are extremely complex to configure inside Flatpak and often fail due to driver isolation.

For this reason, the **CPU version is strongly recommended** when running GIMP via Flatpak.

| Characteristic    | rembg[cpu]           | rembg[gpu]           |
| ----------------- | -------------------- | -------------------- |
| Installation      | Easy and lightweight | Very heavy (> 1 GB)  |
| Compatibility     | 100% (all PCs)       | Random (NVIDIA only) |
| Flatpak Stability | Excellent            | Very complicated     |
| Speed             | Good (a few seconds) | Ultra-fast (< 1 sec) |

In practice, CPU inference is more than fast enough for standard image sizes and provides maximum stability across systems.

---

# 📂 Plugin Installation

1. Place the plugin file:

```
rm-bg/plugin-rmbg/rmbg.py
```

into your GIMP 3.0 plug-ins directory.

For Flatpak GIMP:

```
~/.config/GIMP/3.0/plug-ins/
```

Example:

```bash
mkdir -p ~/.config/GIMP/3.0/plug-ins/plugin-rmbg
cp rmbg.py ~/.config/GIMP/3.0/plug-ins/plugin-rmbg/
```

## Or use the provided script

```bash
chmod +x install.sh
./install.sh
```

---

## 🔐 Make the script executable

```bash
chmod 755 rmbg.py
```

This ensures:

* Read + execute permissions
* No accidental modification

---

# ▶️ Usage

1. Open an image in GIMP 3.0
2. Select the layer you want to process
3. Go to:

```
Image → Filters → Detourage → Supprimer l'arrière-plan (rembg)...
```

4. The plugin will:

   * Export the active layer
   * Process it using AI
   * Insert a new transparent layer above the original

The original layer remains untouched.

---

# 🧠 How It Works Internally

1. Exports the active drawable to a temporary PNG
2. Forces CPU execution provider:

```python
session = new_session("u2net", providers=['CPUExecutionProvider'])
```

3. Handles multiple possible return types:

   * `bytes`
   * `numpy.ndarray`
   * `PIL.Image`
4. Saves processed PNG
5. Imports it as a new layer
6. Cleans up temporary files

---

# 🐞 Troubleshooting

### ❌ “rembg not installed”

Re-run:

```bash
flatpak run --command=python3 org.gimp.GIMP -m pip install rembg pillow numpy --user
flatpak run --command=python3 org.gimp.GIMP -m pip install "rembg[cpu]" --user
```

---

### ❌ Plugin not appearing in menu

* Ensure the script is executable (`chmod 555 rmbg.py`)
* Ensure it is inside:

  ```
  ~/.config/GIMP/3.0/plug-ins/
  ```
* Restart GIMP

---

# 🏗 Architecture Overview

## 🖌️ GIMP 3.0

![Image](https://librearts.org/2023/11/gimp-3-0-roadmap/featured.webp)

![Image](https://www.digitec.ch/Files/7/6/7/5/4/8/1/9/gimp-gui.jpg)

![Image](https://developer.gimp.org/core/specifications/layer-effects-ui/Basic/apply_an_effect/2.jpg)

![Image](https://librearts.org/2025/03/gimp-3-0-released/gimp-3-0-layer-locks.webp)

The plugin uses the new GI-based Python API introduced in:

* GIMP

It relies on:

* rembg (AI background removal)
* Pillow (image handling)
* NumPy (array compatibility)
* Flatpak (sandbox runtime)

---

# 📜 License

This plugin is provided as-is under the MIT License. Feel free to modify and distribute.

---
