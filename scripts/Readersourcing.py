#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import math as m
import linecache
from collections import deque
import csv
import zipfile
import threading
import numpy as np
import os
import json
import time

# Parameter setting

dataset_name = "sample"
days_serialization = True
days_serialization_threshold = 2
days_number = 10
# days_cleaning_threshold = 4
# result_compression = True
# archive_name = "result"

# Reader score must be set to a very small value otherwise there will be a division by 0

epsilon = 0.000001

# CSV file parsing

dataset_folder_path = "../data/{}/".format(dataset_name)
info_filename = "{}info.csv".format(dataset_folder_path)
ratings_filename = "{}ratings.csv".format(dataset_folder_path)
authors_filename = "{}authors.csv".format(dataset_folder_path)

info = pd.read_csv(info_filename)
paper_authors = pd.read_csv(authors_filename)
paper_authors = paper_authors.values
paper_ratings = pd.read_csv(ratings_filename)
paper_ratings = paper_ratings.values

csv_offset = 2

# Initial Readersourcing setup

dataset_name = info["Dataset"][0]
papers_number = info["Paper"][0]
readers_number = info["Reader"][0]
ratings_number = info["Rating"][0]
ratings_number_per_day = m.floor(int(ratings_number / days_number))
authors_number = info["Author"][0]
papers = np.arange(papers_number)
readers = np.arange(readers_number)
ratings = np.arange(ratings_number)
authors = np.arange(authors_number)
paper_steadiness = np.zeros(papers_number)
paper_score = np.zeros(papers_number)
rating_goodness = np.zeros(ratings_number)
reader_steadiness = np.zeros(readers_number)
reader_score = np.zeros(readers_number)
reader_score.fill(epsilon)
author_steadiness = np.zeros(authors_number)
author_score = np.zeros(authors_number)

# Day serialization handling

computed_days = 1
written = False
# cleaned = False

# Output handling

result_file_paths = []


# In[3]:



# ----- ALGORITHM STARTS HERE ----- #

start_time = time.time()

def get_author(current_paper) :
    
    found_authors = []
    
    for author_index, author_entry in enumerate(paper_authors) :
        current_author = int(author_entry[0])
        written_papers = author_entry[1].split(";")
        written_papers = [int(x) for x in written_papers]
        if current_paper in written_papers :
            found_authors.append(current_author)
            
    return np.asarray(found_authors)

# Function to output result to file

