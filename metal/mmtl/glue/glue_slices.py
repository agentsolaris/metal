import json
import os
import warnings

import numpy as np
import spacy
import torch

from metal.utils import convert_labels

question_words = set(["who", "what", "where", "when", "why", "how"])
nlp = spacy.load("en_core_web_sm")


def BASE(dataset, idx):
    # Always returns True -- used to train a copy fo the base_labelset
    # NOTE/HACK: MUST be named "BASE" to match task definition
    return True


def get_both_sentences(dataset, idx):
    if len(dataset.sentences[idx]) > 1:
        return dataset.sentences[idx][0] + " " + dataset.sentences[idx][1]
    else:
        return dataset.sentences[idx][0]


def more_people(dataset, idx):
    people = 0
    sentence = dataset.sentences[idx][0].split()
    for pronoun in ["she", "her", "hers"]:
        if pronoun in sentence:
            people += 1
            break
    for pronoun in ["he", "him", "his"]:
        if pronoun in sentence:
            people += 1
            break
    for pronoun in ["you", "your", "yours"]:
        if pronoun in sentence:
            people += 1
            break
    for pronoun in ["I", "my", "me", "mine"]:
        if pronoun in sentence:
            people += 1
            break
    return people > 1


def short_premise(dataset, idx, thresh=15):
    return len(dataset.sentences[idx][0].split()) <= thresh


def short_premise_10(dataset, idx, thresh=10):
    return short_premise(dataset, idx, thresh=thresh)


def short_premise_5(dataset, idx, thresh=5):
    return short_premise(dataset, idx, thresh=thresh)


def common_words(dataset, idx, thresh=5):
    return (
        len(
            set(dataset.sentences[idx][0].lower().split()).intersection(
                set(dataset.sentences[idx][1].lower().split())
            )
        )
        >= thresh
    )


def short_premise_cola(dataset, idx, thresh=5):
    return len(dataset.sentences[idx][0].split()) < thresh


def short_hypothesis(dataset, idx, thresh=5):
    return len(dataset.sentences[idx][1].split()) < thresh


def long_hypothesis(dataset, idx, thresh=15):
    return len(dataset.sentences[idx][1].split()) > thresh


def long_premise(dataset, idx, thresh=100):
    return len(dataset.sentences[idx][0].split()) > thresh


def has_wh_words(dataset, idx):
    words = ["who", "what", "where", "when", "why", "how"]
    both_sentences = get_both_sentences(dataset, idx)
    return any([x in both_sentences for x in words])


def has_coordinating_conjunction_hypothesis(dataset, idx):
    words = ["and", "but", "or"]
    hypothesis = dataset.sentences[idx][1]
    return any([p in hypothesis for p in words])


def has_coordinating_conjunction(dataset, idx):
    words = ["and", "but", "or"]
    both_sentences = get_both_sentences(dataset, idx)
    return any([p in both_sentences for p in words])


def ends_with_verb(dataset, idx):
    doc = dataset.spacy_tokens[idx][0]
    # last is punctuation, second to last for last word
    return doc[-2].pos_ == "VERB"


def ends_with_adverb(dataset, idx):
    doc = dataset.spacy_tokens[idx][0]
    # last is punctuation, second to last for last word
    return doc[-2].pos_ == "ADV"


def has_but(dataset, idx):
    both_sentences = get_both_sentences(dataset, idx)
    return "but" in both_sentences


def has_and(dataset, idx):
    both_sentences = get_both_sentences(dataset, idx)
    return "and" in both_sentences


def has_or(dataset, idx):
    both_sentences = get_both_sentences(dataset, idx)
    return "or" in both_sentences


def has_symbol(dataset, idx):
    both_sentences = get_both_sentences(dataset, idx)
    doc = nlp(both_sentences)
    return any([x.pos_ == "SYM" for x, x_ent in zip(doc, doc.ents)])


def who_question(dataset, idx):
    return "who" in dataset.sentences[idx][0].lower()


def what_question(dataset, idx):
    return "what" in dataset.sentences[idx][0].lower()


def where_question(dataset, idx):
    return "where" in dataset.sentences[idx][0].lower()


def when_question(dataset, idx):
    return "when" in dataset.sentences[idx][0].lower()


def why_question(dataset, idx):
    return "why" in dataset.sentences[idx][0].lower()


def how_question(dataset, idx):
    return "how" in dataset.sentences[idx][0].lower()


def has_multiple_articles(dataset, idx):
    both_sentences = get_both_sentences(dataset, idx)
    multiple_a = sum([int(x == "a") for x in both_sentences.split()]) > 1
    multiple_an = sum([int(x == "an") for x in both_sentences.split()]) > 1
    multiple_the = sum([int(x == "a") for x in both_sentences.split()]) > 1
    return multiple_a or multiple_an or multiple_the


def has_numerical_date(dataset, idx):
    both_sentences = get_both_sentences(dataset, idx)
    doc = nlp(both_sentences)
    return any(
        [x_ent.label_ == "DATE" and x.like_num for x, x_ent in zip(doc, doc.ents)]
    )


def is_quantification(dataset, idx):
    words = ["all", "some", "none"]
    both_sentences = get_both_sentences(dataset, idx)
    return any([p in both_sentences for p in words])


def is_spatial_expression(dataset, idx):
    words = ["to the left of", "to the right of"]
    both_sentences = get_both_sentences(dataset, idx)
    return any([p in both_sentences for p in words])


def stsb_captions(dataset, idx):
    split = dataset.split
    genre = json.load(
        open(f"/dfs/scratch0/chami/metal/metal/mmtl/glue/stsb_{split}_slices.json")
    )
    return genre[idx] == "main-captions"


def stsb_news(dataset, idx):
    split = dataset.split
    genre = json.load(
        open(f"/dfs/scratch0/chami/metal/metal/mmtl/glue/stsb_{split}_slices.json")
    )
    return genre[idx] == "main-news"


def stsb_forums(dataset, idx):
    split = dataset.split
    genre = json.load(
        open(f"/dfs/scratch0/chami/metal/metal/mmtl/glue/stsb_{split}_slices.json")
    )
    # print(genre[:5])
    return "forum" in genre[idx]


def is_quantification_hypothesis(dataset, idx):
    words = ["all", "some", "none"]
    hypothesis = dataset.sentences[idx][1]
    return any([p in hypothesis for p in words])


def is_comparative(dataset, idx):
    comparative_words = ["more", "less", "better", "worse", "bigger", "smaller"]
    both_sentences = get_both_sentences(dataset, idx)
    return any([p in both_sentences for p in comparative_words])


def has_non_spatial_preposition(dataset, idx):
    non_spatial_prepositions = [
        "about",
        "after",
        "all over",
        "along",
        "among",
        "around",
        "before",
        "for",
        "from",
        "past",
        "through",
        "to",
        "with",
        "without",
    ]
    both_sentences = get_both_sentences(dataset, idx)
    return any([p in both_sentences for p in non_spatial_prepositions])


def has_spatial_preposition(dataset, idx):
    spatial_prepositions = [
        "above",
        "aross",
        "ahead of",
        "along",
        "around",
        "at",
        "behind",
        "below",
        "beneath",
        "beside",
        "by",
        "in",
        "in front of",
        "inside",
        "inside of",
        "into",
        "near",
        "nearby",
        "next to",
        "on",
        "on top of",
        "out of",
        "out of" "outside",
        "outside of",
        "over",
        "through",
        "under",
        "up",
        "within",
        "with" "without",
    ]
    both_sentences = get_both_sentences(dataset, idx)
    return any([p in both_sentences for p in spatial_prepositions])


def has_temporal_preposition(dataset, idx):
    temporal_prepositions = ["after", "before", "past"]
    both_sentences = get_both_sentences(dataset, idx)
    return any([p in both_sentences for p in temporal_prepositions])


