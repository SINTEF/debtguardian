import pandas as pd

# Read the CSV file
df = pd.read_csv('/home/simetv/lab/techdebt/preprocessing/data/MLCQCodeSmellSamples.csv', delimiter=';')

# Sort the DataFrame by the 'commit_hash' column
df_sorted = df.sort_values(by='commit_hash')

# Write the sorted DataFrame back to a CSV file
df_sorted.to_csv('/home/simetv/lab/techdebt/preprocessing/data/OrderedSamples_MLCQ.csv', index=False)

print("CSV file sorted successfully.")