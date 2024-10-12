import json
import matplotlib.pyplot as plt
from MetricsHandler import MetricsHandler

# Function to load results from JSON file
def carica_risultati_json(filepath):
    with open(filepath, 'r') as json_file:
        return json.load(json_file)

# Function to calculate the average precision and recall for all files in the JSON
def calcola_media_precision_recall(saved_results):
    precision_sums = {
        'library_name_version': [],
        'library_name_only': [],
        'filename_library_name_version': [],
        'filename_library_name_only': []
    }
    recall_sums = {
        'library_name_version': [],
        'library_name_only': [],
        'filename_library_name_version': [],
        'filename_library_name_only': []
    }

    file_count = len(saved_results)

    for method in precision_sums.keys():
        max_k = 10  # Assume a constant max_k
        precision_sums[method] = [0] * max_k
        recall_sums[method] = [0] * max_k

    for file_path, metrics in saved_results.items():
        for method in precision_sums.keys():
            precision = metrics[method]['precision']
            recall = metrics[method]['recall']

            for i in range(len(precision)):
                precision_sums[method][i] += precision[i]
                recall_sums[method][i] += recall[i]

    precision_means = {method: [p / file_count for p in precision_sums[method]] for method in precision_sums.keys()}
    recall_means = {method: [r / file_count for r in recall_sums[method]] for method in recall_sums.keys()}

    return precision_means, recall_means

# Function to plot the comparison between precision and recall of two files.
def plot_confronto_precision_recall(precision_means1, recall_means1, precision_means2, recall_means2):
    plt.figure(figsize=(12, 12))

    metodologie = [
        'library_name_version',
        'library_name_only',
        'filename_library_name_version',
        'filename_library_name_only'
    ]

    # Mapping to convert method names to desired titles
    method_titles = {
        'library_name_version': 'library name + version',
        'library_name_only': 'library name only',
        'filename_library_name_version': 'filename + library name + version',
        'filename_library_name_only': 'filename + library name only'
    }

    # Plots the graphs in a 2x2 grid
    for i, method in enumerate(metodologie):
        plt.subplot(2, 2, i + 1)
        precision1 = precision_means1[method]
        recall1 = recall_means1[method]
        precision2 = precision_means2[method]
        recall2 = recall_means2[method]
        
        # Manual plot creation with different styles
        plt.plot(range(1, len(precision1) + 1), precision1, label='Precision (Optimization O0)', color='orange', linestyle='-', marker='o')
        plt.plot(range(1, len(recall1) + 1), recall1, label='Recall (Optimization O0)', color='orange', linestyle='--', marker='s')
        plt.plot(range(1, len(precision2) + 1), precision2, label='Precision (Optimization O3)', color='red', linestyle='-', marker='o')
        plt.plot(range(1, len(recall2) + 1), recall2, label='Recall (Optimization O3)', color='red', linestyle='--', marker='s')
        
        plt.title(f'Comparison: {method_titles[method]}')
        plt.xlabel('k')
        plt.ylabel('Value (%)')
        
        # Customization of x and y axis labels
        plt.xticks(range(1, 11))  # Show all values from 1 to 10 on the x-axis
        plt.yticks(range(0, 101, 10))  # Show values from 0 to 100 on the y-axis, with step of 10

        # Set the same scale for all charts
        plt.ylim(-5, 105)  # Extend a bit beyond 100 to avoid overlapping at maximum values
        plt.yticks(range(0, 101, 10))  # Tick from 0 to 100 with increments of 10

        plt.legend(loc='best')
        plt.grid(True)

    # Adjustment of spaces between the charts
    plt.subplots_adjust(wspace=0.6, hspace=1.2)
    plt.tight_layout()
    plt.show()

# Function to calculate the average percentage difference between precision and recall means
def calcola_differenza_percentuale_media(precision_means1, recall_means1, precision_means2, recall_means2):
    differenze_percentuali_medie = {}

    metodologie = [
        'library_name_version',
        'library_name_only',
        'filename_library_name_version',
        'filename_library_name_only'
    ]

    for method in metodologie:
        # Calculation of percentage differences for precision
        precision_diff = [
            100 * (p2 - p1) / p1 if p1 != 0 else 0
            for p1, p2 in zip(precision_means1[method], precision_means2[method])
        ]
        # Calculation of percentage differences for recall
        recall_diff = [
            100 * (r2 - r1) / r1 if r1 != 0 else 0
            for r1, r2 in zip(recall_means1[method], recall_means2[method])
        ]

        # Calculation of the average of the percentage differences
        precision_diff_media = sum(precision_diff) / len(precision_diff)
        recall_diff_media = sum(recall_diff) / len(recall_diff)

        differenze_percentuali_medie[method] = {
            'precision_diff_media': precision_diff_media,
            'recall_diff_media': recall_diff_media
        }

    return differenze_percentuali_medie

# Function to print the average percentage difference
def stampa_differenze_percentuali_medie(differenze_percentuali_medie):
    for method, diff in differenze_percentuali_medie.items():
        print(f"\nMetodologia: {method}")
        precision_diff = diff['precision_diff_media']
        recall_diff = diff['recall_diff_media']
        print(f"Precision difference: {'+' if precision_diff >= 0 else ''}{precision_diff:.2f}%")
        print(f"Recall difference: {'+' if recall_diff >= 0 else ''}{recall_diff:.2f}%")

# Main function for comparison
def confronta_due_file_metrics(file1_path, file2_path):
    # Load results from the two JSON files
    saved_results1 = carica_risultati_json(file1_path)
    saved_results2 = carica_risultati_json(file2_path)

    # Calculate precision and recall means for both files
    precision_means1, recall_means1 = calcola_media_precision_recall(saved_results1)
    precision_means2, recall_means2 = calcola_media_precision_recall(saved_results2)

    # Plot the comparison between the two files
    plot_confronto_precision_recall(precision_means1, recall_means1, precision_means2, recall_means2)

    # Calculate the average percentage differences between the two files
    differenze_percentuali_medie = calcola_differenza_percentuale_media(precision_means1, recall_means1, precision_means2, recall_means2)

    # Print the average percentage differences
    stampa_differenze_percentuali_medie(differenze_percentuali_medie)

# Execute the comparison between two specified files
if __name__ == "__main__":
    file1 = 'metricsresult4files1.json'
    file2 = 'metricsresult4files2.json'
    confronta_due_file_metrics(file1, file2)
