conversations = {}


def get_history(chat_id):

    if chat_id not in conversations:
        conversations[chat_id] = []

    return conversations[chat_id]


def add_message(chat_id, role, content):

    history = get_history(chat_id)

    history.append(
        {
            "role": role,
            "content": content,
        }
    )

    conversations[chat_id] = history[-20:]