def has_possessive_preposition(dataset, idx):
    possessive_prepositions = ["inside of", "with", "within"]
    both_sentences = get_both_sentences(dataset, idx)
    return any([p in both_sentences for p in possessive_prepositions])


def common_negation(dataset, idx):
    negation_words = [
        # https://www.grammarly.com/blog/negatives/
        "no",
        "not",
        "none",
        "no one",
        "nobody",
        "nothing",
        "neither",
        "nowhere",
        "never",
        "hardly",
        "scarcely",
        "barely",
        "doesn't",
        "isn't",
        "wasn't",
        "shouldn't",
        "wouldn't",
        "couldn't",
        "won't",
        "can't",
        "don't",
    ]
    both_sentences = get_both_sentences(dataset, idx)
    return any([x in negation_words for x in both_sentences.split()])


def entity_secondonly(dataset, idx):
    sent1 = dataset.sentences[idx][0]
    sent2 = nlp(dataset.sentences[idx][1])
    for ent in sent2.ents:
        if ent.text not in sent1:
            return True
    return False


def ends_with_question_word(dataset, idx):
    """Returns True if a question word is in the last three tokens of any sentence"""
    # HACK: For now (speedy POC), just use the BERT tokens
    # Eventually, we'd like to have access to the raw text (e.g., via the Spacy
    # tokenization) and have the two sentences separated for pair tasks

    # spacy_sentences = dataset.spacy_tokens[idx]
    # for spacy_sentence in spacy_sentences:
    #     if any(token.text in question_words for token in spacy_sentence):
    #         return True

    bert_ints = dataset.bert_tokens[idx]
    bert_tokens = dataset.bert_tokenizer.convert_ids_to_tokens(bert_ints)
    return any(token in question_words for token in bert_tokens[-3:])
    # match = any(token in question_words for token in bert_tokens[-3:])
    # if match:
    #     print(bert_tokens)
    # return match


def is_statement_has_question(dataset, idx):
    """Returns True if question word exists in statement that doesn't end with ?"""
    bert_ints = dataset.bert_tokens[idx]
    bert_tokens = dataset.bert_tokenizer.convert_ids_to_tokens(bert_ints)

    return (
        any(t.lower() in question_words for t in bert_tokens) and bert_tokens[-2] != "?"
    )


def ends_with_question_mark(dataset, idx):
    """Returns True if last token is '?" symbol"""
    bert_ints = dataset.bert_tokens[idx].tolist()
    bert_tokens = dataset.bert_tokenizer.convert_ids_to_tokens(bert_ints)

    # last token is '[SEP]'
    # check the second to last token for end of sentence
    return bert_tokens[-2] == "?"


def dash_semicolon(dataset, idx):
    """Returns True if there is a dash or semicolon in sentence1"""
    bert_ints = dataset.bert_tokens[idx].tolist()
    bert_tokens = dataset.bert_tokenizer.convert_ids_to_tokens(bert_ints)
    return "-" in bert_tokens or ";" in bert_tokens


question_type = dict()
with open(
    os.environ["METALHOME"] + "/metal/mmtl/slicing/qnli_question_type.txt", "r"
) as read_file:
    for line in read_file:
        question, type = line.strip().split("######")
        question_type[question] = int(type)

    LABEL_MAPPING = {"unknown": 1, "what": 2, "who": 3, "when": 4, "affirmation": 5}


def question_type_unknown(dataset, idx, type=1):
    return (
        dataset.sentences[idx][0] in question_type
        and question_type[dataset.sentences[idx][0]] == type
    )


def question_type_what(dataset, idx, type=2):
    return (
        dataset.sentences[idx][0] in question_type
        and question_type[dataset.sentences[idx][0]] == type
    )


def question_type_who(dataset, idx, type=3):
    return (
        dataset.sentences[idx][0] in question_type
        and question_type[dataset.sentences[idx][0]] == type
    )


def question_type_when(dataset, idx, type=4):
    return (
        dataset.sentences[idx][0] in question_type
        and question_type[dataset.sentences[idx][0]] == type
    )


