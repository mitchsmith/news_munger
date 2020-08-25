#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Robot voices from google text to speech api """

from google.cloud import texttospeech as tts


def list_voices(language_code=None):

    """Retrieve a list of available voices. """
    client = tts.TextToSpeechClient()
    response = client.list_voices(language_code=language_code)
    voices = sorted(response.voices, key=lambda voice: voice.name)
    print(f" Voices: {len(voices)} ".center(60, "-"))

    for voice in voices:
        languages = ", ".join(voice.language_codes)
        name = voice.name
        gender = tts.SsmlVoiceGender(voice.ssml_gender).name
        rate = voice.natural_sample_rate_hertz
        print(
            f"{languages:<8}", f"{name:<24}", f"{gender:<8}", f"{rate:,} Hz", sep=" | "
        )


def text_to_mp3(voice_name, text):

    """Read out the given text in the given voice and write it to a file. """
    language_code = "-".join(voice_name.split("-")[:2])
    text_input = tts.SynthesisInput(text=text)
    voice_params = tts.VoiceSelectionParams(
        language_code=language_code, name=voice_name
    )
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.MP3)
    client = tts.TextToSpeechClient()
    response = client.synthesize_speech(
        input=text_input, voice=voice_params, audio_config=audio_config
    )
    filename = f"{language_code}.mp3"

    with open(filename, "wb") as out:
        out.write(response.audio_content)
        print(f'Audio content written to "{filename}"')
