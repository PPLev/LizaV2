from transformers import AutoModel, AutoTokenizer
import numpy as np
import torch
from collections import Counter


class NLU:
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

    def classify_text(self, text):
        vector = self.embed_bert_cls(text)
        scores = np.dot(self.example_vectors, vector)
        result = Counter()
        for score, intent in zip(scores, self.intent_names):
            result[intent] = max(result[intent], score)
        return result.most_common()

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


if __name__ == '__main__':
    intents = {
        'how_are_you': ['как дела', 'как поживаешь'],
        'toast': ['я поднимаю стакан', 'пью до дна', 'за ваше здоровье'],
        'music': ['включи музыку', 'вруби шансон', 'хочу послушать музыку'],
        "lamp_on": ["включи лампу"],
        "lamp_off": ["выключи лампу"],
        "tg_msg": ["сообщение телеграм"],
    }
    nlu = NLU(intents=intents)
    print(nlu.classify_text("Напиши сообщение Мадине в телеграм с текстом как дела"))
