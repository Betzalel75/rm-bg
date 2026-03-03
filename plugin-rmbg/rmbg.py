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

try:
    from PIL import Image
    from rembg import remove, new_session
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

flatpak_python_path = os.path.expanduser('~/.var/app/org.gimp.GIMP/data/python/lib/python3.13/site-packages')
if flatpak_python_path not in sys.path:
    sys.path.append(flatpak_python_path)


# Configuration de l'internationalisation
# ========================================
# Définir le domaine de traduction
DOMAIN = "gimp30-plugin-rembg"
# Chemin où se trouvent les fichiers de traduction (.mo)
LOCALE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locale")

# Initialiser gettext
try:
    # Essayer de charger les traductions
    translation = gettext.translation(DOMAIN, LOCALE_DIR, fallback=True)
    _ = translation.gettext
except Exception:
    # Fallback si les traductions ne sont pas disponibles
    def _(s):
        return s

# Fonction pour formater les messages avec des variables
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
        procedure.add_menu_path("<Image>/Filters/Detourage/")
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
        
        # Créer l'image temporaire
        temp_image = Gimp.Image.new(width, height, Gimp.ImageBaseType.RGB)
        
        # CORRECTION 1 : Transférer le calque vers la NOUVELLE image
        temp_layer = Gimp.Layer.new_from_drawable(drawable, temp_image)
        temp_image.insert_layer(temp_layer, None, 0)
        
        # CORRECTION 2 : Utiliser l'API GIMP 3.0 pour sauvegarder (plus de PDB fastidieux)
        file = Gio.File.new_for_path(temp_path)
        
        # Gimp.file_save prend: mode, image, liste de calques, fichier destination
        success = Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, temp_image, file)
        
        # Nettoyer
        temp_image.delete()
        
        return success
    
    def run(self, procedure, run_mode, image, drawables, config, run_data):
        # Vérification des dépendances
        if not REMBG_AVAILABLE:
            Gimp.message(_("The 'rembg' or 'Pillow' library is not installed in GIMP's Python environment.\n"
                                     "Please run: pip install rembg pillow"))
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error(_('rembg missing')))
        
        # Utilisez len(drawables) au lieu de l'ancien n_drawables
        if len(drawables) != 1:
            Gimp.message(_("Please select exactly one layer."))
            return procedure.new_return_values(Gimp.PDBStatusType.CALLING_ERROR, GLib.Error(_('Invalid selection')))
        
        drawable = drawables[0]
        
        # Fichiers temporaires
        fd_in, temp_in = tempfile.mkstemp(suffix=".png")
        os.close(fd_in)
        fd_out, temp_out = tempfile.mkstemp(suffix=".png")
        os.close(fd_out)
        
        try:
            # 1. Sauvegarder le calque sélectionné dans un fichier PNG temporaire
            Gimp.progress_init(_("Exporting layer..."))
            
            if not self.export_layer_to_temp_file(drawable, temp_in):
                raise Exception(_("Failed to temporarily export the layer."))
            
            # 2. Traiter l'image avec rembg via Pillow
            Gimp.progress_init(_("Analyzing image with rembg AI..."))
            img = Image.open(temp_in)
            
            # Forcer l'utilisation du CPU pour éviter l'erreur Flatpak/CUDA
            session = new_session("u2net", providers=['CPUExecutionProvider'])
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
            
            # 3. Charger le fichier PNG transparent résultant
            Gimp.progress_init(_("Importing result..."))
            
            file_out = Gio.File.new_for_path(temp_out)
                        
            try:
                # CORRECTION 2 : Utiliser l'API GIMP 3.0 pour charger l'image
                loaded_image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, file_out)
                loaded_layers = loaded_image.get_layers()
                
                # Regrouper l'insertion dans un bloc d'annulation
                image.undo_group_start()
                
                for loaded_layer in loaded_layers:
                    # CORRECTION 1 : Créer le nouveau calque en le liant à l'image principale
                    new_layer = Gimp.Layer.new_from_drawable(loaded_layer, image)
                    new_layer.set_name(drawable.get_name() + _(" (no background)"))
                    
                    # Positionner le nouveau calque juste au-dessus du calque d'origine
                    parent = drawable.get_parent()
                    try:
                        position = image.get_item_position(drawable)
                    except Exception:
                        position = 0
                        
                    image.insert_layer(new_layer, parent, position)
                    
                # Supprimer l'image temporaire chargée
                loaded_image.delete()
                image.undo_group_end()
                Gimp.displays_flush()
                
            except Exception as e:
                raise Exception(_("Failed to import the cutout layer: {}").format(str(e)))
        
        except Exception as e:
            Gimp.message(_("Error during processing: {}").format(str(e)))
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error(str(e)))
        
        finally:
            # Nettoyage des fichiers temporaires
            if os.path.exists(temp_in):
                os.remove(temp_in)
            if os.path.exists(temp_out):
                os.remove(temp_out)
        
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())



if __name__ == '__main__':
    Gimp.main(RemoveBackgroundPlugin.__gtype__, sys.argv)