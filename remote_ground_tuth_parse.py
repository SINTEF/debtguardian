import pandas as pd
import json
import pygit2
import os
import git
from pydriller import Repository

file_path = '/home/simetv/lab/techdebt/preprocessing/data/MLCQCodeSmellSamples.csv'

df = pd.read_csv(file_path, sep=';')

commit_dict = {}

repo_mapping = {}

error_log = []

error_count = 0

log_dict = {}


def find_previous_commit(repo_url, file_path, commit_hash):
    previous_commit = None

    if repo_url in error_log:
        return None

    try:
        for commit in Repository(repo_url, to_commit=commit_hash, order='reverse').traverse_commits():
            print(commit_hash)
            print(commit.hash)
            print(commit.modified_files)
            print(commit.author_date)
            for modified_file in commit.modified_files:
                print(file_path)
                print(modified_file.old_path)
                print(modified_file.new_path)
                if modified_file.new_path == file_path or modified_file.old_path == file_path:
                    previous_commit = commit.hash
                    print("YES")
                    break
            if previous_commit:
                break
        
        return previous_commit
    #except (git.exc.InvalidGitRepositoryError, git.exc.BadName, ValueError, git.exc.GitCommandError) as e:
    except Exception as e:
        print(f"Error: {e}")
        error_log.append(repo_url)
        #error_count += 1
        return None


for _, row in df.iterrows():
    #commit_hash = row['commit_hash']
    snap_commit_hash = row['commit_hash']
    path = row['path']
    repo = row['repository']

    https_url = repo.replace('git@github.com:', 'https://github.com/')



    trimmed_path = path.lstrip('/')

    commit_hash = find_previous_commit(https_url, trimmed_path, snap_commit_hash)

    print(commit_hash)

    if commit_hash is None:
        continue

    smell = row['smell']
    location_entry = {
        'start_line': row['start_line'],
        'end_line': row['end_line']
    }
    
    #Check if hash existing in dictionary
    if commit_hash not in commit_dict:
        commit_dict[commit_hash] = {}
    
    #Check if file location exists in dictionary under same commit hash
    if path not in commit_dict[commit_hash]:
        commit_dict[commit_hash][path] = {'location': path, 'technicalDebts': []}

    technical_debt_entry = next((item for item in commit_dict[commit_hash][path]['technicalDebts'] if item['type'] == smell), None)
                                
    if technical_debt_entry is None:
        technical_debt_entry = {'type': smell, 'locations': []}
        commit_dict[commit_hash][path]['technicalDebts'].append(technical_debt_entry)

    technical_debt_entry['locations'].append(location_entry)

    #update and write to json file for each iteration

    log_dict = {commit: list(paths.values()) for commit, paths in commit_dict.items()} 
    with open('stream_commit_data.json', 'w') as json_file:
        json.dump(log_dict, json_file, indent=4) 

# Convert the nested dictionary to the desired format
final_dict = {commit: list(paths.values()) for commit, paths in commit_dict.items()}  

with open('new_commit_data.json', 'w') as json_file:
    json.dump(final_dict, json_file, indent=4)