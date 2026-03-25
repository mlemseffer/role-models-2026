from ImageGenerator import ImageGenerator
from TextGenerator import TextGenerator
from VideoGenerator import VideoGenerator
from AudioGenerator import AudioGenerator
import os
from dotenv import load_dotenv
import getopt
import sys

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_URL = os.getenv("OLLAMA_URL")
HUGGING_FACE_URL = "https://huggingface.co/api"
HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEYS_FILE = "./.gemini.api-keys"


teacher_voice = "Erinome"
student_voice = "Rasalgethi"

tts_provider = "gemini"
text_model = "llama3.3:70b"  # modèles disponibles : qwen3:32b, qwen2.5:32b, llama3.3:70b

image_model = "black-forest-labs/FLUX.1-schnell"
image_to_text_model = "google/gemma-3-27b-it"
tts_model = "gemini-2.5-flash-preview-tts"
age = None
person = None
nb = 15
contenu = ""
format = "vm"
fps = 12
fade_duration = 1.0
image_url = None
find_informations = True


def print_help():
    print(
        """
        ## Utilisation
        python main_pipeline.py -p ("Nom Prenom" or Nom_Prenom) -a AGE [-f FORMAT] [-l LENGTH] [-c CONTENT_FILENAME]

        ### Paramètres
        -p	Nom de la personne (utiliser _ pour les espaces ou le mettre entre des strings)	| -p Anne-Marie_Kermarrec
        -a  Age cible pour le podcast |-a "8/9 years old", "teenager"
        -l	length : s (short, 10 répliques/images) ~1 min, m (medium, 15 répliques/images) ~1 min 30, l (long, 20 répliques/images) ~2 min |-l s | default : m
        -c content_path : Chemin pour accéder au fichier avec des informations concernant la personne renseignée | default : None
        -f format du contenu généré : vidéo + voix unique : 'vu', vidéo + voix multiples : 'vm', podcast : 'p' | -f vu | default : vm
        -i image_url (local ou web) de la personne concernée par le podcast | -i https://www.ins2i.cnrs.fr/sites/institut_ins2i/files/styles/article/public/image/DSC_1603_site.png?itok=Bxb-ChHW | default : None
        
        ### Exemple complet
        python main_pipeline.py -p Anne-Marie_Kermarrec -a 8/9 -l m -c amk_informations.txt -f vu
        """
    )


try:
    opts, args = getopt.getopt(sys.argv[1:], "p:a:l:f:c:hi:n")
except:
    print("Error while parsing args")
    exit(1)

for opt, arg in opts:
    if opt in ["-a"]:
        age = arg
    elif opt in ["-p"]:
        person = arg.replace("_", " ")
    elif opt in ["-l"]:
        if arg == "s":
            nb = 10
        elif arg == "l":
            nb = 20
    elif opt in ["-c"]:
        with open(arg, "r") as f:
            contenu = f.read()
    elif opt in ["-f"]:
        format = arg
    elif opt in ["-i"]:
        image_url = arg
    elif opt in ["-n"]:
        find_informations = False
    elif opt in ["-h"]:
        print_help()
        exit(0)


assert age != None, "age should be specified"
assert person != None, "person should be specified"
assert(find_informations or contenu != "")

dialogue_directory = "../generated/dialogues"
audio_filename = f"../generated/podcasts/{person}"
image_directory = f"../generated/images/{person}"
video_path = f"../generated/videos/{person}.mp4"

speech_path = TextGenerator(
    inference_server_base_url=OLLAMA_URL,
    inference_server_api_key=OLLAMA_API_KEY,
    text_model=text_model,
).generate(
    person=person,
    age=age,
    contenu=contenu,
    nb=nb,
    format=format,
    directory=dialogue_directory,
    find_informations = find_informations
)

audio_path = AudioGenerator(
    gemini_api_keys=GEMINI_API_KEYS_FILE,
    teacher_voice=teacher_voice,
    student_voice=student_voice,
    tts_model=tts_model,
).generate(
    dialogue_file=speech_path,
    output_filename=audio_filename,
)

if format == "p":
    exit(0)

ImageGenerator(
    text_inference_server_api_key=OLLAMA_API_KEY,
    text_inference_server_url=OLLAMA_URL,
    image_inference_server_api_key=HUGGING_FACE_API_KEY,
    image_inference_server_url=HUGGING_FACE_URL,
    image_to_text_inference_server_api_key=HUGGING_FACE_API_KEY,
    image_to_text_model=image_to_text_model,
    text_model=text_model,
    image_model=image_model,
).generate(
    dialogue_file=speech_path,
    images_nb=nb,
    output_directory=image_directory,
    person=person,
    age=age,
    image_url = image_url
)

VideoGenerator().generate(
    images_dir=image_directory,
    audio_path=audio_path,
    output_path=video_path,
    fps=fps,
    fade_duration=fade_duration,
)
