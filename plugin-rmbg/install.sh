#!/usr/bin/env bash

set -euo pipefail
IFS=$'\n\t'

# ==============================
# Configuration
# ==============================

REPO_URL="https://github.com/Betzalel75/rm-bg.git"
PLUGIN_SUBDIR="rmbg"
TMP_DIR="$(mktemp -d)"
FLATPAK_APP_ID="org.gimp.GIMP"

# ============================
# Colors
# ============================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# ===========================
# Functions
# ===========================

function log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

function log_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

function log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

function log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║         GIMP 3.0 rembg Plugin Installer (Universal)         ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

function is_installed() {
  command -v "$1" >/dev/null 2>&1
}

function ask_yes_no(){
    local prompt="$1"
    local default="${2:-y}"
    if [[ "$default" == "y" ]]; then
            prompt="$prompt [Y/n] "
        else
            prompt="$prompt [y/N] "
     fi
     while true; do
         read -rp "$prompt" answer
         case "${answer:-$default}" in
             [Yy]* ) return 0;;
             [Nn]* ) return 1;;
             * ) echo "Please answer yes (y) or no (n).";;
        esac
    done
}

# ==============================
# Check dependencies (system packages)
# ==============================

function install_with_package_manager() {
    local package="$1"
    local managers=(
        "apt-get:apt-get install -y"
        "yum:yum install -y"
        "dnf:dnf install -y"
        "pacman:pacman -S --noconfirm"
        "zypper:zypper install -y"
        "apk:apk add"
        "brew:brew install"
    )

    for manager_cmd in "${managers[@]}"; do
        local manager="${manager_cmd%%:*}"
        local cmd="${manager_cmd#*:}"

        if command -v "$manager" >/dev/null 2>&1; then
            log_info "Installing $package using $manager..."
            if [[ "$manager" == "apt-get" ]]; then
                sudo apt-get update
            fi
            case "$manager" in
                brew) $cmd "$package" ;;
                *) 
                    # shellcheck disable=SC2086
                    sudo $cmd "$package" ;;
            esac
            return $?
        fi
    done

    log_error "Could not find a supported package manager"
    return 1
}

# ==============================
# GIMP installation detection
# ==============================

function detect_gimp_installation() {
    local gimp_flatpak_installed=false
    local gimp_system_installed=false

    # Check Flatpak GIMP
    if flatpak list --app 2>/dev/null | grep -q "$FLATPAK_APP_ID"; then
        gimp_flatpak_installed=true
    fi

    # Check system GIMP (by looking for gimp binary)
    if is_installed gimp; then
        if ! gimp --version 2>/dev/null | grep -qi flatpak; then
            gimp_system_installed=true
        fi
    fi

    if $gimp_flatpak_installed && $gimp_system_installed; then
        log_warning "Both Flatpak and system GIMP installations detected."
        if ask_yes_no "Use system GIMP? (If no, Flatpak will be used)" "y"; then
            USE_FLATPAK=false
        else
            USE_FLATPAK=true
        fi
    elif $gimp_flatpak_installed; then
        log_info "Flatpak GIMP detected."
        USE_FLATPAK=true
    elif $gimp_system_installed; then
        log_info "System GIMP detected."
        USE_FLATPAK=false
    else
        log_error "No GIMP installation found."
        if ask_yes_no "Do you want to install GIMP now?"; then
            if ask_yes_no "Install Flatpak version? (If no, system package will be attempted)" "y"; then
                USE_FLATPAK=true
                install_flatpak_gimp
            else
                USE_FLATPAK=false
                install_system_gimp
            fi
        else
            exit 1
        fi
    fi
}

function install_flatpak_gimp() {
    if ! is_installed flatpak; then
        log_error "flatpak is not installed"
        if ask_yes_no "Do you want to install flatpak?"; then
            install_with_package_manager "flatpak" || exit 1
        else
            exit 1
        fi
    fi
    log_info "Installing GIMP from Flathub..."
    flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
    flatpak install flathub "$FLATPAK_APP_ID" -y
}

function install_system_gimp() {
    log_info "Attempting to install GIMP via system package manager..."
    install_with_package_manager "gimp" || {
        log_error "Could not install GIMP automatically."
        log_info "Please install GIMP 3.x manually and re-run this script."
        exit 1
    }
}

