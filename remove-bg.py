#!/usr/bin/env python3
"""
Script pour supprimer l'arrière-plan d'une image en utilisant rembg.
"""

import argparse
import os
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image
from rembg import remove


def remove_bg(input_file, output_file=None):
    """
    Supprime l'arrière-plan d'une image.

    Args:
        input_file (str): Chemin vers l'image d'entrée
        output_file (str, optional): Chemin vers l'image de sortie.
                                        Si None, génère un nom automatiquement.

    Returns:
        bool: True si succès, False sinon
    """
    try:
        # Vérifier que le fichier d'entrée existe
        if not os.path.exists(input_file):
            print(f"❌ Erreur : Le fichier '{input_file}' n'existe pas.")
            return False

        # Générer un nom de fichier de sortie si non spécifié
        if output_file is None:
            chemin = Path(input_file)
            output_file = f"{chemin.stem}_rmbg.png"

        # Vérifier l'extension du fichier de sortie
        if not output_file.lower().endswith(".png"):
            print(
                "⚠️  Attention : Le format PNG est recommandé pour préserver la transparence."
            )
            print("   Le fichier de sortie sera converti en PNG si nécessaire.")

        print(f"📂 Traitement de l'image : {input_file}")
        print(f"💾 Fichier de sortie : {output_file}")

        # Ouvrir l'image originale
        print("🔍 Ouverture de l'image...")
        image_originale = Image.open(input_file)
        print(f"   Format : {image_originale.format}")
        print(f"   Taille : {image_originale.size}")
        print(f"   Mode : {image_originale.mode}")

        # Supprimer l'arrière-plan
        print("🎨 Suppression de l'arrière-plan...")
        resultat = remove(image_originale)

        # Gérer les différents types de retour de remove()
        if isinstance(resultat, Image.Image):
            # Si c'est déjà une image PIL
            image_detouree = resultat
        elif isinstance(resultat, bytes):
            # Si c'est des bytes, les charger comme image
            image_detouree = Image.open(BytesIO(resultat))
        elif isinstance(resultat, np.ndarray):
            # Si c'est un numpy array, le convertir en image PIL
            image_detouree = Image.fromarray(resultat)
        else:
            raise TypeError(f"Type de retour non supporté: {type(resultat)}")

        # Sauvegarder le résultat
        print("💾 Sauvegarde du résultat...")
        image_detouree.save(output_file)

        print(f"✅ Succès ! L'image a été sauvegardée sous : {output_file}")
        print(f"   Taille finale : {image_detouree.size}")

        return True

    except FileNotFoundError:
        print(f"❌ Erreur : Le fichier '{input_file}' n'a pas été trouvé.")
        return False
    except PermissionError:
        print(
            f"❌ Erreur : Permission refusée pour accéder au fichier '{input_file}'."
        )
        return False
    except IOError as e:
        print(f"❌ Erreur d'E/S : {e}")
        return False
    except ImportError:
        print("❌ Erreur : Bibliothèque 'rembg' non installée.")
        print("   Installez-la avec : pip install rembg")
        return False
    except Exception as e:
        print(f"❌ Une erreur inattendue s'est produite : {e}")
        return False


def main():
    """Fonction principale du script."""
    parser = argparse.ArgumentParser(
        description="Supprime l'arrière-plan d'une image en utilisant rembg.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation :
  %(prog)s image.jpg                    # Génère image_sans_fond.png
  %(prog)s image.jpg -o resultat.png    # Spécifie le nom de sortie
  %(prog)s -i image.jpg -o resultat.png # Version longue des options
        """,
    )

    parser.add_argument("input", nargs="?", help="Fichier image d'entrée")

    parser.add_argument(
        "-i",
        "--input",
        dest="input_file",
        help="Fichier image d'entrée (option longue)",
    )

    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        help="Fichier image de sortie (par défaut: [nom]_rmbg.png)",
    )

    parser.add_argument("-v", "--version", action="version", version="%(prog)s 1.0")

    args = parser.parse_args()

    # Déterminer le fichier d'entrée
    input_file = args.input_file or args.input

    if not input_file:
        print("❌ Erreur : Vous devez spécifier un fichier d'entrée.")
        print("   Utilisez : python remove-bg.py <fichier_image>")
        print("   ou : python remove-bg.py -i <fichier_image>")
        parser.print_help()
        sys.exit(1)

    # Exécuter le traitement
    succes = remove_bg(input_file, args.output_file)

    if not succes:
        sys.exit(1)


if __name__ == "__main__":
    main()
