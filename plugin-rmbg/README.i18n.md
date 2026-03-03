
---

# GIMP 3.0 – Internationalization & Build Guide

This document explains the new **internationalization (i18n) system**, translation workflow, additional dependencies, and compilation steps for the `gimp30-plugin-rembg` project.

---

# 🌍 Internationalization (i18n)

The plugin now supports **multiple languages** using GNU `gettext`.

Currently supported:

* 🇬🇧 English
* 🇫🇷 French

Language selection is automatically handled by:

* The system locale
* GIMP’s runtime environment

The plugin loads translations from:

```
~/.config/GIMP/3.0/plug-ins/locale/<lang>/LC_MESSAGES/gimp30-plugin-rembg.mo
```

---

## 🧠 How It Works

The plugin uses Python's built-in:

* `gettext`
* `gettext.translation()`

Domain:

```python
DOMAIN = "gimp30-plugin-rembg"
```

Locale directory:

```python
LOCALE_DIR = os.path.join(os.path.dirname(__file__), "locale")
```

Translation function:

```python
_ = translation.gettext
```

All user-facing strings are wrapped with:

```python
_("My translatable string")
```

---

# 📂 Locale Directory Structure

```
plugin-rmbg/
│
├── rmbg.py
├── locale/
│   ├── en/
│   │   └── LC_MESSAGES/
│   │       ├── gimp30-plugin-rembg.po
│   │       └── gimp30-plugin-rembg.mo
│   └── fr/
│       └── LC_MESSAGES/
│           ├── gimp30-plugin-rembg.po
│           └── gimp30-plugin-rembg.mo
```

---

# 🛠 New Dependencies

In addition to previous requirements:

* `rembg`
* `pillow`
* `numpy`

You now also need:

* GNU `gettext`
* `msgfmt` (to compile `.po` → `.mo`)

On Debian/Ubuntu:

```bash
sudo apt install gettext
```

---

# 🔨 Compiling Translation Files

`.po` files must be compiled into `.mo` files before GIMP can use them.

From the `plugin-rmbg` directory:

### Compile English

```bash
msgfmt ~/.config/GIMP/3.0/plug-ins/locale/en/LC_MESSAGES/gimp30-plugin-rembg.po \
-o ~/.config/GIMP/3.0/plug-ins/locale/en/LC_MESSAGES/gimp30-plugin-rembg.mo
```

### Compile French

```bash
msgfmt ~/.config/GIMP/3.0/plug-ins/locale/fr/LC_MESSAGES/gimp30-plugin-rembg.po \
-o ~/.config/GIMP/3.0/plug-ins/locale/fr/LC_MESSAGES/gimp30-plugin-rembg.mo
```

---

## 🧪 Verifying Compilation

You should see:

```
gimp30-plugin-rembg.mo
```

inside each `LC_MESSAGES` folder.

If `.mo` files are missing, translations will fallback to default strings.

---

# ➕ Adding a New Language

Example: Spanish (`es`)

### 1️⃣ Create directory

```
~/.config/GIMP/3.0/plug-ins/locale/es/LC_MESSAGES/
```

### 2️⃣ Copy template

```bash
cp ~/.config/GIMP/3.0/plug-ins/locale/en/LC_MESSAGES/gimp30-plugin-rembg.po \
~/.config/GIMP/3.0/plug-ins/locale/es/LC_MESSAGES/gimp30-plugin-rembg.po
```

### 3️⃣ Edit:

```po
Language: es
Language-Team: Spanish
```

Translate all `msgstr` values.

### 4️⃣ Compile

```bash
msgfmt ~/.config/GIMP/3.0/plug-ins/locale/es/LC_MESSAGES/gimp30-plugin-rembg.po \
-o ~/.config/GIMP/3.0/plug-ins/locale/es/LC_MESSAGES/gimp30-plugin-rembg.mo
```

Done.

---

# 🧩 How GIMP Selects Language

The plugin respects:

* `LANG`
* `LC_ALL`
* System locale

Example:

```bash
LANG=fr_FR.UTF-8 flatpak run org.gimp.GIMP
```

`NB : If previous translations set manually the language in GIMP preferences, they will override these environment variables.`

---

# 🏗 Full Build Workflow (Flatpak + i18n)

### 1️⃣ Install dependencies inside Flatpak

```bash
flatpak run --command=python3 org.gimp.GIMP -m pip install rembg pillow numpy --user
flatpak run --command=python3 org.gimp.GIMP -m pip install "rembg[cpu]" --user
```

---

### 2️⃣ Compile translations

```bash
msgfmt ~/.config/GIMP/3.0/plug-ins/locale/en/LC_MESSAGES/gimp30-plugin-rembg.po \
-o ~/.config/GIMP/3.0/plug-ins/locale/en/LC_MESSAGES/gimp30-plugin-rembg.mo

msgfmt ~/.config/GIMP/3.0/plug-ins/locale/fr/LC_MESSAGES/gimp30-plugin-rembg.po \
-o ~/.config/GIMP/3.0/plug-ins/locale/fr/LC_MESSAGES/gimp30-plugin-rembg.mo
```

---

### 3️⃣ Install plugin

```bash
mkdir -p ~/.config/GIMP/3.0/plug-ins/plugin-rmbg
cp -r plugin-rmbg/* ~/.config/GIMP/3.0/plug-ins/plugin-rmbg/
chmod 555 ~/.config/GIMP/3.0/plug-ins/plugin-rmbg/rmbg.py
```

Restart GIMP.

---

# 🧪 Development Mode Tip

To test translations without reinstalling:

```bash
export LANG=fr_FR.UTF-8
flatpak run org.gimp.GIMP
```

---

# 🔎 What Changed in the Codebase

### Added

* `gettext` initialization
* Translation domain configuration
* Locale directory loading
* `_()` wrapping for all UI strings
* Safe fallback when `.mo` files are missing

### Improved

* Error messages now localized
* Menu label localized
* Layer naming localized
* Progress messages localized

---

# 🧠 Architectural Note

## 🖌️ GIMP 3.0

![Image](https://librearts.org/2023/11/gimp-3-0-roadmap/featured.webp)

![Image](https://gimpchat.com/files/196_2025-12-09_030531.png)

![Image](https://www.cyberciti.biz/media/new/cms/2025/03/Installing-GIMP-3.0-on-Linux-desktop-using-flatpak.png)

![Image](https://www.gimp.org/news/2024/12/27/gimp-3-0-RC2-released/gimp-3.0.0-rc2-broken-font-macos.jpg)

This plugin relies on:

* GIMP – new GI-based Python API
* GNU gettext – translation framework
* rembg – AI segmentation
* Flatpak – runtime isolation

---

# 📌 Recommendation

Keep:

* `README.md` → user-focused
* `README.i18n.md` → developer-focused

This separation keeps your GitHub repository clean and professional.

---