get_gimp_major_minor() {
    local version_cmd
    if [[ "$USE_FLATPAK" == true ]]; then
        version_cmd="flatpak run $FLATPAK_APP_ID --version 2>&1"
    else
        version_cmd="gimp --version 2>&1"
    fi

    local full_version
    full_version=$($version_cmd | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [[ -n "$full_version" ]]; then
        echo "$full_version" | cut -d. -f1,2
    else
        local latest_dir
        latest_dir=$(find "$HOME"/.config/GIMP/ -maxdepth 1 -type d -regextype posix-extended -regex '.*/[0-9]+\.[0-9]+' -printf '%f\n' 2>/dev/null | sort -V | tail -1)
        if [[ -n "$latest_dir" ]]; then
            echo "$latest_dir"
        else
            echo "3.0"
        fi
    fi
}

function check_gimp_version() {
    local version_cmd
    if [[ "$USE_FLATPAK" == true ]]; then
        version_cmd="flatpak run $FLATPAK_APP_ID --version 2>&1"
    else
        version_cmd="gimp --version 2>&1"
    fi

    local gimp_version
    if gimp_version=$($version_cmd | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -1); then
        log_info "Found GIMP version: $gimp_version"
        if [[ ! "$gimp_version" =~ ^3\. ]]; then
            log_warning "This plugin is designed for GIMP 3.x"
            log_info "You have GIMP $gimp_version."
            if ! ask_yes_no "Continue anyway?" "n"; then
                exit 1
            fi
        fi
    else
        log_warning "Could not determine GIMP version."
    fi
}

function install_packages() {
    if ! is_installed git; then
        log_warning "git is not installed"
        if ask_yes_no "Do you want to install git?"; then
            install_with_package_manager "git" || exit 1
        else
            exit 1
        fi
    fi
    log_success "git verified"

    if ! is_installed msgfmt; then
        log_warning "gettext is not installed"
        if ask_yes_no "Do you want to install gettext?"; then
            install_with_package_manager "gettext" || exit 1
        else
            exit 1
        fi
    fi
    log_success "gettext verified"

    # For system GIMP, no extra check needed.
    # For Flatpak, we already ensured flatpak and GIMP are installed in detect_gimp_installation.
    if [[ "$USE_FLATPAK" == true ]]; then
        if ! is_installed flatpak; then
            log_error "flatpak is not installed"
            exit 1
        fi
        if ! flatpak list --app | grep -q "$FLATPAK_APP_ID"; then
            log_error "GIMP Flatpak not found."
            exit 1
        fi
    else
        if ! is_installed gimp; then
            log_error "GIMP system installation not found."
            exit 1
        fi
    fi
    check_gimp_version
    log_success "GIMP verified"
}

# Install dependencies for Flatpak
function install_flatpak_deps() {
    log_info "Installing Flatpak dependencies..."
    flatpak run --command=curl org.gimp.GIMP -L https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    flatpak run --command=python3 org.gimp.GIMP /tmp/get-pip.py --user
    flatpak run --command=python3 org.gimp.GIMP -m pip install pillow numpy --user
    flatpak run --command=python3 org.gimp.GIMP -m pip install "rembg[cpu]" --user
    log_success "Flatpak dependencies installed"
}

# Install dependencies for system installation
function install_system_deps() {
    INSTALL_DIR=$1
    log_info "Installing system dependencies..."

    echo
    log_info "Python dependencies needed: rembg and pillow"
    echo "Choose Python dependencies installation method:"
    echo "  1) Create a dedicated virtual environment (recommended, safe)"
    echo "  2) Use an existing virtual environment ($HOME/your-venv)"
    echo "  3) Skip (I will configure manually later)"
    read -rp "Your choice [1/2/3]: " py_choice

    # Ask about GPU acceleration early (used by cases 1 and 2)
    USE_GPU=false
    if [[ "$py_choice" =~ ^[12]$ ]]; then
        echo
        log_info "GPU Acceleration"
        echo "  CPU mode:  Works everywhere, moderate speed (a few seconds)"
        echo "  GPU mode:  Ultra-fast (< 1 sec), requires NVIDIA CUDA or AMD ROCm"
        echo
        if ask_yes_no "Use GPU acceleration? (requires CUDA/ROCm drivers)" "n"; then
            USE_GPU=true
            REMBG_PKG="rembg[gpu]"
            log_info "GPU mode selected — will install onnxruntime-gpu"
        else
            REMBG_PKG="rembg"
            log_info "CPU mode selected"
        fi
    fi

    case "$py_choice" in
        1)
            VENV_DIR="$HOME/.local/share/gimp-rembg-venv"
            log_info "Creating virtual environment in $VENV_DIR..."

            if ! python3 -m venv --help >/dev/null 2>&1; then
                log_warning "python3-venv is not installed."
                if ask_yes_no "Attempt to install python3-venv?"; then
                    install_with_package_manager "python3-venv" || exit 1
                else
                    exit 1
                fi
            fi

            python3 -m venv "$VENV_DIR"
            source "$VENV_DIR/bin/activate"
            pip install --upgrade pip
            pip install "$REMBG_PKG" pillow numpy

            echo "$VENV_DIR" > "$INSTALL_DIR/venv_path.txt"
            log_success "Virtual environment configured and dependencies installed."
            deactivate
            ;;
        2)
            read -rp "Enter the full path to your existing virtual environment: " VENV_PATH
            if [[ ! -d "$VENV_PATH" ]] || [[ ! -f "$VENV_PATH/bin/python" ]]; then
                log_error "Invalid virtual environment directory."
                exit 1
            fi
            log_info "Using existing venv: $VENV_PATH"
            source "$VENV_PATH/bin/activate"

            if ! "$VENV_PATH/bin/python" -c "import rembg" 2>/dev/null; then
                log_warning "rembg not found in this venv."
                if ask_yes_no "Install rembg and pillow now?"; then
                    pip install "$REMBG_PKG" pillow numpy
                else
                    log_error "Plugin will not work without rembg."
                    exit 1
                fi
            else
                log_success "rembg is already installed."
                if $USE_GPU; then
                    log_warning "rembg already installed, but GPU extras may be missing."
                    if ask_yes_no "Install onnxruntime-gpu now?"; then
                        pip install onnxruntime-gpu
                    fi
                fi
            fi

            echo "$VENV_PATH" > "$INSTALL_DIR/venv_path.txt"
            log_success "Virtual environment configured."
            deactivate
            ;;
        *)
            log_warning "Dependencies not installed. You must install rembg and pillow manually."
            log_info "You can later create a venv and write its path to:"
            echo "$INSTALL_DIR/venv_path.txt"
            ;;
    esac
    log_success "System dependencies installed"
}

