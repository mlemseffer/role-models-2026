import requests
from huggingface_hub import InferenceClient
import ast
import re
import time
import os
from WebSearchClient import WebSearchClient


MAX_ATTEMPTS_SUITABLE_IMAGE = 3
class ImageGenerator:
    def __init__(
        self,
        text_inference_server_api_key,
        text_inference_server_url,
        image_inference_server_api_key,
        image_inference_server_url,
        image_to_text_inference_server_api_key,
        image_to_text_model,
        text_model,
        image_model,
    ):
        self.text_inference_client = InferenceClient(
            base_url=text_inference_server_url, api_key=text_inference_server_api_key
        )
        self.image_inference_client = InferenceClient(
            base_url=image_inference_server_url, api_key=image_inference_server_api_key
        )
        self.web_client = WebSearchClient(
            inference_server_base_url=text_inference_server_url,
            inference_server_api_key=text_inference_server_api_key,
            text_model=text_model,
        )
        self.image_to_text_inference_client = InferenceClient(
            api_key=image_to_text_inference_server_api_key,
        )
        self.text_model = text_model
        self.image_model = image_model
        self.image_to_text_model = image_to_text_model

    def __get_most_important_points(self, dialogue: str, point_nb: int):
        response = self.text_inference_client.chat.completions.create(
            model=self.text_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that only output the answer to the question. your answer must be a python list. Do not respond with your thought process, just the answer.",
                },
                {
                    "role": "user",
                    "content": f"Using the following dialogue : {dialogue}. Generate {point_nb} prompts describing scenes that fit what is said in the dialogue in a chronological order.",
                },
            ],
        )
        return response.choices[0].message.content

    def __improve_description(self, description, person_description):
        response = self.text_inference_client.chat.completions.create(
            model=self.text_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that only output the answer to the question. your answer must be an improved prompt to generate an image. Do not respond with your thought process, just the answer.",
                },
                {
                    "role": "user",
                    "content": f"Enhance the following prompt to generate a detailed image: {description}. Enrich the background with as many specific visual elements as possible, fully aligned with the original description. The image must also include a person matching this description: {person_description}, they should be part a of the scene in the background or foreground depending on the context. Only return the final prompt without any explanations or tags.",
                },
            ],
        )
        return response.choices[0].message.content

    def __generate_image(self, description, age, output_directory):
        image = self.image_inference_client.text_to_image(
            f"In a suitable art style for the {age}. Generate this image : " + description + "The image should be flattering for the person described.",
            model=self.image_model,
            num_inference_steps=6,
        )
        output_filename = os.path.join(
            output_directory, f"img_gen{round(time.time() * 1000)}" + ".webp"
        )
        image.save(output_filename)
        return output_filename

    def __get_person_description(self, person, image_url):
        valid_image_not_found = True
        attempts = MAX_ATTEMPTS_SUITABLE_IMAGE
        if image_url == None:
            while(valid_image_not_found and attempts != 0):
                image_url = self.web_client.get_person_image(person, MAX_ATTEMPTS_SUITABLE_IMAGE - attempts)
                print(f"Found image of {person} at : {image_url}")
                valid_image_not_found = requests.options(image_url).status_code >= 400
                attempts -= 1
                if(valid_image_not_found):
                    print("URL not responding, trying another image...")
            if(attempts == 0):
                print("Could not find a valid image describing the person. Try specifying an image URL with the -i parameter.")
                exit(1)

        response = self.image_to_text_inference_client.chat.completions.create(
            model=self.image_to_text_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that only output the answer to the question.",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe in detail the person in the image. Include their eye color, facial features (such as the shape of the eyes, nose, lips, and jawline), skin tone, and hair color and style. Mention any notable details such as freckles, dimples, facial hair, or makeup if present. The description should be precise, objective, and physically accurate.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url" : image_url},
                        },
                    ],
                },
            ],
        )
        return response.choices[0].message.content

    def generate(self, dialogue_file, images_nb, output_directory, person, age, image_url):
        os.makedirs(output_directory, exist_ok=True)
        with open(dialogue_file, "r") as f:
            dialogue = f.read()
        # Récupérer les points clés du dialogue
        print("Generating images...")
        print(f"Generating physical description of {person}...")
        person_description = self.__get_person_description(person, image_url)
        print(f"Generating most important points...")
        most_important_points = self.__get_most_important_points(dialogue, images_nb)
        match = re.search(r"\[.*?\]", most_important_points, re.DOTALL)
        if match:
            substring = match.group(0)
            important_point_parsed = ast.literal_eval(substring)
            for idx, point in enumerate(important_point_parsed):
                print(f"Generating image {idx+1} of {len(important_point_parsed)}")
                print("Improving image description...")
                point = self.__improve_description(point, person_description)
                print("Generating image...")
                output_filename = self.__generate_image(
                    point, age, output_directory=output_directory
                )
                print(f"Saved image to {output_filename}")
        else:
            print("Something went wrong while generating descriptions")
