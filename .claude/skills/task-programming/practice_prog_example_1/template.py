::python3
::header

# ==== Имитация фреймворка LangChain / LangGraph ====

class Message:
    """Эмуляция объекта сообщения LangChain"""
    def __init__(self, role, content):
        self.role = role
        self.content = content


class InMemorySaver:
    """Эмуляция InMemorySaver — хранение сообщений по thread_id"""
    def __init__(self):
        self.memory = {}

    def add_message(self, thread_id, role, content):
        if thread_id not in self.memory:
            self.memory[thread_id] = []
        self.memory[thread_id].append(Message(role, content))

    def get_messages(self, thread_id):
        return self.memory.get(thread_id, [])


class Agent:
    """Простой агент с памятью"""
    def __init__(self, model, checkpointer):
        self.model = model
        self.checkpointer = checkpointer
        self.name = None

    def invoke(self, data, config):
        thread_id = config["configurable"]["thread_id"]
        user_message = data["messages"][-1]["content"]

        # Сохраняем вход
        self.checkpointer.add_message(thread_id, "user", user_message)
        messages = self.checkpointer.get_messages(thread_id)
        
        # Проверка корректности модели
        if self.model != "gpt-5":
            raise ValueError("Используйте модель gpt-5")

        # Эмуляция поведения модели
        if "меня зовут" in user_message.lower():
            self.name = user_message.split()[-1].strip(".!?,")
            reply = f"Приятно познакомиться, {self.name}! 😊"
        elif "напомни моё имя" in user_message.lower():
            reply = f"Вы представились как {self.name}." if self.name else "Вы не представились."
        elif user_message.lower() in ("выход", "exit", "quit"):
            reply = "До свидания!"
        else:
            reply = "Чем могу помочь?"

        # Сохраняем ответ
        self.checkpointer.add_message(thread_id, "assistant", reply)
        return {"messages": [Message("assistant", reply)]}


def create_agent(model, checkpointer):
    """Имитация функции create_agent"""
    return Agent(model, checkpointer)

::code
def solution():
    # ==== Ваш код тут ====

::footer
solution()