# Function Main

function main(){
    print_header
    echo

    detect_gimp_installation
    install_packages

    GIMP_VERSION_DIR=$(get_gimp_major_minor)
    INSTALL_DIR="$HOME/.config/GIMP/$GIMP_VERSION_DIR/plug-ins/$PLUGIN_SUBDIR"
    log_info "GIMP configuration directory: $HOME/.config/GIMP/$GIMP_VERSION_DIR"
    sleep 2

    # ==============================
    # Clone repository
    # ==============================

    log_info "[1/6] Cloning repository..."
    if ! git clone --depth 1 "$REPO_URL" "$TMP_DIR"; then
      log_error "Failed to clone repository."
      exit 1
    fi

    # ==============================
    # Create install directory
    # ==============================

    sleep 2

    log_info "[2/6] Creating plugin directory..."
    mkdir -p "$INSTALL_DIR"

    # ==============================
    # Copy plugin files
    # ==============================

    log_info "[3/6] Copying plugin source..."
    cp "$TMP_DIR/$PLUGIN_SUBDIR/rmbg.py" "$INSTALL_DIR/"

    # ==============================
    # Setup locale structure
    # ==============================

    log_info "[4/6] Setting up locale structure..."

    mkdir -p "$INSTALL_DIR/locale/en/LC_MESSAGES"
    mkdir -p "$INSTALL_DIR/locale/fr/LC_MESSAGES"

    sleep 2

    cp "$TMP_DIR/$PLUGIN_SUBDIR/locale/en/LC_MESSAGES/"*.po \
    "$INSTALL_DIR/locale/en/LC_MESSAGES/"

    cp "$TMP_DIR/$PLUGIN_SUBDIR/locale/fr/LC_MESSAGES/"*.po \
    "$INSTALL_DIR/locale/fr/LC_MESSAGES/"

    # ==============================
    # Compile translations
    # ==============================

    log_info "[5/6] Compiling translations..."

    sleep 2

    msgfmt \
    "$INSTALL_DIR/locale/en/LC_MESSAGES/gimp30-plugin-rembg.po" \
    -o "$INSTALL_DIR/locale/en/LC_MESSAGES/gimp30-plugin-rembg.mo"

    msgfmt \
    "$INSTALL_DIR/locale/fr/LC_MESSAGES/gimp30-plugin-rembg.po" \
    -o "$INSTALL_DIR/locale/fr/LC_MESSAGES/gimp30-plugin-rembg.mo"

    # ==============================
    # Set permissions
    # ==============================

    log_info "[6/6] Setting permissions..."

    chmod 755 "$INSTALL_DIR/rmbg.py"

    # ==============================
    # Cleanup
    # ==============================

    sleep 2

    rm -rf "$TMP_DIR"

    echo
    log_success "✅ Installation complete!"
    log_info "Plugin installed in:"
    echo "$INSTALL_DIR"
    echo
    if [[ "$USE_FLATPAK" == true ]]; then
        install_flatpak_deps
        log_warning "🔄 Restart GIMP (Flatpak)."
    else
        install_system_deps "$INSTALL_DIR"
        log_warning "🔄 Restart GIMP (system version)."
    fi
}

main "$@"
