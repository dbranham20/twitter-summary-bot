from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
import numpy as np
import networkx as nx
import re

def organize_tweets(tweets_list):
    article=[]
    for tweet in tweets_list:
        for sentence in tweet.split(". "):
            withOutLinks = re.sub(r'http\S+', '', sentence)
            article.append(withOutLinks)

    sentences = []
    for sentence in article:
        sentences.append(sentence.replace("[^a-zA-Z]", " ").split(" "))
    sentences.pop() 
    
    return sentences

def sentence_similarity(sent1, sent2, stopwords=None):
    if stopwords is None:
        stopwords = []
 
    sent1 = [w.lower() for w in sent1]
    sent2 = [w.lower() for w in sent2]
 
    all_words = list(set(sent1 + sent2))
 
    vector1 = [0] * len(all_words)
    vector2 = [0] * len(all_words)
 
    for w in sent1:
        if w in stopwords:
            continue
        vector1[all_words.index(w)] += 1
 
    for w in sent2:
        if w in stopwords:
            continue
        vector2[all_words.index(w)] += 1
 
    return 1 - cosine_distance(vector1, vector2)
 
def build_similarity_matrix(sentences, stop_words):
    similarity_matrix = np.zeros((len(sentences), len(sentences)))
 
    for idx1 in range(len(sentences)):
        for idx2 in range(len(sentences)):
            if idx1 == idx2: #ignore if both are same sentences
                continue 
            similarity_matrix[idx1][idx2] = sentence_similarity(sentences[idx1], sentences[idx2], stop_words)

    return similarity_matrix

def build_summary_tweets(ranked_sentences, tweet_limit):
    char_limit = 280
    current_chars = 0
    summary_tweets = []
    summary_text = "SUMMARY: "
    for sentence in ranked_sentences:
        if len(sentence[1]) > 1:
            fullSentence = " ".join(sentence[1])
            if len(summary_tweets) < tweet_limit:
                if (current_chars + len(fullSentence)) > char_limit:
                    summary_tweets.append(summary_text)
                    summary_text = fullSentence
                    current_chars = 0
                else:
                    summary_text += fullSentence
                    current_chars += len(fullSentence)
            else:
                return summary_tweets

def generate_summary(tweets_list, tweet_limit):
    stop_words = stopwords.words('english')

    sentences =  organize_tweets(tweets_list)
    sentence_similarity_martix = build_similarity_matrix(sentences, stop_words)
    sentence_similarity_graph = nx.from_numpy_array(sentence_similarity_martix)
    scores = nx.pagerank(sentence_similarity_graph)
    ranked_sentence = sorted(((scores[i],s) for i,s in enumerate(sentences)), reverse=True)    

    # Step 5 - Offcourse, output the summarize texr
    return build_summary_tweets(ranked_sentence, tweet_limit)
