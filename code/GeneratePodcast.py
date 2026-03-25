import time
from logging import error
from google import genai
from google.genai import types
import wave
import os


class GeneratePodcast:
    def __init__(
        self,
        gemini_api_key,
        teacher_voice="Erinome",
        student_voice="Rasalgethi",
        model="gemini-2.5-flash-preview-tts",
    ):
        self.dialogues = []

        self.teacher_voice = teacher_voice
        self.student_voice = student_voice

        # id's of the voices to use for each type of voice and provider
        self.__progress_filename = "progress_save.ps"

        self.model = model
        self.gemini = genai.Client(api_key=gemini_api_key)

    def __current_milli_time(self):
        return round(time.time() * 1000)

    def __parse_file(self, filename):
        # Tuple (VoiceType, text)
        voices_and_replies = list()

        with open(filename, "r") as f:
            for line in f:
                self.dialogues.append(line)
                splited_line = line.split(":")
                voices_and_replies.append(
                    (splited_line[0].strip(), splited_line[1].strip())
                )

        return voices_and_replies

    def __parse_progress_dialogues(self, dialogues):
        # Tuple (VoiceType, text)
        voices_and_replies = list()

        for line in dialogues:
            self.dialogues.append(line)
            splited_line = line.split(":")
            voices_and_replies.append(
                (splited_line[0].strip(), splited_line[1].strip())
            )

        return voices_and_replies

    def __generate_dialogue(self, replies_with_voices):
        audio_segments = []
        for idx, reply in enumerate(replies_with_voices):
            feedback_line = (
                "Generating reply "
                + str(idx + 1)
                + " of "
                + str(len(replies_with_voices))
                + "..."
            )
            print(feedback_line.ljust(2, " "), end="\n")
            try:
                response = self.gemini.models.generate_content(
                    model=self.model,
                    contents=reply[1],
                    config=types.GenerateContentConfig(
                        temperature=2,
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=(
                                        self.teacher_voice
                                        if reply[0] == "TEACHER_F"
                                        else self.student_voice
                                    )
                                )
                            )
                        ),
                    ),
                )
                if idx != 0 and (idx + 1) % 4 == 0:
                    print("Sleeping...")
                    time.sleep(30)
            except:
                self.__add_new_line_to_progress()
                self.__add_strings_to_progress(self.dialogues[idx:])

                self.__add_replica_count_to_progress(len(replies_with_voices) - idx)

                raise Exception(
                    "TTS could not be generated entirely, progress has been saved in file "
                    + self.__progress_filename
                )

            candidate = response.candidates[0] if response.candidates else None

            if (
                not candidate
                or not candidate.content
                or not hasattr(candidate.content, "parts")
            ):
                print(f"Warning: No content in response for dialogue {idx}")
                continue

            part = candidate.content.parts[0] if candidate.content.parts else None

            if not part or not hasattr(part, "inline_data") or not part.inline_data:
                print(f"Warning: No inline_data for dialogue {idx}")
                continue

            if not hasattr(part.inline_data, "data") or not part.inline_data.data:
                print(
                    f"Warning: inline_data has no 'data' attribute for dialogue {idx}"
                )
                continue
            else:
                data = part.inline_data.data
                self.__add_audio_segment_to_progress(data)
                audio_segments.append(data)
        return audio_segments

    def __save_audio(
        self, audio_segments, output_filename, channels=1, rate=24000, sample_width=2
    ):
        concat_audio = b""

        for segment in audio_segments:
            concat_audio += segment
        out = output_filename + str(self.__current_milli_time()) + ".wav"
        with wave.open(out, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(concat_audio)
        return out

    def generate(
        self,
        input_filename,
        output_filename,
        replies_with_voices=None,
        audio_segments=None,
    ):
        assert (replies_with_voices == None) == (audio_segments == None)

        if replies_with_voices == None:
            self.__init_progress_file()
            self.__add_string_to_progress("GEMINI")
            replies_with_voices = self.__parse_file(input_filename)
        if audio_segments == None:
            audio_segments = []

        out = None
        print("Generating dialogue using Gemini...")
        audio_segments.extend(self.__generate_dialogue(replies_with_voices))
        print("Done")
        print(f"Saving in {output_filename}...")
        out = self.__save_audio(audio_segments, output_filename=output_filename)

        return out

    def __init_progress_file(self, progress_filename=None):
        progress_dir = "../generated/progress"
        os.makedirs(progress_dir, exist_ok=True)
        if progress_filename is None:
            self.__progress_filename = os.path.join(
                progress_dir, "tts_progress" + str(self.__current_milli_time()) + ".pgs"
            )
        else:
            self.__progress_filename = os.path.join(progress_dir, progress_filename)

    def __add_replica_count_to_progress(self, count):

        with open(self.__progress_filename, "ab") as f:
            f.write(int.to_bytes(count))

    def __add_string_to_progress(self, line):
        with open(self.__progress_filename, "ab") as f:
            f.write(line.encode("utf-8"))
            f.write(b"\n")

    def __add_strings_to_progress(self, lines):
        with open(self.__progress_filename, "ab") as f:
            for line in lines:
                f.write(line.encode("utf-8"))

    def __add_new_line_to_progress(self):
        with open(self.__progress_filename, "ab") as f:
            f.write(b"\n")

    def __add_audio_segment_to_progress(self, audio_segment):
        with open(self.__progress_filename, "ab") as f:
            f.write(audio_segment)

    def __add_audio_segments_to_progress(self, audio_segments):
        with open(self.__progress_filename, "ab") as f:
            for seg in audio_segments:
                f.write(seg)

    def resume_from_progress_file(
        self, progress_filename, input_filename, output_filename
    ):
        with open(progress_filename, "rb") as f:
            lines = f.readlines()
        count = int.from_bytes(lines[-1])
        dialogues = [line.decode("utf-8") for line in lines[-1 - count : -1]]
        audio_segments = lines[1 : -1 - count]
        if audio_segments != []:
            audio_segments[-1] = audio_segments[-1][0:-1]
        self.__init_progress_file()
        self.__add_string_to_progress("GEMINI")

        replies_with_voices = self.__parse_progress_dialogues(dialogues)
        self.__add_audio_segments_to_progress(audio_segments)
        out = self.generate(
            replies_with_voices=replies_with_voices,
            audio_segments=audio_segments,
            input_filename=input_filename,
            output_filename=output_filename,
        )
        return out
