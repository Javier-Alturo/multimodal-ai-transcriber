import re

from ollama import Client

OLLAMA_HOST = "http://127.0.0.1:11434"

SYSTEM_PROMPT_EN = """You are a friendly English tutor helping a Spanish-speaking student practice spoken English.

On every turn you MUST reply using exactly this format (plain text, no markdown):

CORRECTION: <one short line if they made a mistake, or NONE if their English was fine>
RESPONSE: <what you say out loud in English: brief correction if needed, then encouragement and a follow-up question>

Rules:
- RESPONSE must be under 70 words (it will be spoken aloud).
- Be warm and conversational, like a real teacher.
- If they spoke Spanish, understand them but encourage answering in English in your RESPONSE.
- CORRECTION line is for the console only; keep RESPONSE natural for speech.
- If there is ANY grammar, tense, word order, or vocabulary mistake, CORRECTION must state the fix (never write NONE when there is an error)."""

SYSTEM_PROMPT_ES = """Eres un profesor de espanol amable que ayuda a practicar espanol hablado.

En cada turno DEBES responder exactamente con este formato (texto plano, sin markdown):

CORRECCION: <una linea corta si cometieron un error, o NINGUNA si el espanol estuvo bien>
RESPUESTA: <lo que dices en voz alta en espanol: correccion breve si hace falta, animo y una pregunta de seguimiento>

Reglas:
- RESPUESTA maximo 70 palabras (se leera en voz alta).
- Se calido y conversacional, como un profesor de verdad.
- Todo en espanol (Espana o neutro latinoamericano).
- La linea CORRECCION es solo para la consola; RESPUESTA debe sonar natural al hablar.
- Si hay CUALQUIER error de gramatica, conjugacion, orden de palabras o vocabulario, CORRECCION debe indicar la forma correcta (nunca escribas NINGUNA si hay error)."""

PROMPTS = {"en": SYSTEM_PROMPT_EN, "es": SYSTEM_PROMPT_ES}

QUIT_WORDS = {"salir", "quit", "exit", "stop", "adios", "bye"}


def is_quit(text):
    return text.strip().lower() in QUIT_WORDS


def parse_teacher_reply(raw):
    correction = None
    response = raw.strip()

    corr_match = re.search(
        r"(?:CORRECTION|CORRECCION):\s*(.+?)(?=\n(?:RESPONSE|RESPUESTA):|\Z)",
        raw,
        re.DOTALL | re.IGNORECASE,
    )
    resp_match = re.search(r"(?:RESPONSE|RESPUESTA):\s*(.+)", raw, re.DOTALL | re.IGNORECASE)

    if corr_match:
        line = corr_match.group(1).strip()
        if line.upper() not in ("NONE", "NINGUNA", "N/A") and line:
            correction = line

    if resp_match:
        response = resp_match.group(1).strip()
    elif re.search(r"(?:RESPONSE|RESPUESTA):", raw, re.IGNORECASE):
        response = re.split(r"(?:RESPONSE|RESPUESTA):", raw, maxsplit=1, flags=re.IGNORECASE)[-1].strip()

    return correction, response


class EnglishTeacher:
    def __init__(self, model="llama3.2:latest", host=OLLAMA_HOST, language="es"):
        self.model = model
        self.client = Client(host=host)
        prompt = PROMPTS.get(language, SYSTEM_PROMPT_ES)
        self.history = [{"role": "system", "content": prompt}]

    def respond(self, student_text):
        self.history.append({"role": "user", "content": student_text})

        result = self.client.chat(
            model=self.model,
            messages=self.history,
            options={"temperature": 0.7, "num_predict": 200},
        )
        raw = result["message"]["content"]
        self.history.append({"role": "assistant", "content": raw})

        correction, spoken = parse_teacher_reply(raw)
        if not spoken:
            spoken = raw
        return correction, spoken
