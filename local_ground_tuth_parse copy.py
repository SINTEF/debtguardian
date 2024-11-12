import pandas as pd
import json
import pygit2
import os
import git

file_path = '/home/simetv/lab/techdebt/preprocessing/data/MLCQCodeSmellSamples.csv'

df = pd.read_csv(file_path, sep=';')

commit_dict = {}

repo_mapping = {}

error_log = []

error_count = 0

#def clone_or_update_repo(repo_url, local_path):
#    if not os.path.exists(local_path):
#        print(f'Cloning repository from {repo_url} to {local_path}')
#        pygit2.clone_repository(repo_url, local_path)
#    else:
#        print(f'Repository already exists at {local_path}. Pulling latest changes.')
#        repo = pygit2.Repository(local_path)
#        for remote in repo.remotes:
#            remote.fetch()
#            repo.checkout('refs/remotes/origin/main')


#def get_local_repo_path(repo_url):
#    if repo_url in repo_mapping:
#        return repo_mapping[repo_url]
#    else:
#        local_path = f'/home/simetv/lab/techdebt/preprocessing/repos/{repo_url.split("/")[-1].replace(".git", "")}'
#        clone_or_update_repo(repo_url, local_path)
#        repo_mapping[repo_url] = local_path
#        return local_path


#def find_previous_commit(repo_path, file_path, commit_hash):
#    repo = pygit2.Repository(repo_path)
#    commit = repo.get(commit_hash)
#    
#    # Iterate through the commit history
#    for parent in commit.parents:
#        tree = parent.tree
#        try:
#            tree[file_path]
#            return parent.hex
#        except KeyError:
#            continue
#    
#    return None

def clone_or_update_repo(repo_url, local_path):
    try:
        if not os.path.exists(local_path):
            print(f'Cloning repository from {repo_url} to {local_path}')
            git.Repo.clone_from(repo_url, local_path)
        else:
            print(f'Repository already exists at {local_path}.')
            #repo = git.Repo(local_path)
            #for remote in repo.remotes:
            #    remote.fetch(prune=True)
            #repo.git.checkout('origin/main')
    except git.exc.GitCommandError as e:
        print(f'Error with repository {repo_url}: {e}')
        error_log.append((repo_url, str(e)))


def get_local_repo_path(repo_url):
    if repo_url in repo_mapping:
        return repo_mapping[repo_url]
    else:
        local_path = f'/home/simetv/lab/techdebt/preprocessing/repos/{repo_url.split("/")[-1].replace(".git", "")}'
        clone_or_update_repo(repo_url, local_path)
        if repo_url not in error_log:
            repo_mapping[repo_url] = local_path
        return local_path


def find_previous_commit(repo_path, file_path, commit_hash):
    # Check if faulty repo
    print(error_log)
    if repo_path in error_log:
        #error_count += 1
        return None

    try:

        repo = git.Repo(repo_path)

        #Check for existence of commit
        if not repo.commit(commit_hash):
            print(f"Commit {commit_hash} does not exist in the repository.")
            error_log.append(repo_path)
            return None

        commit = repo.commit(commit_hash)

        # Iterate through the commit history
        for prev_commit in commit.iter_parents():
            print(prev_commit.tree)
            if file_path in prev_commit.tree:
                return prev_commit.hexsha
    
        return None

    except Exception as e:
        print(f"Error: {e}")
        error_log.append(repo_path)
        #error_count += 1
        return None


for _, row in df.iterrows():
    #commit_hash = row['commit_hash']
    snap_commit_hash = row['commit_hash']
    path = row['path']
    repo = row['repository']

    https_url = repo.replace('git@github.com:', 'https://github.com/')

    local_repo_path = get_local_repo_path(https_url)
    repo_path = os.path.join(local_repo_path, '.git')

    trimmed_path = path.lstrip('/')

    commit_hash = find_previous_commit(repo_path, trimmed_path, snap_commit_hash)

    print(commit_hash)

    smell = row['smell']
    location_entry = {
        'start_line': row['start_line'],
        'end_line': row['end_line']
    }
    
    if commit_hash not in commit_dict:
        commit_dict[commit_hash] = {}
    
    if path not in commit_dict[commit_hash]:
        commit_dict[commit_hash][path] = {'location': path, 'technicalDebts': []}

    technical_debt_entry = next((item for item in commit_dict[commit_hash][path]['technicalDebts'] if item['type'] == smell), None)
                                
    if technical_debt_entry is None:
        technical_debt_entry = {'type': smell, 'locations': []}
        commit_dict[commit_hash][path]['technicalDebts'].append(technical_debt_entry)

    technical_debt_entry['locations'].append(location_entry)

# Convert the nested dictionary to the desired format
final_dict = {commit: list(paths.values()) for commit, paths in commit_dict.items()}  

with open('commit_data.json', 'w') as json_file:
    json.dump(final_dict, json_file, indent=4)