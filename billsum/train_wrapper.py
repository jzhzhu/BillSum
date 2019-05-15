'''
Wrapper to train and evaluate a supervised model
'''
from billsum.classifiers.classifier_scorer import TextScorer
from billsum.post_process import greedy_summarize, mmr_selection
from billsum.utils.sentence_utils import list_to_doc

import numpy as np
import pandas as pd
import pickle

from rouge import Rouge
rouge = Rouge()

prefix = '/Users/anastassiakornilova/BSDATA/'


##########     Load in the data ###############
us_train = pd.read_json(prefix + 'clean_final/us_train_data_final.jsonl', lines=True)
us_train.set_index('bill_id', inplace=True)
us_train_sents = pickle.load(open(prefix + 'sent_data/us_train_sent_scores.pkl', 'rb'))
us_train_summary = pickle.load(open(prefix + 'clean_final/us_train_summary_sents.pkl', 'rb'))

final_train = {}
for bill_id, sents in us_train_sents.items():

    doc = [v[1] for v in sents]
    
    scores = [v[2] for v in sents]
    
    sent_texts = [v[0] for v in sents]

    summary = us_train.loc[bill_id]['clean_summary']

    title = us_train.loc[bill_id]['clean_title']

    mysum = us_train_summary[bill_id]

    final_train[bill_id] = {'doc': doc, 'scores': scores, 'sum_text': summary, 
                             'sent_texts': sent_texts, 'title': title, 'sum_doc': mysum}

del us_train, us_train_sents, us_train_summary

######## Train a model ###################

model = FeatureScorer()
model.train(final_train.values())

pickle.dump(model, open('feature_scorer_model.pkl', 'wb'))


######### Evaluate Performance ################

for locality in ['us', 'ca']:

    test_data = pd.read_json(prefix + 'clean_final/{}_test_data_final.jsonl'.format(locality), lines=True)
    test_data.set_index('bill_id', inplace=True)
    test_sents = pickle.load(open(prefix + 'sent_data/{}_test_sent_scores.pkl'.format(locality), 'rb'))

    final_test = {}
    for bill_id, sents in test_sents.items():

        doc = [v[1] for v in sents]
        
        scores = [v[2] for v in sents]
        
        sent_texts = [v[0] for v in sents]

        summary = test_data.loc[bill_id]['clean_summary']

        title = test_data.loc[bill_id]['clean_title']

        final_test[bill_id] = {'doc': doc, 'scores': scores, 'sum_text': summary, 
                               'sent_texts': sent_texts, 'title': title, 
                               'textlen': len(test_data.loc[bill_id]['text'])}

    del test_data, test_sents, us_test_summary

    # Summarizer
    final_scores = {}
    for bill_id, doc in final_test.items():
        
        scores = model.score_doc(doc)

        final_sum = ' '.join(mmr_selection(doc['sent_texts'], scores, 13333))

        rs = rouge.get_scores([final_sum],[doc['sum_text']])[0]

        final_scores[bill_id] = rs

    pickle.dump(final_scores, open('{}_test_feature_model_res.pkl'.format(locality), 'wb'))

