# Classeur de photos par visage

Application 100 % locale qui range tes photos dans des dossiers selon les personnes
reconnues. Tu definis les personnes (un prenom + une ou plusieurs photos de reference),
tu pointes le dossier a classer, et l'application copie chaque photo dans le bon dossier.

- 1 personne connue -> dossier a son **prenom**
- plusieurs connues -> dossier **`Prenom1_Prenom2_...`** (ordre alphabetique)
- visages inconnus -> **`Inconnus`** · photos sans visage -> **`Sans visage`**

Aucune photo ne quitte ton ordinateur. Aucun abonnement, aucune API payante.

## Installation (Windows 10/11)

1. **Installe Python 3.12** depuis <https://www.python.org/downloads/windows/>
   (rubrique "Stable Releases", derniere version 3.12.x, lien "Windows installer (64-bit)").
   **Coche "Add python.exe to PATH"** pendant l'installation.
2. **Double-clique `installer.bat`.** Il installe les composants un par un et affiche a la fin
   "OK : tous les composants sont installes." (laisse-le finir, puis ferme la fenetre).
3. **Double-clique `lancer.bat`.** Au tout premier lancement, le modele de reconnaissance
   se telecharge (~110 Mo) : Internet requis cette fois-la uniquement, puis tout est hors-ligne.

Tu n'as jamais de commande a taper.

## Utilisation

1. **Personnes** -> *Ajouter une personne* : saisis un prenom, clique *Choisir des photos*,
   selectionne le bon visage si la photo en contient plusieurs, puis *Enregistrer*.
2. **Source & parametres** -> choisis le dossier racine et le dossier de sortie
   (garde "Copier" pour ne pas toucher aux originaux).
3. **Classement** -> *Lancer l'apercu* (analyse sans rien copier) puis *Lancer le classement*.

## Bon a savoir

- **Seuil de ressemblance** (reglages avances) : si une meme personne est eclatee en
  plusieurs dossiers, baisse-le ; si des personnes sont confondues, monte-le. Relance l'apercu.
- **Profils complets / visages de dos** ne sont pas reconnus (-> `Inconnus` / `Sans visage`).
- **Performance** : sur CPU une grosse photothèque prend du temps ; une carte NVIDIA + l'option
  GPU accelere.
- **Lancements suivants** : seul `lancer.bat` est necessaire.

## Confidentialite & licence

- Traitement entierement local ; aucune photo ni empreinte envoyee en ligne.
- Moteur : FaceNet via `facenet-pytorch` (modele VGGFace2). Les poids pre-entraines sont
  destines a un usage de recherche / personnel, adapte au tri de tes propres photos.

## Depannage

- **"Python introuvable"** : Python absent ou case PATH non cochee. Reinstalle-le en cochant
  "Add python.exe to PATH".
- **installer.bat finit par [PROBLEME]** : un composant n'a pas pu se telecharger. En entreprise,
  c'est souvent un proxy/pare-feu. Copie la ligne rouge et envoie-la.
- **La fenetre ne s'ouvre pas** : assure-toi d'etre sous Windows 10/11 (composant Edge WebView2,
  normalement deja present).
