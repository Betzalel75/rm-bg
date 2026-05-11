#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plugin GIMP 3.0 pour supprimer l'arrière-plan d'une image en utilisant rembg.
"""
import io
import numpy as np
import tempfile
import os
import sys
import gettext

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio

def add_python_packages_path():
    """
    Ajoute au sys.path les répertoires contenant rembg / pillow.
    Priorité : fichier venv_path.txt (si présent) > user site-packages.
    """
    if os.path.exists('/.flatpak-info') or 'FLATPAK_ID' in os.environ:
        flatpak_path = os.path.expanduser('~/.var/app/org.gimp.GIMP/data/python/lib/python3.13/site-packages')
        if os.path.isdir(flatpak_path) and flatpak_path not in sys.path:
            sys.path.insert(0, flatpak_path)
        return

    venv_config = os.path.join(os.path.dirname(__file__), 'venv_path.txt')
    if os.path.exists(venv_config):
        with open(venv_config, 'r') as f:
            venv_path = f.read().strip()
            if os.path.isdir(venv_path):
                site_packages = os.path.join(
                    venv_path, 'lib',
                    f'python{sys.version_info.major}.{sys.version_info.minor}',
                    'site-packages'
                )
                if os.path.isdir(site_packages) and site_packages not in sys.path:
                    sys.path.insert(0, site_packages)
                    return

    # Fallback
    user_site = os.path.expanduser(
        f'~/.local/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages'
    )
    if os.path.isdir(user_site) and user_site not in sys.path:
        sys.path.insert(0, user_site)

add_python_packages_path()

try:
    from PIL import Image
    from rembg import remove, new_session
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False


def create_rembg_session(model_name="birefnet-general"):
    """
    Create a rembg session auto-detecting the best execution provider.

    Queries ONNX Runtime for actually available providers and selects
    the first matching GPU backend in priority order:
      NVIDIA → AMD → Intel → CPU fallback.
    TensorRT is deliberately excluded from auto-detection because it
    requires a separate NVIDIA TensorRT SDK (libnvinfer.so.10) that
    most users don't have; requesting it triggers noisy EP Errors.
    """
    import onnxruntime as ort

    available = ort.get_available_providers()

    # Priority: dedicated GPUs first, then integrated, then CPU
    preferred = [
        'CUDAExecutionProvider',        # NVIDIA GPU (CUDA)
        'ROCMExecutionProvider',        # AMD GPU (ROCm)
        'OpenVINOExecutionProvider',    # Intel GPU / accelerators
        'CPUExecutionProvider',         # Universal fallback
    ]

    providers = [p for p in preferred if p in available]

    return new_session(model_name, providers=providers)


DOMAIN = "gimp30-plugin-rembg"
LOCALE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locale")

try:
    translation = gettext.translation(DOMAIN, LOCALE_DIR, fallback=True)
    _ = translation.gettext
except Exception:
    def _(s):
        return s

def N_(message):
    """Marqueur pour les chaînes à traduire (sans traduction immédiate)"""
    return message


class RemoveBackgroundPlugin(Gimp.PlugIn):
    
    def do_query_procedures(self):
        return ["python-fu-rembg-remove-bg"]
    
    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run, None)
        
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_menu_label(_("Remove Background (rembg)"))
        procedure.add_menu_path(_("<Image>/AI/Clipping/"))
        procedure.set_attribution("Betzalel75", "Betzalel75", "2026")
        procedure.set_documentation(
            _("Removes the background from the active layer using rembg AI"),
            _("Temporarily exports the layer, applies rembg to make the background transparent, then imports it as a new layer."),
            name
        )
        return procedure
    
    def export_layer_to_temp_file(self, drawable, temp_path):
        """Exporte un calque vers un fichier PNG temporaire"""
        width = drawable.get_width()
        height = drawable.get_height()
        
        temp_image = Gimp.Image.new(width, height, Gimp.ImageBaseType.RGB)
        
        temp_layer = Gimp.Layer.new_from_drawable(drawable, temp_image)
        temp_image.insert_layer(temp_layer, None, 0)
        
        file = Gio.File.new_for_path(temp_path)
        
        success = Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, temp_image, file)
        
        temp_image.delete()
        
        return success
    
    def run(self, procedure, run_mode, image, drawables, config, run_data):
        if not REMBG_AVAILABLE:
            Gimp.message(_("The 'rembg' or 'Pillow' library is not installed in GIMP's Python environment.\n"
                                     "Please run: pip install rembg pillow"))
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error(_('rembg missing')))
        
        if len(drawables) != 1:
            Gimp.message(_("Please select exactly one layer."))
            return procedure.new_return_values(Gimp.PDBStatusType.CALLING_ERROR, GLib.Error(_('Invalid selection')))
        
        drawable = drawables[0]
        
        fd_in, temp_in = tempfile.mkstemp(suffix=".png")
        os.close(fd_in)
        fd_out, temp_out = tempfile.mkstemp(suffix=".png")
        os.close(fd_out)
        
        try:
            Gimp.progress_init(_("Exporting layer..."))
            
            if not self.export_layer_to_temp_file(drawable, temp_in):
                raise Exception(_("Failed to temporarily export the layer."))
            
            Gimp.progress_init(_("Analyzing image with rembg AI..."))
            img = Image.open(temp_in)
            
            session = create_rembg_session()
            result = remove(img, session=session)
            
            if isinstance(result, bytes):
                out_img = Image.open(io.BytesIO(result))
            elif isinstance(result, np.ndarray):
                out_img = Image.fromarray(result)
            elif isinstance(result, Image.Image):
                out_img = result
            else:
                raise TypeError(_("Unexpected type returned by rembg: {}").format(type(result)))
            
            out_img.save(temp_out, format="PNG")
            
            Gimp.progress_init(_("Importing result..."))
            
            file_out = Gio.File.new_for_path(temp_out)
                        
            try:
                loaded_image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, file_out)
                loaded_layers = loaded_image.get_layers()
                
                image.undo_group_start()
                
                for loaded_layer in loaded_layers:
                    new_layer = Gimp.Layer.new_from_drawable(loaded_layer, image)
                    new_layer.set_name(drawable.get_name() + _(" (no background)"))
                    
                    parent = drawable.get_parent()
                    try:
                        position = image.get_item_position(drawable)
                    except Exception:
                        position = 0
                        
                    image.insert_layer(new_layer, parent, position)
                    
                loaded_image.delete()
                image.undo_group_end()
                Gimp.displays_flush()
                
            except Exception as e:
                raise Exception(_("Failed to import the cutout layer: {}").format(str(e)))
        
        except Exception as e:
            Gimp.message(_("Error during processing: {}").format(str(e)))
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error(str(e)))
        
        finally:
            if os.path.exists(temp_in):
                os.remove(temp_in)
            if os.path.exists(temp_out):
                os.remove(temp_out)
        
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())



if __name__ == '__main__':
    Gimp.main(RemoveBackgroundPlugin.__gtype__, sys.argv)