def question_type_affirmation(dataset, idx, type=5):
    return (
        dataset.sentences[idx][0] in question_type
        and question_type[dataset.sentences[idx][0]] == type
    )


def has_location(dataset, idx):
    both_sentences = get_both_sentences(dataset, idx)
    doc = nlp(both_sentences)
    return any([x_ent.label_ == "GPE" for x, x_ent in zip(doc, doc.ents)])


def in_asia(dataset, idx):
    words = [
        "azerbaijan",
        "japan",
        "qatar",
        "armeniajordan",
        "saudi",
        "arabia",
        "bahrain",
        "kazakhstan",
        "singapore",
        "bangladesh",
        "kuwait",
        "south korea",
        "bhutan",
        "kyrgyzstan",
        "sri lanka",
        "brunei",
        "laos",
        "syria",
        "burma",
        "lebanon",
        "taiwan",
        "cambodia",
        "malaysia",
        "tajikistan",
        "china",
        "maldives",
        "thailand",
        "east timor",
        "mongolia",
        "turkey",
        "india",
        "nepal",
        "turkmenistan",
        "indonesia",
        "north korea",
        "united arab emirates",
        "iran",
        "oman",
        "uzbekistan",
        "iraq",
        "pakistan",
        "vietnam",
        "israel",
        "philippines",
        "yemen",
    ]
    both_sentences = get_both_sentences(dataset, idx)
    return any([x in both_sentences for x in words])


def sports(dataset, idx):
    words = [
        "sport",
        "sports",
        "athletics",
        "athletics",
        "baseball",
        "basketball",
        "bowling",
        "car racing",
        "cycling",
        "football",
        "golf",
        "gymnastics",
        "handball",
        "hang gliding",
        "hockey",
        "horse racing",
        "jogging",
        "motorcycle racing",
        "para gliding",
        "polo",
        "rugby",
        "scuba diving",
        "skiing",
        "skin diving",
        "snow-boarding",
        "soccer",
        "softball",
        "squash",
        "swimming",
        "table tennis",
        "tennis",
        "track and field",
        "volleyball",
    ]
    both_sentences = get_both_sentences(dataset, idx)
    return any([x in both_sentences for x in words])


def non_question(dataset, idx):
    question_words = set(["who", "what", "where", "when", "why", "how"])
    for word in question_words:
        if word in dataset.sentences[idx][0].lower():
            return False
    return True


# Functions which map a payload and index with an indicator if that example is in slice
# NOTE: the indexing is left to the functions so that extra fields helpful for slicing
# but not required by the model (e.g., spacy-based features) can be stored with the
# dataset but not necessarily passed back by __getitem__() which is called by the
# DataLoaders.
# No longer needed: can do same thing as below with globals()[slice_name]
# slice_functions = {
#     "ends_with_question_word": ends_with_question_word,
#     "ends_with_question_mark": ends_with_question_mark,
#     "is_statement_has_question": is_statement_has_question,
# }


def create_slice_labels(dataset, base_task_name, slice_name, verbose=False):
    """Returns a label set masked to include only those labels in the specified slice"""
    # TODO: break this out into more modular pieces oncee we have multiple slices
    slice_fn = globals()[slice_name]
    slice_indicators = torch.tensor(
        [slice_fn(dataset, idx) for idx in range(len(dataset))], dtype=torch.uint8
    ).view(-1, 1)

    Y_base = dataset.labels[f"{base_task_name}_gold"]
    Y_slice = Y_base.clone().masked_fill_(slice_indicators == 0, 0)

    if verbose:
        if not any(Y_slice):
            warnings.warn(f"No examples were found to belong to slice {slice_name}")
        else:
            print(f"Found {sum(slice_indicators)} examples in slice {slice_name}.")

    # NOTE: we assume here that all slice labels are for sentence-level tasks only
    # convert from True/False mask -> 1,2 categorical labels
    categorical_indicator = convert_labels(slice_indicators, "onezero", "categorical")

    return {"ind": categorical_indicator, "pred": Y_slice}
