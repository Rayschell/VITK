#!/bin/bash

# Script pour configurer l'environnement virtuel et installer les dépendances
# ITK/VTK Mini-Project

echo "============================================"
echo "🐍 Configuration de l'environnement Python"
echo "============================================"

# Vérifier si l'environnement virtuel existe
if [ ! -d ".venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv .venv
    if [ $? -eq 0 ]; then
        echo "✅ Environnement virtuel créé dans .venv"
    else
        echo "❌ Erreur lors de la création de l'environnement virtuel"
        exit 1
    fi
else
    echo "✅ Environnement virtuel existant trouvé"
fi

# Activer l'environnement virtuel
echo "🔄 Activation de l'environnement virtuel..."
source .venv/bin/activate

# Mettre à jour pip
echo "⬆️ Mise à jour de pip..."
pip install --upgrade pip

# Installer les dépendances
echo "📚 Installation des dépendances ITK/VTK..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Installation terminée avec succès!"
    echo ""
    echo "Pour utiliser l'environnement:"
    echo "  source .venv/bin/activate"
    echo "  python main.py"
    echo ""
    echo "Pour désactiver l'environnement:"
    echo "  deactivate"
else
    echo "❌ Erreur lors de l'installation des dépendances"
    exit 1
fi
