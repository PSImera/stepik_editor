import random
import math
from collections import defaultdict


def _build_cooccurrence(corpus, vocab):
    word_to_idx = {w: i for i, w in enumerate(vocab)}
    n = len(vocab)
    matrix = [[0.0] * n for _ in range(n)]

    for sentence in corpus:
        words = sentence.strip().split()
        for i, word in enumerate(words):
            if word not in word_to_idx:
                continue
            if i > 0 and words[i - 1] in word_to_idx:
                a, b = word_to_idx[word], word_to_idx[words[i - 1]]
                matrix[a][b] += 1
                matrix[b][a] += 1
    return matrix


def _cosine(v1, v2):
    dot = sum(a * b for a, b in zip(v1, v2))
    n1 = math.sqrt(sum(a ** 2 for a in v1))
    n2 = math.sqrt(sum(b ** 2 for b in v2))
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)


def generate():
    tests = []

    # Тест 1: пример из условия
    tests.append("кот спит\nкот ест\nсобака ест\nсобака\n")

    # Тест 2: простой — два слова-синонима по контексту
    tests.append("кот мяукает\nкошка мяукает\nсобака лает\nкот\n")

    # Тест 3: три слова, одно явно ближе
    tests.append("python программирование\njava программирование\npython код\njava\n")

    # Тест 4: все слова в одном предложении
    tests.append("а б в г\nа б в д\nа\n")

    # Тест 5: запрос стоит в начале предложений
    tests.append("кот спит дома\nкот ест рыбу\nпёс спит дома\nпёс\n")

    # Тест 6: длинный корпус, явные кластеры
    corpus = [
        "машина едет быстро",
        "автобус едет медленно",
        "машина стоит",
        "велосипед едет медленно",
        "автобус стоит",
    ]
    tests.append("\n".join(corpus) + "\nмашина\n")

    # Тест 7: слова встречаются в разных позициях
    tests.append("солнце светит ярко\nлуна светит ночью\nзвезда светит ночью\nсолнце\n")

    # Тест 8: минимальный корпус — два предложения по два слова
    tests.append("день ночь\nутро день\nночь\n")

    # Тесты 9-15: случайные корпуса из коротких предложений
    word_pool = ["alpha", "beta", "gamma", "delta", "epsilon",
                 "zeta", "eta", "theta", "iota", "kappa"]
    for _ in range(7):
        random.shuffle(word_pool)
        chosen = word_pool[:6]
        sentences = []
        for _ in range(4):
            length = random.randint(2, 4)
            sentence = " ".join(random.choices(chosen, k=length))
            sentences.append(sentence)
        query = random.choice(chosen)
        # убедимся что query есть в корпусе
        sentences.append(f"{query} {random.choice(chosen)}")
        test = "\n".join(sentences) + f"\n{query}\n"
        tests.append(test)

    return tests


def solve(dataset):
    lines = dataset.strip().splitlines()
    query = lines[-1]
    corpus = lines[:-1]

    vocab = sorted(set(w for sent in corpus for w in sent.split()))
    word_to_idx = {w: i for i, w in enumerate(vocab)}
    n = len(vocab)

    matrix = [[0.0] * n for _ in range(n)]
    for sentence in corpus:
        words = sentence.strip().split()
        for i, word in enumerate(words):
            if word not in word_to_idx:
                continue
            if i > 0 and words[i - 1] in word_to_idx:
                a, b = word_to_idx[word], word_to_idx[words[i - 1]]
                matrix[a][b] += 1
                matrix[b][a] += 1

    if query not in word_to_idx:
        return ""

    q_vec = matrix[word_to_idx[query]]
    best_word = None
    best_score = -2.0

    for word in vocab:
        if word == query:
            continue
        score = _cosine(q_vec, matrix[word_to_idx[word]])
        if score > best_score or (score == best_score and (best_word is None or word < best_word)):
            best_score = score
            best_word = word

    return best_word if best_word else ""


def check(reply, clue):
    reply = reply.strip()
    clue = clue.strip()

    if reply == clue:
        return True

    return False, f"Ожидалось: '{clue}', получено: '{reply}'"