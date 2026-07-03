import ollama

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Sen HeyKanka isimli samimi bir Türkçe AI asistansın. "
        "Kullanıcıya gerektiğinde 'kanka' diye hitap et. "
        "Kısa, net ve yardımcı cevaplar ver."
    ),
}


def ask_ai(history):

    messages = [SYSTEM_PROMPT] + history

    response = ollama.chat(
        model="gemma3:12b",
        messages=messages,
    )

    return response["message"]["content"]