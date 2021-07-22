# from github nestauk/narrowing_ai_research/blob/master/narrowing_ai_research/utils/nlp.py

import re
import string
import nltk
from nltk.corpus import stopwords
from gensim import models
import numpy as np
import tqdm
import collections

#%% A mettre dans folder text

stop_words = set(
    stopwords.words("english") + list(string.punctuation) + ["\\n"] + ["quot"]
)

regex_str = [
    r"http[s]?://(?:[a-z]|[0-9]|[$-_@.&+]|" r"[!*\(\),](?:%[0-9a-f][0-9a-f]))+",
    r"(?:\w+-\w+){2}",
    r"(?:\w+-\w+)",
    r"(?:\\\+n+)",
    r"(?:@[\w_]+)",
    r"<[^>]+>",
    r"(?:\w+'\w)",
    r"(?:[\w_]+)",
    r"(?:\S)",
]

# Create the tokenizer which will be case insensitive and will ignore space.
tokens_re = re.compile(r"(" + "|".join(regex_str) + ")", re.VERBOSE | re.IGNORECASE)


def tokenize_document(text, remove_stops=False):
    """Preprocess a whole raw document.
    Args:
        text (str): Raw string of text.
        remove_stops (bool): Flag to remove english stopwords
    Return:
        List of preprocessed and tokenized documents
    """
    return [
        clean_and_tokenize(sentence, remove_stops)
        for sentence in nltk.sent_tokenize(text)
    ]


def clean_and_tokenize(text, remove_stops):
    """Preprocess a raw string/sentence of text.
    Args:
       text (str): Raw string of text.
       remove_stops (bool): Flag to remove english stopwords
    Return:
       tokens (list, str): Preprocessed tokens.
    """
    tokens = tokens_re.findall(text)
    _tokens = [t.lower() for t in tokens]
    filtered_tokens = [
        token.replace("-", "_")
        for token in _tokens
        if not (remove_stops and len(token) <= 2)
        and (not remove_stops or token not in stop_words)
        and not any(x in token for x in string.digits)
        and any(x in token for x in string.ascii_lowercase)
    ]
    return filtered_tokens


def make_ngram(tokenised_corpus, n_gram=2, threshold=10):
    """Extract bigrams from tokenised corpus
    Args:
        tokenised_corpus (list): List of tokenised corpus
        n_gram (int): maximum length of n-grams. Defaults to 2 (bigrams)
        threshold (int): min number of n-gram occurrences before inclusion
    Returns:
        ngrammed_corpus (list)
    """

    tokenised = tokenised_corpus.copy()
    t = 1
    # Loops while the ngram length less / equal than our target
    while t < n_gram:
        phrases = models.Phrases(tokenised, threshold=1)
        bigram = models.phrases.Phraser(phrases)
        tokenised = bigram[tokenised]
        t += 1
    return list(tokenised)

# from https://github.com/ddangelov/Top2Vec/blob/master/top2vec/Top2Vec.py
def _find_topic_words_and_scores(model,nb_words):
    topic_words = []
    topic_word_scores = []

    res = np.inner(model.topic_vectors, model._get_word_vectors())
    top_words = np.flip(np.argsort(res, axis=1), axis=1)
    top_scores = np.flip(np.sort(res, axis=1), axis=1)

    for words, scores in zip(top_words, top_scores):
        topic_words.append([model._index2word(i) for i in words[0:nb_words]])
        topic_word_scores.append(scores[0:nb_words])

    topic_words = np.array(topic_words)
    topic_word_scores = np.array(topic_word_scores)

    return topic_words, topic_word_scores

def get_topic_dist(model,doc,cos_threshold,nb_word_threshold):
    n = 0
    words = doc.split(' ')
    topic_list = []
    for word in words:
        try :
            cos_sim, topic_idx = model.search_topics([word],1)[2:]
            if cos_sim > cos_threshold:
                topic_list.append(int(topic_idx))
                n+=1
        except :
            pass
        
    topic_count = collections.Counter(topic_list)
    
    
    topic_dist = np.repeat(0,model.get_num_topics())
    for topic in topic_count:
        if topic_count[topic] > nb_word_threshold:
            topic_dist[int(topic)] = topic_count[topic] 
    
    return topic_dist/topic_dist.sum()
    
    
        