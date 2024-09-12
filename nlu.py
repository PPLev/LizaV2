from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from transformers import AutoModel, AutoTokenizer
import numpy as np
import torch
from collections import Counter


class NLU:
    # cointegrated/LaBSE-en-ru - 0.7
    # cointegrated/roberta-base-formality - 0.97
    # cointegrated/rubert-tiny2 - 0.86
    def __init__(self, intents: dict, model_name='cointegrated/rubert-tiny2'):
        self.intents = intents
        self.example_vectors = []
        self.intent_names = []
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        self.update_intents()

    def embed_bert_cls(self, text):
        t = self.tokenizer(text, padding=True, truncation=True, max_length=128, return_tensors='pt')
        t = {k: v.to(self.model.device) for k, v in t.items()}
        with torch.no_grad():
            model_output = self.model(**t)
        embeddings = model_output.last_hidden_state[:, 0, :]
        embeddings = torch.nn.functional.normalize(embeddings)
        return embeddings[0].cpu().numpy()

    def classify_text(self, text, minimum_percent=0.0):
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


class NLU_SL:
    def __init__(self, intents: dict):
        self.intents = intents
        # Обучение матрицы на data_set модели
        self.vectorizer = CountVectorizer()
        self.vectors = self.vectorizer.fit_transform([i[1] for i in self._transform_intents()])

        self.clf = RandomForestClassifier()
        self.clf.fit(self.vectors, [i[0] for i in self._transform_intents()])

    def _transform_intents(self):
        data = []
        for intent, examples in self.intents.items():
            for example in examples:
                data.append([intent, example])

        return data

    def classify_text(self, text):
        text_vector = self.vectorizer.transform([text]).toarray()[0]
        answer = self.clf.predict([text_vector])[0]
        return answer

    def update_intents(self, new_intents: dict = None):
        if new_intents is not None:
            self.intents.update(new_intents)

        if not self.intents:
            return


if __name__ == '__main__':
    intents = {
        'how_are_you': ['как дела', 'как поживаешь', "какое у тебя настроение", "что ты чувствуешь"],
        'toast': ['я поднимаю стакан', 'пью до дна', 'за ваше здоровье'],
        'music': ['включи музыку', 'вруби шансон', 'хочу послушать музыку'],
        "lamp_on": ["включи лампу", "включи свет"],
        "lamp_off": ["выключи лампу", "выключи свет"],
        "tg_msg": ["сообщение телеграм", "напиши сообщение", "отправь в телеграм"],
    }
    nlu = NLU(intents=intents)
    rez = nlu.classify_text("напиши плопу как дела", minimum_percent=0.86)
    print(rez)
