#!/usr/bin/env python3
"""
Script de test pour démontrer l'utilisation de remove-bg.py
"""

import os
import subprocess
import sys



def test_script_basique():
    """Test l'affichage de l'aide et la version"""
    print("🧪 Test 1: Affichage de l'aide")
    result = subprocess.run(
        [sys.executable, "remove-bg.py", "--help"], capture_output=True, text=True
    )
    if "usage:" in result.stdout:
        print("✅ Aide affichée correctement")
    else:
        print("❌ Échec de l'affichage de l'aide")
        print(result.stderr)

    print("\n🧪 Test 2: Version")
    result = subprocess.run(
        [sys.executable, "remove-bg.py", "--version"], capture_output=True, text=True
    )
    if "1.0" in result.stdout:
        print("✅ Version affichée correctement")
    else:
        print("❌ Échec de l'affichage de la version")


def test_file_exist():
    """Test avec un fichier qui n'existe pas"""
    print("\n🧪 Test 3: Fichier inexistant")
    result = subprocess.run(
        [sys.executable, "remove-bg.py", "fichier_inexistant.jpg"],
        capture_output=True,
        text=True,
    )
    if "n'existe pas" in result.stdout or "n'a pas été trouvé" in result.stdout:
        print("✅ Erreur détectée correctement pour fichier inexistant")
    else:
        print("❌ Échec de la détection de fichier inexistant")


def verifier_dependances():
    """Vérifie si les dépendances sont installées"""
    print("\n🔍 Vérification des dépendances...")
    try:
        import rembg
        from PIL import Image

        print("✅ rembg et PIL/Pillow sont installés")
        return True
    except ImportError as e:
        print(f"❌ Dépendances manquantes: {e}")
        print("\nPour installer les dépendances:")
        print("pip install rembg pillow")
        return False


def creater_example_image():
    """Crée une image exemple simple pour les tests"""
    print("\n🎨 Création d'une image exemple...")
    try:
        from PIL import Image, ImageDraw

        # Créer une image simple avec un cercle coloré
        img = Image.new("RGB", (200, 200), color="lightblue")
        draw = ImageDraw.Draw(img)

        # Dessiner un cercle rouge
        draw.ellipse([50, 50, 150, 150], fill="red", outline="darkred")

        # Ajouter du texte
        draw.text((60, 80), "TEST", fill="white")

        # Sauvegarder
        img.save("example_test.jpg")
        print("✅ Image exemple créée: example_test.jpg")
        return True
    except Exception as e:
        print(f"❌ Échec de création de l'image exemple: {e}")
        return False


def test_avec_image_exemple():
    """Test avec une image exemple créée"""
    print("\n🧪 Test 4: Traitement d'une image réelle")

    if not os.path.exists("example_test.jpg"):
        print("❌ Image exemple non trouvée")
        return False

    result = subprocess.run(
        [sys.executable, "remove-bg.py", "example_test.jpg"],
        capture_output=True,
        text=True,
    )

    if "Succès" in result.stdout or "Traitement" in result.stdout:
        print("✅ Script exécuté avec succès")

        # Vérifier si le fichier de sortie a été créé
        if os.path.exists("example_test_rmbg.png"):
            print("✅ Fichier de sortie créé: example_test_rmbg.png")

            # Vérifier la taille du fichier
            taille = os.path.getsize("example_test_rmbg.png")
            print(f"   Taille du fichier: {taille} octets")
            return True
        else:
            print("❌ Fichier de sortie non créé")
            return False
    else:
        print("❌ Échec de l'exécution du script")
        print("Sortie:", result.stdout)
        print("Erreur:", result.stderr)
        return False


def nettoyer_fichiers_test():
    """Nettoie les fichiers créés pendant les tests"""
    print("\n🧹 Nettoyage des fichiers de test...")

    files_to_remove = ["example_test.jpg", "example_test_rmbg.png"]

    for file in files_to_remove:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✅ Supprimé: {file}")
            except Exception as e:
                print(f"⚠️  Impossible de supprimer {file}: {e}")


def main():
    """Fonction principale des tests"""
    print("=" * 60)
    print("TEST DU SCRIPT remove-bg.py")
    print("=" * 60)

    # Vérifier que le script principal existe
    if not os.path.exists("remove-bg.py"):
        print("❌ Fichier remove-bg.py non trouvé")
        print("Assurez-vous d'être dans le bon répertoire")
        return

    # Exécuter les tests
    test_script_basique()

    if not verifier_dependances():
        print("\n⚠️  Les tests suivants nécessitent les dépendances installées")
        return

    test_file_exist()

    if creater_example_image():
        test_avec_image_exemple()

    nettoyer_fichiers_test()

    print("\n" + "=" * 60)
    print("TESTS TERMINÉS")
    print("=" * 60)

    print("\n📋 RÉSUMÉ D'UTILISATION:")
    print("Pour utiliser le script avec vos propres images:")
    print("1. python remove-bg.py votre_image.jpg")
    print("2. python remove-bg.py -i votre_image.jpg -o resultat.png")
    print("\nPour plus d'informations:")
    print("python remove-bg.py --help")


if __name__ == "__main__":
    main()
