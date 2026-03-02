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

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio

try:
    from PIL import Image
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

flatpak_python_path = os.path.expanduser('~/.var/app/org.gimp.GIMP/data/python/lib/python3.13/site-packages')
if flatpak_python_path not in sys.path:
    sys.path.append(flatpak_python_path)


class RemoveBackgroundPlugin(Gimp.PlugIn):
    
    def do_query_procedures(self):
        return ["python-fu-rembg-remove-bg"]
    
    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run, None)
        
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_menu_label("Supprimer l'arrière-plan (rembg)...")
        procedure.add_menu_path("<Image>/Filters/Detourage/")
        procedure.set_attribution("Assistant", "Assistant", "2024")
        procedure.set_documentation(
            "Supprime l'arrière-plan du calque actif en utilisant l'IA rembg",
            "Exporte temporairement le calque, applique rembg pour rendre le fond transparent, puis l'importe comme nouveau calque.",
            name
        )
        return procedure
    
    # def export_layer_to_temp_file(self, drawable, temp_path):
    #     """Exporte un calque vers un fichier PNG temporaire"""
    #     # Créer une nouvelle image temporaire
    #     width = drawable.get_width()
    #     height = drawable.get_height()
        
    #     # Déterminer le type d'image
    #     if drawable.has_alpha():
    #         image_type = Gimp.ImageType.RGBA_IMAGE
    #     else:
    #         image_type = Gimp.ImageType.RGB_IMAGE
        
    #     # Créer l'image temporaire
    #     temp_image = Gimp.Image.new(width, height, Gimp.ImageBaseType.RGB)
        
    #     # Copier le calque
    #     temp_layer = drawable.copy()
    #     temp_image.insert_layer(temp_layer, None, 0)
        
    #     # Exporter en PNG
    #     success = Gimp.get_pdb().run_procedure('file-png-save2', [
    #         GObject.Value(Gimp.RunMode, Gimp.RunMode.NONINTERACTIVE),
    #         GObject.Value(Gimp.Image, temp_image),
    #         GObject.Value(Gimp.Drawable, temp_layer),
    #         GObject.Value(Gio.File, Gio.File.new_for_path(temp_path)),
    #         GObject.Value(GObject.TYPE_BOOLEAN, False),  # interlace
    #         GObject.Value(GObject.TYPE_INT, 0),  # compression level
    #         GObject.Value(GObject.TYPE_BOOLEAN, False),  # save bkgd
    #         GObject.Value(GObject.TYPE_BOOLEAN, False),  # save gamma
    #         GObject.Value(GObject.TYPE_BOOLEAN, False),  # save offset
    #         GObject.Value(GObject.TYPE_BOOLEAN, False),  # save phys
    #         GObject.Value(GObject.TYPE_BOOLEAN, False),  # save time
    #         GObject.Value(GObject.TYPE_BOOLEAN, False),  # save comment
    #         GObject.Value(GObject.TYPE_BOOLEAN, True),   # save color from paras
    #         GObject.Value(GObject.TYPE_BOOLEAN, False),  # preserve color of transparent pixels
    #     ])
        
    #     # Nettoyer l'image temporaire
    #     Gimp.delete(temp_image)
        
    #     return success.index(0) == Gimp.PDBStatusType.SUCCESS
    
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
        Gimp.delete(temp_image)
        
        return success
    
    def run(self, procedure, run_mode, image, drawables, config, run_data):
        # Vérification des dépendances
        if not REMBG_AVAILABLE:
            Gimp.message("La bibliothèque 'rembg' ou 'Pillow' n'est pas installée dans l'environnement Python de GIMP.\n"
                         "Veuillez exécuter : pip install rembg pillow")
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error('rembg manquant'))
        
        # Utilisez len(drawables) au lieu de l'ancien n_drawables
        if len(drawables) != 1:
            Gimp.message("Veuillez sélectionner exactement un seul calque.")
            return procedure.new_return_values(Gimp.PDBStatusType.CALLING_ERROR, GLib.Error('Sélection invalide'))
        
        drawable = drawables[0]
        
        # Fichiers temporaires
        fd_in, temp_in = tempfile.mkstemp(suffix=".png")
        os.close(fd_in)
        fd_out, temp_out = tempfile.mkstemp(suffix=".png")
        os.close(fd_out)
        
        try:
            # 1. Sauvegarder le calque sélectionné dans un fichier PNG temporaire
            Gimp.progress_init("Exportation du calque...")
            
            if not self.export_layer_to_temp_file(drawable, temp_in):
                raise Exception("Échec de l'exportation temporaire du calque.")
            
            # 2. Traiter l'image avec rembg via Pillow
            Gimp.progress_init("Analyse de l'image avec l'IA rembg...")
            img = Image.open(temp_in)
            result = remove(img)
            
            if isinstance(result, bytes):
                out_img = Image.open(io.BytesIO(result))
            elif isinstance(result, np.ndarray):
                out_img = Image.fromarray(result)
            elif isinstance(result, Image.Image):
                out_img = result
            else:
                raise TypeError(f"Type inattendu retourné par rembg: {type(result)}")
            
            out_img.save(temp_out, format="PNG")
            
            # 3. Charger le fichier PNG transparent résultant
            Gimp.progress_init("Importation du résultat...")
            
            file_out = Gio.File.new_for_path(temp_out)
                        
            try:
                # CORRECTION 2 : Utiliser l'API GIMP 3.0 pour charger l'image
                loaded_image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, file_out)
                loaded_layers = loaded_image.list_layers()
                
                # Regrouper l'insertion dans un bloc d'annulation
                image.undo_group_start()
                
                for loaded_layer in loaded_layers:
                    # CORRECTION 1 : Créer le nouveau calque en le liant à l'image principale
                    new_layer = Gimp.Layer.new_from_drawable(loaded_layer, image)
                    new_layer.set_name(drawable.get_name() + " (sans fond)")
                    
                    # Positionner le nouveau calque juste au-dessus du calque d'origine
                    parent = drawable.get_parent()
                    try:
                        position = image.get_item_position(drawable)
                    except Exception:
                        position = 0
                        
                    image.insert_layer(new_layer, parent, position)
                    
                # Supprimer l'image temporaire chargée
                Gimp.delete(loaded_image)
                image.undo_group_end()
                Gimp.displays_flush()
                
            except Exception as e:
                raise Exception(f"Échec de l'importation du calque détouré : {str(e)}")
        
        except Exception as e:
            Gimp.message(f"Erreur lors du traitement : {str(e)}")
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