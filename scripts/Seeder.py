#!/usr/bin/env python
# coding: utf-8

# In[9]:



import pandas as pd
import seaborn as sb
import numpy as np
import math as m
import os
import collections
import csv
import random as rn
from matplotlib import pyplot as plt
import scipy as sp
from scipy.stats import truncnorm as tn

# Parameter setting

dataset_name = "sample_days"
papers_number = 300
readers_number = 150
authors_number = 25
months_number = 1
paper_frequencies = [
    2 * months_number, 
    4 * months_number, 
    8 * months_number, 
    30 * months_number, 
    90 * months_number
]
readers_percent = 20

assert papers_number > (90 * months_number), f"ERROR: papers_number must be greater than (equal to) {(90 * months_number)}" 

# Seed folder path

dataset_folder_path = f"../data/{dataset_name}/"
info_file_path = f"{dataset_folder_path}info.csv"
ratings_file_path = f"{dataset_folder_path}ratings.csv"
authors_file_path = f"{dataset_folder_path}authors.csv"
stats_file_path = f"{dataset_folder_path}stats.csv"

# Setting up arrays

papers = np.arange(papers_number)
readers = np.arange(readers_number)
authors = np.arange(authors_number)

os.makedirs(dataset_folder_path, exist_ok=True)

print("DATASET NAME: ", dataset_name)
print("DATASET FOLDER PATH: ", dataset_folder_path)
print("INFO FILE PATH: ", info_file_path)
print("RATINGS FILE PATH: ", ratings_file_path)
print("AUTHORS FILE PATH: ", authors_file_path)


# In[10]:



# Papers distribution generation

print("---------- PAPER DISTRIBUTIONS GENERATION STARTED ----------")

paper_distributions = np.empty(papers_number)
for index in range(0, papers_number):
    percentage = 100*index/papers_number
    if percentage % 10 == 0:
        print(f"{int(index)}/{papers_number} ({int(percentage)}/100%)")
    distribution = tn(0, 1, loc=rn.uniform(0, 1), scale=rn.uniform(0, 0.05)).rvs(1)
    paper_distributions[index] = distribution
print(f"{papers_number}/{papers_number} (100/100%)")
    
print("---------- PAPER DISTRIBUTIONS GENERATION COMPLETED ----------")


# In[11]:



# Ratings file generation

# N sets of readers, each one has X% of the total

reader_sets_number = m.floor(100 / readers_percent)
readers_amount = m.floor((readers_number*readers_percent)/100)

readers_set = set(readers)
readers_sets = []

print("---------- READERS SETS GENERATION STARTED ----------")

ratings_number = sum(paper_frequencies) * readers_amount
for x in range(0, reader_sets_number):
    current_readers_set = rn.sample(readers_set, readers_amount)
    # Removing last index
    if readers_number in current_readers_set: current_readers_set.remove(readers_number)
    readers_sets.append(current_readers_set)
    for reader in current_readers_set:
        readers_set.remove(reader)
    print(f"SET {x}: ", current_readers_set)
     
print("---------- READERS SETS GENERATION COMPLETED ----------")

print("---------- RATINGS GENERATION STARTED ----------")

