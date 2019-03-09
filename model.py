import random
import pickle
import pandas as pd
from string import punctuation
from collections import defaultdict

import config

TOP_N = 100
K = 10

english_vocab = pickle.load(open(config.ENGLISH_VOCAB, "rb"))
stopword = pickle.load(open(config.STOPWORD, "rb"))


def change_vocab(model):
    word_vocab = model.vocab
    word_vectors = model.wv

    map_word_to_frequency = {}
    for k, v in word_vocab.items():
        map_word_to_frequency[k] = v.count
    small_vocab = {}
    for k, v in map_word_to_frequency.items():
        if k in english_vocab:
            small_vocab[k] = v
    new_vocab = {}
    for k, v in small_vocab.items():
        new_vocab[k] = model.vocab[k]
    model.vocab = new_vocab


def clean_input(input_string):
    # Remove punctuations:
    no_punc = input_string.translate(str.maketrans('', '', punctuation))
    # Split and remove stopwords
    processed = [word for word in no_punc.split() if word not in stopword]
    return processed


def clean_result(res, no):
    cleaned = set()
    for k, v in res:
        k = k.replace('_', ' ').lower()
        merged = k.replace(' ', '')
        if merged.isalpha():
            cleaned.add(k.replace(' ', '_'))
        # if not k.isalpha():
        #     k = regex.sub('', k)
        # cleaned.add(k.replace('_', ' '))
    words = random.sample(cleaned, no)
    return words


def get_suggestions(word, processed_fix_keywords, model):
    # key_words.append(word)
    result = model.most_similar(word, topn=TOP_N)
    if word in processed_fix_keywords:
        words = [word] * K
    else:
        words = clean_result(res=result, no=K)
    return words


def word2vec_predict_sentence_with_fixed_keywords(sentence, fix_keywords, model):
    processed_sentence = clean_input(sentence)
    processed_fix_keywords = clean_input(fix_keywords)
    map_word_to_suggestions = defaultdict(list)
    key_words = []

    for word in processed_sentence:
        # Turn word to lower case:
        lowered = word.lower()
        # Get capitalized word
        capitalized = word.capitalize()
        if lowered in model.vocab:
            key_words.append(word)
            words = get_suggestions(word, processed_fix_keywords, model)
            map_word_to_suggestions[word] = words
        elif capitalized in model.vocab:
            key_words.append(word)
            words = get_suggestions(capitalized, processed_fix_keywords, model)
            map_word_to_suggestions[word] = words

    shuffled = []
    for suggestion in list(map_word_to_suggestions.values()):
        shuffled.append(random.sample(suggestion, len(suggestion)))
    random_com = []
    for i in range(10):
        this_com = [x[i] for x in shuffled]
        random_com.append(this_com)

    suggestion_df = pd.DataFrame(map_word_to_suggestions)
    df_html = suggestion_df.to_html(classes='table', escape=True, border=0, justify='center')
    return key_words, df_html, random_com


# def word2vec_predict_sentence(sentence, model):
#     no_punc = sentence.translate(str.maketrans('', '', punctuation))
#     processed = [word for word in no_punc.split() if word not in stopword]
#     map_word_to_suggestions = defaultdict(list)
#     key_words = []
#     for word in processed:
#         if word[0].isupper():
#             swap = word.lower()
#         else:
#             swap = word.upper()
#         if word in model.vocab:
#             key_words.append(word)
#             result = model.most_similar(word, topn=TOP_N)
#             words = clean_result(res=result, no=K)
#             map_word_to_suggestions[word] = words
#         elif swap in model.vocab:
#             key_words.append(word)
#             result = model.most_similar(swap, topn=TOP_N)
#             words = clean_result(res=result, no=K)
#             map_word_to_suggestions[swap] = words
#
#     shuffled = []
#     for suggestion in list(map_word_to_suggestions.values()):
#         shuffled.append(random.sample(suggestion, len(suggestion)))
#     random_com = []
#     for i in range(10):
#         this_com = [x[i] for x in shuffled]
#         random_com.append(this_com)
#
#     suggestion_df = pd.DataFrame(map_word_to_suggestions)
#     df_html = suggestion_df.to_html(classes='table', escape=True, border=0, justify='center')
#     return key_words, df_html, random_com


# def word2vec_predict_simple(sentence):
#     # titles = ['cat', 'hello']
#     # rows = [['dog', 'hi'], ['lion', 'goodbye'], ['tiger', 'yo'], ['pig', 'welcome']]
#     # return titles, rows
#     # return {'cat': ['dog', 'lion', 'tiger', 'pig'], 'hello': ['hi', 'goodbye', 'yo', 'welcome']}
#     df = pd.DataFrame({'cat': ['dog', 'lion', 'tiger', 'pig'],
#                        'hello': ['hi', 'goodbye', 'yo', 'welcome'],
#                        'christmas': ['xmas', 'holiday', 'Noel', 'Santa']})
#     df_html = df.to_html(classes='table', escape=True, border=0, justify='center')
#     random_com = [['dog', 'hi', 'xmas'], ['lion', 'goodbye', 'holiday']]
#     return df_html, random_com

