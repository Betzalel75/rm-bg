# Script de Suppression d'Arrière-Plan d'Image

Ce script Python permet de supprimer l'arrière-plan d'une image en utilisant la bibliothèque `rembg`. Le script a été corrigé pour gérer correctement les différents types de retour de la fonction `remove()`.

## Corrections apportées

- ✅ Correction de la gestion des différents types de retour de `remove()` (bytes, Image, numpy array)
- ✅ Résolution des problèmes d'importation et de portée des variables
- ✅ Ajout de la gestion d'erreurs complète
- ✅ Support amélioré des arguments en ligne de commande

## Fonctionnalités

- Suppression automatique de l'arrière-plan d'images
- Support de multiples formats d'image (JPG, PNG, etc.)
- Génération d'images avec transparence (format PNG)
- Interface en ligne de commande avec options
- Messages d'erreur détaillés

## Prérequis

- Python 3.6 ou supérieur
- pip (gestionnaire de paquets Python)

## Installation

1. Clonez ou téléchargez le script `remove-bg.py`

2. Installez les dépendances nécessaires :

```bash
pip install rembg pillow numpy
```

**Note :** `rembg` nécessite également `onnxruntime` qui sera installé automatiquement.

### Installation via requirements.txt

```bash
pip install -r requirements.txt
```

## Utilisation

### Droits

- Le script nécessite les droits de lecture et d'écriture sur les fichiers d'entrée et de sortie.
- Il nécessite également les droits de lecture et d'exécution sur le script lui-même.

```bash
chmod 555 remove-bg.py
```

### Syntaxe de base

```bash
python remove-bg.py <fichier_image>
```

### Avertissements

- Lors de la première exécution, le modèle ONNX peut être téléchargé automatiquement. Ce processus peut prendre un certain temps.


### Options disponibles

```
usage: remove-bg.py [-h] [-i INPUT_FILE] [-o OUTPUT_FILE] [-v] [input]

Supprime l'arrière-plan d'une image en utilisant rembg.

positional arguments:
  input                 Fichier image d'entrée

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_FILE, --input INPUT_FILE
                        Fichier image d'entrée (option longue)
  -o OUTPUT_FILE, --output OUTPUT_FILE
                        Fichier image de sortie (par défaut: [nom]_sans_fond.png)
  -v, --version         show program's version number and exit

Exemples d'utilisation :
  remove-bg.py image.jpg                    # Génère image_sans_fond.png
  remove-bg.py image.jpg -o resultat.png    # Spécifie le nom de sortie
  remove-bg.py -i image.jpg -o resultat.png # Version longue des options
```

### Exemples

1. **Supprimer l'arrière-plan d'une image simple :**

   ```bash
   ./remove-bg.py photo.jpg
   ```

   Génère : `photo_sans_fond.png`

2. **Spécifier un nom de fichier de sortie :**

   ```bash
   ./remove-bg.py photo.jpg -o resultat.png
   ```

3. **Utiliser les options longues :**
   ```bash
   ./remove-bg.py --input photo.jpg --output resultat_final.png
   ```

## Formats supportés

### Formats d'entrée :

- JPEG/JPG
- PNG
- BMP
- TIFF
- GIF
- Et autres formats supportés par Pillow

### Format de sortie :

- PNG (recommandé pour préserver la transparence)

## Dépannage

### Erreur : "Bibliothèque 'rembg' non installée"

```bash
pip install rembg pillow numpy
```

_`NB : il est recommandé d'utiliser un environnement virtuel pour éviter les conflits de dépendances.`_

### Erreur : "Attribute `save` is not defined on `bytes`"

Cette erreur était due à un bug dans la gestion des types de retour. La version corrigée du script gère maintenant correctement les bytes, images PIL et numpy arrays.

### Erreur : "Le fichier n'existe pas"

Vérifiez que le chemin vers l'image est correct et que le fichier existe.

### Erreur de permission

Assurez-vous d'avoir les droits de lecture sur le fichier d'entrée et d'écriture dans le répertoire de sortie.

### Performances

Le premier lancement peut être plus lent car `rembg` télécharge le modèle de machine learning.

### Erreurs d'importation

Si vous rencontrez des erreurs d'importation, assurez-vous que toutes les dépendances sont installées :

```bash
pip install rembg pillow numpy onnxruntime
```

## Structure du code

Le script est organisé en deux fonctions principales :

1. `supprimer_arriere_plan()` : Fonction principale qui effectue le traitement
2. `main()` : Gère les arguments en ligne de commande et l'exécution

## Licence

Ce script est fourni tel quel sans garantie. Vous pouvez l'utiliser et le modifier librement.

## Auteur

Script développé pour le traitement d'images avec Python.

## Notes techniques

- Le script utilise le modèle U²-Net intégré dans `rembg`
- La transparence est préservée en utilisant le format PNG
- Les images sont traitées telles quelles sans redimensionnement
- Le script gère maintenant les trois types de retour possibles de `remove()` :
  - `PIL.Image.Image` : image PIL directement utilisable
  - `bytes` : données binaires converties en image
  - `numpy.ndarray` : tableau numpy converti en image

## Tests

Un script de test est disponible pour vérifier le fonctionnement :

```bash
python test_remove_bg.py
```

## Fichiers inclus

- `remove-bg.py` : Script principal corrigé
- `requirements.txt` : Dépendances nécessaires
- `test_remove_bg.py` : Script de test
- `README.md` : Documentation (ce fichier)
