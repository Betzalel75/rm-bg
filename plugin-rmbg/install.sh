#!/usr/bin/env bash

set -euo pipefail
IFS=$'\n\t'

# ==============================
# Configuration
# ==============================

REPO_URL="https://github.com/Betzalel75/rm-bg.git"
PLUGIN_SUBDIR="plugin-rmbg"
INSTALL_DIR="$HOME/.config/GIMP/3.0/plug-ins/plugin-rmbg"
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
CYAN='\033[0;36m'
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
    echo "║         GIMP 3.0 rembg Plugin Installer (Flatpak)           ║"
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
         read -p "$prompt" answer
         case "${answer:-$default}" in
             [Yy]* ) return 0;;
             [Nn]* ) return 1;;
             * ) echo "Please answer yes (y) or no (n).";;
        esac
    done
}

# ==============================
# Check dependencies
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
            sudo $cmd "$package"
            return $?
        fi
    done
    
    log_error "Could not find a supported package manager"
    return 1
}

function check_gimp_version() {
    local gimp_version
    if gimp_version=$(flatpak info org.gimp.GIMP 2>/dev/null | grep -i "version:" | head -1); then
        log_info "Found GIMP version: $gimp_version"
        if [[ ! "$gimp_version" =~ 3\. ]]; then
            log_warning "This plugin is designed for GIMP 3.x"
            log_info "Updating to GIMP 3.x is recommended."
            if ! ask_yes_no "Do you want to update to GIMP 3.x?" "n"; then
                exit 1
            else
                log_info "Updating to GIMP 3.x..."
                flatpak --user update
                log_success "GIMP updated to version $gimp_version"
            fi
        fi
    fi
}

function install_packages() {
    # Check git
    if ! is_installed git; then
        log_warning "git is not installed"
        if ask_yes_no "Do you want to install git?"; then
            install_with_package_manager "git" || exit 1
        else
            exit 1
        fi
    fi
    log_success "git verified"
    
    # Check gettext (msgfmt)
    if ! is_installed msgfmt; then
        log_warning "gettext is not installed"
        if ask_yes_no "Do you want to install gettext?"; then
            install_with_package_manager "gettext" || exit 1
        else
            exit 1
        fi
    fi
    log_success "gettext verified"
    
    # Check Flatpak
    if ! is_installed flatpak; then
        log_error "flatpak is not installed"
        log_info "This plugin requires GIMP Flatpak"
        if ask_yes_no "Do you want to install flatpak?"; then
            install_with_package_manager "flatpak" || exit 1
        else
            exit 1
        fi
    fi
    
    # Check GIMP Flatpak
    if ! flatpak list --app | grep -q "$FLATPAK_APP_ID"; then
        log_warning "GIMP Flatpak is not installed"
        if ask_yes_no "Do you want to install GIMP Flatpak?"; then
            log_info "Installing GIMP from Flathub..."
            flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
            flatpak install flathub org.gimp.GIMP -y
        else
            exit 1
        fi
    fi
    check_gimp_version
    log_success "GIMP Flatpak verified"
}


# Function Main

function main(){
    print_header
    echo
    
    install_packages
    
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
    log_warning "🔄 Restart GIMP 3.x."

}

main "$@"
