def most_similar(corpus, query):
    """Находит ближайшее слово по матрице совместной встречаемости."""
    # Словарь в алфавитном порядке — обеспечивает воспроизводимость
    vocab = sorted(set(w for sent in corpus for w in sent.split()))
    word_to_idx = {w: i for i, w in enumerate(vocab)}
    n = len(vocab)

    # Строим матрицу: для каждой соседней пары слов добавляем +1 симметрично
    matrix = np.zeros((n, n))
    for sentence in corpus:
        words = sentence.split()
        for i in range(1, len(words)):
            a, b = word_to_idx.get(words[i]), word_to_idx.get(words[i - 1])
            if a is not None and b is not None:
                matrix[a, b] += 1
                matrix[b, a] += 1

    # Вектор запроса и его норма
    q_vec = matrix[word_to_idx[query]]
    q_norm = np.linalg.norm(q_vec)

    best_word, best_score = None, -2.0
    for word in vocab:
        if word == query:
            continue
        v = matrix[word_to_idx[word]]
        v_norm = np.linalg.norm(v)
        # Нулевой вектор — слово ни с чем не соседствовало
        score = float(np.dot(q_vec, v) / (q_norm * v_norm)) if q_norm and v_norm else 0.0
        if score > best_score or (score == best_score and (best_word is None or word < best_word)):
            best_score, best_word = score, word

    return best_word