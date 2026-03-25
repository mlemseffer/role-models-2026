import os
import re
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, vfx

def extract_number(filename):
    match = re.search(r'img_gen(\d+)\.webp', filename)
    return int(match.group(1)) if match else float('inf')

class VideoGenerator:

    def generate(self, images_dir, audio_path, fade_duration = 2.0, fps = 24, output_path="./output_video.mp4"):
        os.makedirs(output_path.rsplit("/", 1)[0] + "/", exist_ok=True)
        print("Generating video...")
        print("Fetching images...")
        images = [f for f in os.listdir(images_dir) if re.match(r'img_gen\d+\.png$', f)]
        images = sorted(images, key=extract_number)
        images = [os.path.join(images_dir, f) for f in images]
        audio = AudioFileClip(audio_path)
        clips = [ImageClip(img_path).with_duration(audio.duration / len(images)).with_effects([vfx.CrossFadeIn(fade_duration), vfx.CrossFadeOut(fade_duration)]).with_start(i * ((audio.duration / len(images)) - fade_duration)) for i, img_path in enumerate(images)]
        CompositeVideoClip(clips).with_fps(fps).with_audio(audio).write_videofile(output_path)
        print(f"Video saved to {output_path}")