generated_ratings = 0
with open(ratings_file_path, mode='w', newline='') as ratings_file:
    ratings_writer = csv.writer(ratings_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    ratings_writer.writerow(['Timestamp', 'Reader', 'Paper', 'Score'])
    for current_set in range(0, reader_sets_number):
        paper_per_reader = paper_frequencies[current_set]
        readers_set = readers_sets[current_set]
        for reader in readers_set:
            for index, paper in enumerate(rn.sample(set(papers), paper_per_reader)):
                paper_distribution = paper_distributions[paper]
                percentage = 100*generated_ratings/ratings_number
                if percentage % 10 == 0:
                    print(f"{int(generated_ratings)}/{ratings_number} ({int(percentage)}/100%)")
                current_tuple = {
                    "Reader": reader, 
                    "Paper": paper, 
                    "Score": round(paper_distribution, 2), 
                }
                ratings_writer.writerow([generated_ratings, current_tuple["Reader"], current_tuple["Paper"], current_tuple["Score"]])
                generated_ratings+=1
    print(f"{ratings_number}/{ratings_number} (100/100%)")
ratings_file.close()

print("---------- RATINGS GENERATION ENDED ----------")


# In[12]:



# Authors file generation

print("---------- AUTHORS GENERATION STARTED ----------")

with open(authors_file_path, mode='w', newline='') as authors_file:
    authors_writer = csv.writer(authors_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    authors_writer.writerow(["Author", "Paper"])
    for index, author in enumerate(authors):
        percentage = 100*index/authors_number
        if percentage % 10 == 0:
            print(f"{int(index)}/{authors_number} ({int(percentage)}/100%)")
        # An author writes a number of paper between 1 and paper_fraction
        author_papers_number = rn.randint(1, (papers_number-1))
        papers_written = np.random.choice(papers, author_papers_number).tolist()
        papers_written = set(papers_written)
        if len(papers_written) > 1:
            papers_written = map(str, list(papers_written))
            papers_written = ";".join(papers_written)
        authors_writer.writerow([author, papers_written])
    print(f"{authors_number}/{authors_number} (100/100%)")
authors_file.close()
        
print("---------- AUTHORS GENERATION ENDED ----------")


# In[13]:



# Info file generation

print("---------- INFO GENERATION STARTED ----------")

info_dataframe = pd.DataFrame(columns=["Dataset", "Paper", "Reader", "Rating", "Author"])
info_dataframe = info_dataframe.append(
    {
        "Dataset": dataset_name, 
        "Paper": papers_number, 
        "Reader": readers_number, 
        "Rating": ratings_number, 
        "Author": authors_number
    }, ignore_index=True)
info_dataframe.to_csv(info_file_path, index=False)

print("---------- INFO GENERATION ENDED ----------")


# In[14]:


# Stats file generation

print("---------- STATS GENERATION STARTED ----------")

temp_ratings_dataframe = pd.read_csv(ratings_file_path, header=None)
temp_ratings_dataframe[temp_ratings_dataframe.columns] = temp_ratings_dataframe[temp_ratings_dataframe.columns].convert_objects(convert_numeric=True)

stats_dataframe = temp_ratings_dataframe.copy()
stats_dataframe[stats_dataframe > 0.0000001] = 1

print("---------- COMPUTING STATS FOR PAPERS ----------")

sums_paper = stats_dataframe.copy().sum(axis=0)
sums_paper_dataframe = pd.DataFrame(sums_paper)

max_ratings_paper = sums_paper_dataframe.max()
min_ratings_paper = sums_paper_dataframe.min()
mean_ratings_paper = sums_paper_dataframe.mean()

temp_ratings_dataframe = temp_ratings_dataframe.T
paper_counter = 0
for index, row in temp_ratings_dataframe.iterrows():
    if len(np.unique(row)) == 1:
        paper_counter+=1
        
print("---------- COMPUTING STATS FOR READERS ----------")

sums_reader = stats_dataframe.copy().sum(axis=1)
counter=collections.Counter(sums_reader)
sums_reader_dataframe = pd.DataFrame(sums_reader)

max_ratings_reader = sums_reader_dataframe.max()
min_ratings_reader = sums_reader_dataframe.min()
mean_ratings_reader = sums_reader_dataframe.mean()

temp_ratings_dataframe = temp_ratings_dataframe
reader_counter = 0
for index, row in temp_ratings_dataframe.iterrows():
    if len(np.unique(row)) == 1:
        reader_counter+=1
        
# Writing stats to file

stats_dataframe = pd.DataFrame(columns=[
    "Dataset",
    "Max Number Rating Paper", 
    "Min Number Rating Paper", 
    "Mean Number Rating Paper",
    "Max Number Rating Reader", 
    "Min Number Rating Reader", 
    "Mean Number Rating Reader"
])
stats_dataframe = stats_dataframe.append(
    {
        "Dataset": dataset_name, 
        "Max Number Rating Paper": int(max_ratings_paper.values[0]), 
        "Min Number Rating Paper": int(min_ratings_paper.values[0]), 
        "Mean Number Rating Paper": int(mean_ratings_paper.values[0]), 
        "Max Number Rating Reader": int(max_ratings_reader.values[0]), 
        "Min Number Rating Reader": int(min_ratings_reader.values[0]), 
        "Mean Number Rating Reader": int(mean_ratings_reader.values[0]), 
    }, ignore_index=True)
stats_dataframe.to_csv(stats_file_path, index=False)

print("---------- STATS GENERATION COMPLETED ----------")


# In[15]:


# Summary

print("MAX NUMBER OF RATINGS FOR A PAPER: ", int(max_ratings_paper.values[0]))
print("MIN NUMBER OF RATINGS FOR A PAPER: ", int(min_ratings_paper.values[0]))
print("MEAN NUMBER OF RATINGS FOR A PAPER: ", int(mean_ratings_paper.values[0]))
print("NUMBER OF PAPERS WITH UNIQUE RATING: ", reader_counter)
print("MAX NUMBER OF RATINGS FOR A READER: ", int(max_ratings_reader.values[0]))
print("MIN NUMBER OF RATINGS FOR A READER: ", int(min_ratings_reader.values[0]))
print("MEAN NUMBER OF RATINGS FOR A READER: ", int(mean_ratings_reader.values[0]))
print("NUMBER OF READERS WITH UNIQUE RATING: ", paper_counter)


# In[ ]:




