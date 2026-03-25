import re
from time import sleep
import os
from GeneratePodcast import GeneratePodcast


class AudioGenerator:

    def __init__(
        self,
        gemini_api_keys,
        teacher_voice="Erinome",
        student_voice="Rasalgethi",
        tts_model="gemini-2.5-flash-preview-tts",
    ):
        self.GEMINI_API_KEY_FILE = gemini_api_keys
        self.teacher_voice = teacher_voice
        self.student_voice = student_voice
        self.model = tts_model

    def generate(self, dialogue_file, output_filename, progress_file=None):
        os.makedirs(output_filename.rsplit("/", 1)[0] + "/", exist_ok=True)
        with open(self.GEMINI_API_KEY_FILE, "r") as f:
            api_keys = [line.strip() for line in f if line.strip()]
        print("Generating Audio...")
        for j in range(3):
            for i, key in enumerate(api_keys):
                print(f"Test {j*len(api_keys)+(i+1)} of {3*len(api_keys)}...")
                env = os.environ.copy()
                env["GEMINI_API_KEY"] = key
                try:
                    if progress_file:
                        output = GeneratePodcast(
                            gemini_api_key=key,
                            model=self.model,
                            teacher_voice=self.teacher_voice,
                            student_voice=self.student_voice,
                        ).resume_from_progress_file(
                            progress_filename=progress_file,
                            input_filename=dialogue_file,
                            output_filename=output_filename,
                        )
                    else:
                        output = GeneratePodcast(
                            gemini_api_key=key,
                            model=self.model,
                            teacher_voice=self.teacher_voice,
                            student_voice=self.student_voice,
                        ).generate(
                            input_filename=dialogue_file,
                            output_filename=output_filename,
                        )
                    print(f"Saved audio to {output}")
                    return output
                except Exception as e:
                    print(f"Error caught: {e}")
                    match = re.search(
                        r"progress has been saved in file (\S+\.pgs)", str(e)
                    )
                    if match:
                        progress_file = match.group(1).replace("\\", "/")
                    
                    # On s'assure de toujours faire une pause entre les tentatives pour éviter le rate limit,
                    # même s'il n'y a qu'une seule clé API (i == 0).
                    print("Waiting 60 seconds before next attempt to reset rate limits...")
                    sleep(60)
                    
                    print(f"Test {i+1} failed")
                    print("Continuing generation on another test...")
                    continue
        else:
            print("Toutes les tentatives de génération ont échoué...")
            exit(1)
