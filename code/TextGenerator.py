import os
from huggingface_hub import InferenceClient
import re
import ast

from WebSearchClient import WebSearchClient


class TextGenerator:
    def __init__(self, inference_server_api_key, inference_server_base_url, text_model):
        
        self.webClient = WebSearchClient(
            inference_server_base_url=inference_server_base_url,
            inference_server_api_key=inference_server_api_key,
            text_model = text_model
        )

        self.dialogueClient = InferenceClient(
            base_url=inference_server_base_url,
            api_key=inference_server_api_key
        )
        
        self.text_model = text_model

    def __fetch_information(self, person):
        result = self.webClient.get_summary(
                query=person
        )
        return result

    def __generate_dialogue(self, information, person, age, nb):
        response = self.dialogueClient.chat.completions.create(
            model=self.text_model,
            messages=[
                {
                    "role": "system",
                    "content": """
                                You are a helpful assistant that only generates a dialogue using the information provided in the prompt.
                                You can add external knowledge about spoken subjects in the information. 
                                You generate only a Python list of strings, where each string is a line of dialogue.
                                Each line must follow this format exactly: SPEAKER: line of dialogue.
                                You are straightforward, concise, and stay on task.
                                """
                },
                {
                    "role": "user",
                    "content": f"""
                                Based on the following information about {person}:

                                {information}

                                Using this information, generate a dialogue of approximately {nb} exchanges about the life of {person}. You must talk about her childhood, studies, career and involvement for women in computer science. 
                                The speakers are : 
                                - PUPIL_01: a student
                                - TEACHER_F: a teacher

                                The dialogue must:
                                - Be entirely in French.
                                - Be designed to be read aloud (audio format), so use smooth and lively sentences, as if telling a story.
                                - Explain the person's scientific research, by simplifying the important concepts (like algorithms, systems, etc.) using metaphors or concrete examples. To do this: give the scientific term first, then explain what it means.
                                - Highlight their personal journey (life, family, anecdotes, choices, values…).
                                - Highlight their professional journey (studies, career, awards...) as well as their personal and scientific contributions.
                                - Be adapted to a {age}, using vocabulary and sentence structures appropriate for that age.
                                - Be structured as a Python list of strings named `liste_repliques`.
                                - Each string should be in this format:
                                SPEAKER: line of dialogue (e.g., "TEACHER_F: Bonjour, aujourd’hui nous allons parler de...").

                                Important:
                                - Do not include anything except the Python list `liste_repliques`.
                                - Do not write explanations, comments, or extra content.
                                """
                }
            ]
        )
        texte = response.choices[0].message.content
        return texte
    
    def __generate_speech(self, information, person, age, nb):
        response = self.dialogueClient.chat.completions.create(
            model=self.text_model,
            messages=[
                {
                    "role": "system",
                    "content": """
                                You are a helpful assistant that only generates a speech using the information provided in the prompt.
                                You can add external knowledge about spoken subjects in the information. 
                                You generate only a Python list containing 1 string
                                The string must follow this format exactly: SPEAKER: speech.
                                You are straightforward, concise, and stay on task.
                                """
                },
                {
                    "role": "user",
                    "content": f"""
                                Based on the following information about {person}:

                                {information}

                                Using this information, generate a speech of approximately {nb} lines about the life of {person}. You must talk about her childhood, studies, career and involvement for women in computer science. 

                                The speech must:
                                - Be entirely in French.
                                - Be adapted to a {age}, using vocabulary and sentence structures appropriate for that age.
                                - Be designed to be read aloud (audio format), so use smooth and lively sentences, as if telling a story.
                                - Explain the person's scientific research, by simplifying the important concepts (like algorithms, systems, etc.) using metaphors or concrete examples. To do this: give the scientific term first, then explain what it means.
                                - Highlight their personal journey (life, family, anecdotes, choices, values…).
                                - Highlight their professional journey (studies, career, awards...) as well as their personal and scientific contributions.
                                - Be structured as a Python list of strings named `liste_repliques`.
                                - The string should be in this format:
                                THEACHER_F: speech (e.g., "TEACHER_F: Bonjour, aujourd’hui nous allons parler de...").

                                Important:
                                - Do not include anything except the Python list `liste_repliques`.
                                - Do not write explanations, comments, or extra content.
                                """
                }
            ]
        )
        texte = response.choices[0].message.content
        return texte

    def __extract_liste_repliques(self, dialogue_str):
        match = re.search(r'liste_repliques\s*=\s*(\[[\s\S]*?\])', dialogue_str)
        if match:
            list_content = match.group(1)
            try:
                return ast.literal_eval(list_content)
            except Exception as e:
                print(f"Erreur lors de l'évaluation de la liste : {e}")
                return None
        else:
            print("Aucune liste 'liste_repliques' trouvée dans le texte.")
            return None

    def __save_dialogue(self, filename, dialogue, directory):
        # Ensure the directory exists
        os.makedirs(directory, exist_ok=True)
        # Save the dialogue to the specified file
        file_path = os.path.join(directory, filename)
        with open(file_path, "w") as file:
            for reply in dialogue:
                file.write(f"{reply}\n")
        return file_path
    
    def generate(self,person,age,contenu,nb,format,directory="../generated/dialogues",find_informations=True):
        os.makedirs(directory, exist_ok=True)
        if find_informations :
            print(f"Finding informations on {person}...")
            contenu += self.__fetch_information(person)
        if format == 'vu':
            print(f"Generating speech...")
            dialogue = self.__generate_speech(contenu,person,age,nb)
        else : 
            print(f"Generating dialogue...")
            dialogue = self.__generate_dialogue(contenu,person,age,nb)
        liste_repliques = self.__extract_liste_repliques(dialogue)
        file_path = self.__save_dialogue(f"{person}.txt", liste_repliques, directory)
        print(f"Dialogue saved to {file_path}")
        return file_path
