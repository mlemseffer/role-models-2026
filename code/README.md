# Podcast Generator

## Install

Create a venv directory in the root folder of the project :
```sh
mkdir venv
```

Create a python virtual environment using the following command :
```sh
python -m venv ./venv
```

Activate virtual environment using this command on linux : 
```sh
source /venv/bin/activate
```

Or this command on windows:
```sh
./venv/bin/activate.bash
```

You can then install the dependecies using :
```sh
pip install -r requirements.txt
```

## Usage of the main_pipeline.py script

Ce projet permet de générer automatiquement des podcasts vidéo illustrés à partir d’un nom de personnage et de l'âge pour lequel est destiné le podcast. Il utilise des modèles d’IA pour produire un discours, le convertir en audio, générer des images pertinentes, puis assembler le tout en une vidéo complète.

### Structure
Script principal : main_pipeline.py

Appelle plusieurs modules :
- SpeechGenerator : Génère un dialogue en texte concernant la personne.
- GeneratePodcast / PodcastGenerator2 : Génèrent l’audio à partir du texte.
- ImageGenerator : Crée des images à partir du texte.
- VideoGenerator : Assemble les images et l’audio en une vidéo.

### Dépendances
Python ≥ 3.8

#### Modules : 
`dotenv, os, sys, getopt`
#### Modules internes 
`SpeechGenerator, ImageGenerator, VideoGenerator, GeneratePodcast, PodcastGenerator2`

#### API nécessaires :

- ElevenLabs
- Gemini
- Ollama
- Hugging Face

### Variables d'environnement
Le fichier .env doit contenir :

- ELEVENLABS_API_KEY=your_elevenlabs_key
- OLLAMA_API_KEY=your_ollama_key
- OLLAMA_URL=your_ollama_url
- HUGGING_FACE_API_KEY=your_huggingface_key
- GEMINI_API_KEY=your_gemini_key (facultatif)
- Un fichier .gemini.api-keys est requis. Ce fichier correspond à différentes clés api pour gemini

## Utilisation
`python main_pipeline.py -p ("Nom Prenom" or Nom_Prenom) -a AGE [-f FORMAT] [-l LENGTH] [-c CONTENT_FILENAME]`

### Paramètres
```sh
-p	Nom de la personne (utiliser _ pour les espaces ou le mettre entre des strings)	| -p Anne-Marie_Kermarrec
-a  Age cible pour le podcast |-a "8/9 years old", "teenager"
-l	length : s (short, 10 répliques/images) ~1 min, m (medium, 15 répliques/images) ~1 min 30, l (long, 20 répliques/images) ~2 min |-l s | default : m
-c content_path : Chemin pour accéder au fichier avec des informations concernant la personne renseignée | default : None
-f format du contenu généré : vidéo + voix unique : 'vu' , vidéo + voix multiples : 'vm' , podcast : 'p' | -f vu | default : vm
```

### Exemple complet
`python main_pipeline.py -p Anne-Marie_Kermarrec -a 8/9 -l m -c amk_informations.txt -f vu`

Ce script :

- Génère un dialogue d'environ 20 phrases sur "Anne-Marie Kermarrec" à destination de 8/9 ans.
- Convertit le texte en audio.
- Génère 30 images correspondant au contenu.
- Assemble le tout en une vidéo.

### Résultats
- Dialogue : dialogues/<Nom>.txt
- Audio : ./podcasts/<Nom>.mp3
- Images : ./images/<Nom>/
- Vidéo finale : ./videos/<Nom>.mp4

## Format des fichiers de dialogues

Dialogues files use a specific format in order to be processed efficiently by the script : `SPEAKER_NAME: Text`.
`SPEAKER_NAME` can be one of the following : `TEACHER_F`, `TEACHER_M`, `PUPIL_01` or `PUPIL_02`.
One line must contain exactly one replica.
>>>>>>> oldremote/main
