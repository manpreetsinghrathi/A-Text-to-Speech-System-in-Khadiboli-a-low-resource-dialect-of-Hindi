"""
Text-to-Speech for Khadi Boli
Free TTS - no API keys needed

Voices available:
  edge_tts (internet required, best quality):
    - hi-IN-MadhurNeural   (Male, natural)
    - hi-IN-SwaraNeural    (Female, natural)
  gTTS (internet required, good quality):
    - Google Hindi voice
  pyttsx3 (offline, medium quality):
    - Uses Windows system voices
"""

import re
import xml.etree.ElementTree as ET
import asyncio
import sys
import os
from gtts import gTTS
import edge_tts

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False


# ============ Config ============

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

EDGE_VOICES = {
    "1": ("hi-IN-MadhurNeural", "Male (Madhur)"),
    "2": ("hi-IN-SwaraNeural", "Female (Swara)"),
}


# ============ Text Normalization ============

_HI_ONES = ["", "एक", "दो", "तीन", "चार", "पाँच", "छह", "सात", "आठ", "नौ"]
_HI_TEENS = ["दस", "ग्यारह", "बारह", "तेरह", "चौदह", "पंद्रह", "सोलह", "सत्रह", "अठारह", "उन्नीस"]
_HI_TENS = ["", "", "बीस", "तीस", "चालीस", "पचास", "साठ", "सत्तर", "अस्सी", "नब्बे"]


def num_to_hindi(n):
    if n == 0:
        return "शून्य"
    parts = []
    if n >= 10000000:
        parts.append(num_to_hindi(n // 10000000) + " करोड़")
        n %= 10000000
    if n >= 100000:
        parts.append(num_to_hindi(n // 100000) + " लाख")
        n %= 100000
    if n >= 1000:
        parts.append(num_to_hindi(n // 1000) + " हज़ार")
        n %= 1000
    if n >= 100:
        parts.append(_HI_ONES[n // 100] + " सौ")
        n %= 100
    if n >= 20:
        parts.append(_HI_TENS[n // 10])
        n %= 10
    elif n >= 10:
        parts.append(_HI_TEENS[n - 10])
        n = 0
    if 0 < n < 10:
        parts.append(_HI_ONES[n])
    return " ".join(parts)


def normalize_text(raw_text):
    text = re.sub(r'₹(\d+)', lambda m: f"{num_to_hindi(int(m.group(1)))} रुपये", raw_text)
    text = re.sub(r'\b\d+\b', lambda m: num_to_hindi(int(m.group(0))), text)
    return text


# ============ XML/SSML Parsing ============

def parse_xml_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        xml_data = f.read()
    root = ET.fromstring(xml_data)
    sentences = []
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if elem.text and elem.text.strip() and tag not in ('phoneme', 'audio', 'prosody', 'emphasis', 'break'):
            sentences.append(elem.text.strip())
    return sentences


def split_sentences(text):
    return [s.strip() for s in re.split(r'[।?!]+', text) if s.strip()]


# ============ TTS Functions ============

def speak_with_gtts(text, output_file=None, lang="hi"):
    if output_file is None:
        output_file = os.path.join(OUTPUT_DIR, "output_gtts.mp3")
    tts = gTTS(text=text, lang=lang)
    tts.save(output_file)
    print(f"  gTTS: {output_file}")


async def speak_with_edge_tts(text, output_file=None, voice="hi-IN-MadhurNeural"):
    if output_file is None:
        output_file = os.path.join(OUTPUT_DIR, "output_edge.mp3")
    tts = edge_tts.Communicate(text, voice=voice)
    await tts.save(output_file)
    print(f"  edge_tts: {output_file}")


def speak_with_pyttsx3(text, output_file=None, rate=150):
    if output_file is None:
        output_file = os.path.join(OUTPUT_DIR, "output_pyttsx3.wav")
    engine = pyttsx3.init()
    engine.setProperty('rate', rate)
    for voice in engine.getProperty('voices'):
        if 'hindi' in voice.name.lower() or 'hi' in voice.id.lower():
            engine.setProperty('voice', voice.id)
            break
    engine.save_to_file(text, output_file)
    engine.runAndWait()
    print(f"  pyttsx3: {output_file}")


# ============ Main ============

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Read raw text
    raw_text_path = os.path.join(DATA_DIR, "raw_text.txt")
    with open(raw_text_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    print("=" * 50)
    print("  Khadi Boli Text-to-Speech")
    print("=" * 50)
    print()
    print(f"Raw Text: {raw_text.strip()}")
    print()

    # Normalize
    normalized = normalize_text(raw_text)
    print(f"Normalized: {normalized.strip()}")
    print()

    # Split sentences
    sentences = split_sentences(raw_text)
    print("Sentences:")
    for i, s in enumerate(sentences, 1):
        print(f"  {i}. {s}")
    print()

    # Parse XML
    xml_path = os.path.join(DATA_DIR, "sentence_01.xml")
    xml_sentences = parse_xml_file(xml_path)
    print("XML Sentences:")
    for s in xml_sentences:
        print(f"  - {s}")
    print()

    # Menu
    print("Choose TTS engine:")
    print("  1. gTTS (Google, needs internet)")
    print("  2. edge_tts (Microsoft Neural, needs internet)")
    print("  3. pyttsx3 (Offline, Windows voices)")
    print("  4. All")
    print()

    choice = input("Enter choice (1/2/3/4): ").strip()
    print()

    if choice in ("1", "4"):
        print("[gTTS]")
        speak_with_gtts(raw_text)

    if choice in ("2", "4"):
        print("[edge_tts]")
        voice_choice = input("Voice - 1=Male(Madhur), 2=Female(Swara) [default=1]: ").strip() or "1"
        voice_id, voice_name = EDGE_VOICES.get(voice_choice, EDGE_VOICES["1"])
        print(f"  Using: {voice_name}")
        try:
            asyncio.run(speak_with_edge_tts(raw_text, voice=voice_id))
        except Exception as e:
            print(f"  edge_tts failed: {e}")

    if choice in ("3", "4"):
        if HAS_PYTTSX3:
            print("[pyttsx3 - Offline]")
            speak_with_pyttsx3(raw_text)
        else:
            print("[pyttsx3] Not installed. Run: pip install pyttsx3")

    print()
    print("Done! Check the 'output' folder for audio files.")
