import os
import json
from sklearn.feature_extraction.text import CountVectorizer
from scipy.sparse import hstack

def load_character_bags(json_folder):
    character_bags = {}
    for filename in os.listdir(json_folder):
        if filename.endswith('.json'):
            with open(os.path.join(json_folder, filename)) as f:
                data = json.load(f)
                for character in data:
                    name = character['name']
                    bag_words = { "agent verb": [], "patient verb": [], "attribute": []}
                    for pair in character['bag']:
                        bag_words[pair[0]].append(pair[1])
                    
                    character_bags[name] = bag_words
    return character_bags
    
def load_tropes(tropes_file):
    trope_dict = {}
    with open(tropes_file) as f:
        for line in f:
            trope, char_data = line.split("\t")
            char_info = json.loads(char_data)
            name = char_info['char']
            trope_dict[name] = trope
    return trope_dict
    
def get_overlapping_characters(character_bags, trope_dict):
    common_characters = set(character_bags.keys()).intersection(trope_dict.keys())
    filtered_bags = {name: character_bags[name] for name in common_characters}
    filtered_tropes = {name: trope_dict[name] for name in common_characters}
    return filtered_bags, filtered_tropes
    
def get_dt_matrix(chars):
    agent_texts = [" ".join(data["agent verb"]) for data in chars.values()]
    patient_texts = [" ".join(data["patient verb"]) for data in chars.values()]
    attribute_texts = [" ".join(data["attribute"]) for data in chars.values()]

    agent_vectorizer = CountVectorizer()
    patient_vectorizer = CountVectorizer()
    attribute_vectorizer = CountVectorizer()

    agent_matrix = agent_vectorizer.fit_transform(agent_texts)
    patient_matrix = patient_vectorizer.fit_transform(patient_texts)
    attribute_matrix = attribute_vectorizer.fit_transform(attribute_texts)

    agent_features = agent_vectorizer.get_feature_names_out()
    patient_features = patient_vectorizer.get_feature_names_out()
    attribute_features = attribute_vectorizer.get_feature_names_out()
    
    dt_matrix = hstack([agent_matrix, patient_matrix, attribute_matrix])
    
    return dt_matrix, agent_features, patient_features, attribute_features

def get_clusters_dictionary(char_full, char_filtered, pred, num_clusters):
    cluster_dict = {i: [] for i in range(num_clusters)}
    
    for name in list(char_filtered.keys()): 
        label = pred[list(char_full.keys()).index(name)]
        cluster_dict[label].append(name)
           
    return cluster_dict
    
def get_tropes_dictionary(tropes_filtered):
    grouped_by_trope = {}
    
    for name, trope in tropes_filtered.items():
        if trope not in grouped_by_trope:
            grouped_by_trope[trope] = []
        grouped_by_trope[trope].append(name)
        
    return grouped_by_trope
