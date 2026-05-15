def generate():
    return [
        "Привет\nМеня зовут Алексей\nНапомни моё имя.\nвыход\n",
        "Привет\nМеня зовут Ирина\nНапомни моё имя.\nвыход\n",
        "Здравствуй\nКак меня зовут?\nМеня зовут Павел\nНапомни моё имя\nвыход\n",
        "Привет\nНапомни моё имя.\nвыход\n",
        "Привет\nМеня зовут Джон\nНапомни моё имя.\nвыход\n",
        "выход\n"
    ]


def solve(dataset):
    lines = dataset.splitlines()
    replies = []
    name = None
    for line in lines:
        msg = line.lower()
        if "меня зовут" in msg:
            name = line.split()[-1].strip(".!?,")
            replies.append(f"Приятно познакомиться, {name}! 😊")
        elif "напомни моё имя" in msg:
            if name:
                replies.append(f"Вы представились как {name}.")
            else:
                replies.append("Вы не представились.")
        elif msg in ("выход", "exit", "quit"):
            replies.append("До свидания!")
        else:
            replies.append("Чем могу помочь?")
    return "\n".join(replies)


def check(reply, clue):
    reply = reply.strip()
    clue = clue.strip()
    if reply == clue:
        return True
    feedback = f"Ожидалось:\n{clue}\n\nПолучено:\n{reply}"
    return False, feedback