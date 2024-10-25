# from sklearn.ensemble import RandomForestClassifier
# from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
# from sklearn.linear_model import LogisticRegression
# from sklearn.neighbors import KNeighborsClassifier
import logging

from transformers import AutoModel, AutoTokenizer
import numpy as np
import torch
from collections import Counter
logger = logging.getLogger(__name__)

class NLU:
    # cointegrated/LaBSE-en-ru - 0.7
    # cointegrated/roberta-base-formality - 0.97
    # cointegrated/rubert-tiny2 - 0.86
    # cointegrated/rubert-tiny2-sentence-compression - 0.68
    def __init__(self, intents: dict, model_name='cointegrated/rubert-tiny2-sentence-compression'):
        self.intents = intents
        self.example_vectors = []
        self.intent_names = []
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        self.update_intents()

    def embed_bert_cls(self, text):
        t = self.tokenizer(text, padding=True, truncation=True, max_length=6, return_tensors='pt')
        t = {k: v.to(self.model.device) for k, v in t.items()}
        with torch.no_grad():
            model_output = self.model(**t)
        embeddings = model_output.last_hidden_state[:, 0, :]
        embeddings = torch.nn.functional.normalize(embeddings)
        return embeddings[0].cpu().numpy()

    def classify_text(self, text, minimum_percent=0.0):
        intent = list(filter(lambda i: text in self.intents[i], self.intents.keys()))
        if len(intent):
            return [intent[0], 1.0]

        vector = self.embed_bert_cls(text)
        scores = np.dot(self.example_vectors, vector)
        result = Counter()
        for score, intent in zip(scores, self.intent_names):
            result[intent] = max(result[intent], score)
        return [i for i in result.most_common() if i[1] >= minimum_percent]

    def update_intents(self, new_intents: dict = None):
        if new_intents is not None:
            self.intents.update(new_intents)

        if not self.intents:
            return

        for intent, texts in self.intents.items():
            for text in texts:
                self.example_vectors.append(self.embed_bert_cls(text))
                self.intent_names.append(intent)
        self.example_vectors = np.stack(self.example_vectors)

        logger.info(f'Updated {self.intents.keys()}')

#
# class NLU_SL:
#     def __init__(self, intents: dict):
#         self.intents = intents
#         # Обучение матрицы на data_set модели
#         self.vectorizer = TfidfVectorizer()
#         self.vectors = self.vectorizer.fit_transform([i[0] for i in self._transform_intents()])
#
#         self.clf = KNeighborsClassifier(n_neighbors=3)
#         self.clf.fit(self.vectors, [i[1] for i in self._transform_intents()])
#
#     def _transform_intents(self):
#         data = []
#         for intent, examples in self.intents.items():
#             for example in examples:
#                 data.append([example, intent])
#
#         return data
#
#     def classify_text(self, text):
#         text_vector = self.vectorizer.transform([text]).toarray()[0]
#         answer = self.clf.predict_proba([text_vector])
#         return answer[0]
#
#     def update_intents(self, new_intents: dict = None):
#         if new_intents is not None:
#             self.intents.update(new_intents)
#
#         if not self.intents:
#             return


if __name__ == '__main__':
    intents = {
        "add_calendar": ["запомни какое-то событие", "запиши что мне надо", "добавь событие о чем-то", "напомни мне об этом позже", "напомни через час полить цветы"],
        "get_calendar": ["напомни когда произойдет это", "скажи когда произойдет что-то", "через сколько дней будет это"],
        'music_d': ["сделай музыку тише", "уменьши громкость воспроизведения", "сделай звук тише"],
        'music_u': ["сделай музыку громче", "увелич громкость музыки", "сделай воспроизведение громче"],
        'music_pp': ["останови воспроизведение музыки", "останови воспроизведение", "сотановить музыку", "поставь воспроизведение музыки на паузу"],
        "check_upd": ["проверь есть ли обновления", "узнай есть ли новая версия", "проверь наличие новой версии"],
        "run_upd": ["выключи лампу", "выключи свет"],
    }
    nlu = NLU(intents=intents)
    rez = nlu.classify_text("напомни завтра вечером покормить кошку")
    print(rez)