def serialize_result(day, current_index, verbose):
    
    base_path = "../models/{}/readersourcing/".format(dataset_name)
    
    if days_serialization:
        result_folder_path = "{}day_{}/".format(base_path, day)
    else:
        result_folder_path = base_path
    
    os.makedirs(result_folder_path, exist_ok=True)

    # Quantities output handling

    dictionary = [
        {'Quantity': 'Paper Steadiness', 'Identifiers': papers.tolist(), 'Values': paper_steadiness.tolist()},
        {'Quantity': 'Paper Score', 'Identifiers': papers.tolist(), 'Values': paper_score.tolist()},
        {'Quantity': 'Reader Steadiness', 'Identifiers': readers.tolist(), 'Values': reader_steadiness.tolist()},
        {'Quantity': 'Reader Score', 'Identifiers': readers.tolist(), 'Values': reader_score.tolist()},
        {'Quantity': 'Author Steadiness', 'Identifiers': authors.tolist(), 'Values': author_steadiness.tolist()},
        {'Quantity': 'Author Score', 'Identifiers': authors.tolist(), 'Values': author_score.tolist()},
    ]
    
    result_quantities_filename = "{}quantities.json".format(result_folder_path, day)
    
    if verbose:
        print("PRINTING QUANTITIES TO .JSON FILE AT PATH {}".format(result_quantities_filename))
    
    with open(result_quantities_filename, 'w') as result_quantities_file:  
        json.dump(dictionary, result_quantities_file)
    result_quantities_file.close()
        
    # Rating and goodness matrix output handling
    
    rating_matrix = np.zeros((readers_number, papers_number))
    goodness_matrix = np.zeros((readers_number, papers_number))
    
    for rating_index in range(csv_offset, current_index):
                
        current_entry = linecache.getline(ratings_filename, rating_index).split(",")
                
        # Example: <1,1,2,0.8,0>
        # At Timestamp 1 Reader 1 gave to Paper 2 a Rating of 0.8
        current_timestamp = int(current_entry[0])
        current_reader = int(current_entry[1])
        current_paper = int(current_entry[2])
        current_rating = float(current_entry[3])
            
        rating_matrix[current_reader][current_paper] = current_rating
        goodness_matrix[current_reader][current_paper] = rating_goodness[current_timestamp]
    
    result_ratings_filename = "{}ratings.csv".format(result_folder_path, day)
    result_goodness_filename = "{}goodness.csv".format(result_folder_path, day)
    
    if verbose:
        print("PRINTING RATING MATRIX TO .CSV FILE AT PATH {}".format(result_ratings_filename))
            
    paper_ratings_dataframe = pd.read_csv(ratings_filename)
    ratings_matrix = paper_ratings_dataframe.pivot_table(index="Reader", columns="Paper", values="Score")
    ratings_matrix.fillna(0, inplace=True)
    ratings_matrix.to_csv(result_ratings_filename, sep=",", header=False, index=False)
        
    if verbose:
        print("PRINTING RATING GOODNESS MATRIX TO .CSV FILE AT PATH {}".format(result_goodness_filename))
    
    with open(result_goodness_filename, mode='w', newline='') as result_goodness_file:
        goodness_writer = csv.writer(result_goodness_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for goodness_entry in goodness_matrix:
            goodness_writer.writerow(goodness_entry)
    result_goodness_file.close()
    
    # Info output handling
    
    result_elapsed_time = time.time() - start_time 
    
    dictionary = [{'Time': result_elapsed_time}]
    
    result_info_filename = "{}info.json".format(result_folder_path, day)
    
    if verbose:
        print("PRINTING INFO TO .JSON FILE AT PATH {}".format(result_info_filename))
        
    with open(result_info_filename, 'w') as result_info_file:  
        json.dump(dictionary, result_info_file)
    result_info_file.close()
    
    #if result_compression:
    #    archive_filename = "{}{}.zip".format(result_folder_path, archive_name)
    #    archive_file = zipfile.ZipFile(archive_filename, 'w')
    #    for folder, subfolders, files in os.walk(result_folder_path):
    #        for file in files:
    #            if file.endswith('.csv') or file.endswith('.json'):
    #                archive_file.write(os.path.join(folder, file), os.path.relpath(os.path.join(folder,file), result_folder_path), compress_type = zipfile.ZIP_DEFLATED)
    #    archive_file.close()           
    #    print("RESULT COMPRESSED INTO A .ZIP ARCHIVE AT PATH {}".format(archive_filename))
                
    file_paths = [result_ratings_filename, result_goodness_filename, result_quantities_filename, result_info_filename]
    
    return result_elapsed_time, file_paths

def clean_results(results_to_clean):
    print("*********************************")
    print("********** CLEANING RESULTS **********")
    for file_path in results_to_clean:
        if os.path.isfile(file_path):
            print("Deleting file at path: ", file_path)
            thread = threading.Thread(
                target=os.remove,
                args=[file_path],
            )
            thread.daemon = True
            thread.start()
    print("*********************************")

# There are many "print" that you can uncomment if you have to do some debugging
# print("##########")

print("------------------------------")
if days_serialization:
    print("---------- DAY 0/{} ----------".format(days_number))
print("0/0 (0/100%)")

for index in range(csv_offset, (ratings_number + csv_offset)):
    
    percentage = 100*index/ratings_number
    if percentage % 2 == 0:
        print("{}/{} ({}/100%)".format(int(index), ratings_number, int(percentage)))
    
    if days_serialization:
        if index % (ratings_number_per_day * computed_days) == 0:
            computed_days += 1
            written = False
            #cleaned = False
            # if computed_days % days_cleaning_threshold == 0 and not cleaned:
            #     clean_results(result_file_paths)
            #     result_file_paths = []
            #     cleaned = True
            if computed_days % days_serialization_threshold == 0 and not written:
                print("---------- DAY {}/{} ----------".format(computed_days, days_number))
                elapsed_time, paths = serialize_result(computed_days, index, verbose=False)
                result_file_paths = result_file_paths + paths
                written = True

    entry = linecache.getline(ratings_filename, index).split(",")
                                                                     
    # Example: <1,1,2,0.8,0>
    # At Timestamp 1 Reader 1 gave to Paper 2 a Rating of 0.8
    timestamp = int(entry[0])
    reader = int(entry[1])
    paper = int(entry[2])
    rating = float(entry[3])
    authors_of_paper = get_author(paper)
    
    # print("---------- CURRENT ENTRY ----------")
    # print(f"TIMESTAMP {timestamp} - READER {reader} - PAPER {paper} - SCORE {rating}")

    # COMPUTATION START: PAPER AND READER SCORE

    # Saving values at time t(i)

    old_paper_steadiness = paper_steadiness[paper]
    old_paper_score = paper_score[paper]
    old_reader_steadiness = reader_steadiness[reader]
    old_rating_goodness = rating_goodness[timestamp]
    old_reader_score = reader_score[reader]
    
    # print("---------- PRINTING VALUES AT TIME T(I) ----------")
    # print("PAPER STEADINESS T(I) ", old_paper_steadiness)
    # print("PAPER SCORE T(I) ", old_paper_score)
    # print("READER STEADINESS T(I) ", old_paper_score)
    # print("RATING GOODNESS T(I) ", rating_goodness[timestamp])
    # print("READER SCORE T(I) ", old_reader_score)

    # Updating values at time t(i+1)

    paper_steadiness[paper] = old_paper_steadiness + old_reader_score
    paper_score[paper] = ((old_paper_steadiness * old_paper_score) + (old_reader_score * rating)) / paper_steadiness[paper]
    rating_goodness[timestamp] = (1 - (m.sqrt(abs(rating - paper_score[paper]))))
    reader_steadiness[reader] = (old_reader_steadiness + paper_steadiness[paper])
    reader_score[reader] = (((old_reader_steadiness * old_reader_score) + (paper_steadiness[paper] * rating_goodness[timestamp])) / reader_steadiness[reader])

    # print("---------- PRINTING VALUES AT TIME T(I+1) ----------")
    # print("PAPER STEADINESS T(I+1) ", paper_steadiness[paper])
    # print("PAPER SCORE T(I+1) ", paper_score[paper])
    # print("READER STEADINESS T(I+1) ", reader_steadiness[reader])
    # print("RATING GOODNESS T(I+1) ", rating_goodness[timestamp])
    # print("READER SCORE T(I+1) ", reader_score[reader])

    # COMPUTATION START: AUTHOR SCORE

    for author in authors_of_paper :
        # Saving values at time t(i)

        old_author_steadiness = author_steadiness[author]
        old_author_score = author_score[author]

        # Updating values at time t(i+1)7

        author_steadiness[author] = old_author_steadiness + old_reader_score
        author_score[author] = ((old_author_steadiness * old_author_score) + (old_reader_score * rating)) / author_steadiness[author]

    # COMPUTATION START: PROPAGATING CHANGES TO PREVIOUS READERS
        
    previous_ratings = []        
    with open(ratings_filename) as rating_file:
        raw_previous_ratings = deque([next(rating_file) for x in range(csv_offset, (index + csv_offset))])
        raw_previous_ratings.popleft()
    rating_file.close()
    for raw_previous_rating in raw_previous_ratings:
        previous_rating = raw_previous_rating.split(",")
        previous_ratings.append(previous_rating)
    previous_ratings = np.array(previous_ratings, dtype=float)
    previous_ratings = previous_ratings[
         (previous_ratings[:,1]!=float(reader)) &
         (previous_ratings[:,2]==float(paper))
    ]            
                   
    # print(" ----- PREVIOUS PAPER RATINGS -----")

    for previous_index, previous_entry in enumerate(previous_ratings):
        
        # Example: <1,1,2,0.8,0>
        # At Timestamp 1 Reader 1 gave to Paper 2 a Rating of 0.8 written by Author 0
        previous_timestamp = int(previous_entry[0])
        previous_reader = int(previous_entry[1])
        previous_paper = int(previous_entry[2])
        previous_rating = previous_entry[3]

        # print(f"PREVIOUS TIMESTAMP {previous_timestamp} - PREVIOUS READER {previous_reader} - PREVIOUS PAPER {previous_paper} - PREVIOUS RATING {previous_rating}")

        # Saving previous values at time t(i)

        old_previous_reader_steadiness = reader_steadiness[previous_reader]
        old_previous_reader_score = reader_score[previous_reader]
        old_previous_rating = previous_rating
        old_previous_rating_goodness = rating_goodness[previous_timestamp]

        # Updating previous values at time t(i+1)

        rating_goodness[previous_timestamp] = 1 - (m.sqrt(abs(old_previous_rating - paper_score[paper])))
        reader_steadiness[previous_reader] = (old_previous_reader_steadiness + old_reader_score)
        reader_score[previous_reader] = (
                                            (old_previous_reader_steadiness * old_previous_reader_score) -
                                            (old_paper_steadiness * old_previous_rating_goodness) +
                                            (paper_steadiness[paper] * rating_goodness[previous_timestamp])
                                        ) / reader_steadiness[previous_reader]
           
    # print(" ----- PREVIOUS PAPER RATINGS END -----")
        
    # print("---------- PRINTING FINAL VALUES AT TIME T(I+1) ----------")
    # print("PAPER STEADINESS: ", paper_steadiness)
    # print("PAPER SCORE: ", paper_score)
    # print("READER STEADINESS: ", reader_steadiness)
    # print("READER SCORE: ", reader_score)
    # print("##########")

print("------------------------------")
elapsed_time = serialize_result((days_number-1), ratings_number, verbose=True)
print("ELAPSED TIME: ", elapsed_time)

# ----- ALGORITHM ENDS HERE ----- #


# In[2]:


# Summary

print("PAPER STEADINESS:  ", paper_steadiness)
print("PAPER SCORE:       ", paper_score)
print("READER STEADINESS: ", reader_steadiness)
print("READER SCORE:      ", reader_score)
print("AUTHOR STEADINESS: ", author_steadiness)
print("AUTHOR SCORE:      ", author_score)


# In[ ]:




