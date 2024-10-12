import json
import matplotlib.pyplot as plt
from MetricsHandler import MetricsHandler

# Function to load results from the JSON file
def carica_risultati_json(filepath):
    with open(filepath, 'r') as json_file:
        return json.load(json_file)

# Function to print results from the comparisonresult.json file
def stampa_comparison_results(comparison_results):
    print("\n--- Results from comparisonresult.json ---\n")

    for db_name, results in comparison_results.items():
        print(f"\nResults for {db_name}:")
        
        # Print similarity scores without normalization
        print("\nSimilarity Scores (Without Normalization):")
        for comparison in results['without_normalization']:
            print(f"File1: {comparison['file1']}, File2: {comparison['file2']}, Similarity: {comparison['similarity_score']:.4f}")

        # Print similarity scores with normalization
        print("\nSimilarity Scores (With Normalization):")
        for comparison in results['with_normalization']:
            print(f"File1: {comparison['file1']}, File2: {comparison['file2']}, Normalized Similarity: {comparison['similarity_score_normalized']:.4f}")

        # Display similarity charts
        plot_comparison_results(results)

# Function to plot similarity results
def plot_comparison_results(results):
    # Prepare data for the chart
    similarity_scores = [comp['similarity_score'] for comp in results['without_normalization']]
    normalized_scores = [comp['similarity_score_normalized'] for comp in results['with_normalization']]
    comparisons = list(range(1, len(similarity_scores) + 1))  # Comparison number

    # Plotting
    plt.figure(figsize=(14, 6))

    # Chart 1: Similarity Scores (Without Normalization)
    plt.subplot(1, 2, 1)
    plt.plot(comparisons, similarity_scores, marker='o', linestyle='-', color='blue', label='Similarity (Without Normalization)')
    plt.xlabel('Comparison Number')
    plt.ylabel('Similarity Score')
    plt.title('Similarity Scores (Without Normalization)')
    plt.grid(True)

    # Chart 2: Similarity Scores (With Normalization)
    plt.subplot(1, 2, 2)
    plt.plot(comparisons, normalized_scores, marker='o', linestyle='-', color='green', label='Similarity (With Normalization)')
    plt.xlabel('Comparison Number')
    plt.ylabel('Normalized Similarity Score')
    plt.title('Similarity Scores (With Normalization)')
    plt.grid(True)

    plt.tight_layout()
    plt.show()

# Function to print metrics results from the metricsresult.json file
def stampa_metrics_results(saved_results):
    for file_path, metrics in saved_results.items():
        print(f"\nResults for {file_path}:")
        
        # Library Name + Version
        print("\nLibrary Name + Version:")
        print(f"Relevant and total:", metrics['library_name_version']['relevant_total'])
        print(f"Precision:", metrics['library_name_version']['precision'])
        print(f"Recall:", metrics['library_name_version']['recall'])
        
        # Library Name Only
        print("\nLibrary Name Only:")
        print(f"Relevant and total:", metrics['library_name_only']['relevant_total'])
        print(f"Precision:", metrics['library_name_only']['precision'])
        print(f"Recall:", metrics['library_name_only']['recall'])
        
        # Filename + Library Name + Version
        print("\nFilename + Library Name + Version:")
        print(f"Relevant and total:", metrics['filename_library_name_version']['relevant_total'])
        print(f"Precision:", metrics['filename_library_name_version']['precision'])
        print(f"Recall:", metrics['filename_library_name_version']['recall'])
        
        # Filename + Library Name Only
        print("\nFilename + Library Name Only:")
        print(f"Relevant and total:", metrics['filename_library_name_only']['relevant_total'])
        print(f"Precision:", metrics['filename_library_name_only']['precision'])
        print(f"Recall:", metrics['filename_library_name_only']['recall'])

        # Display precision and recall charts
        plot_metrics_results(metrics)

# Function to plot metric charts
def plot_metrics_results(metrics):
    plt.figure(figsize=(12, 12))

    # Chart 1: Precision & Recall (library_name_version)
    plt.subplot(2, 2, 1)
    precision = metrics['library_name_version']['precision']
    recall = metrics['library_name_version']['recall']
    MetricsHandler.plot_precision_recall_combined(precision, recall, 'Precision & Recall (library name + version)', max_k=len(precision))

    # Chart 2: Precision & Recall (library_name_only)
    plt.subplot(2, 2, 2)
    precision = metrics['library_name_only']['precision']
    recall = metrics['library_name_only']['recall']
    MetricsHandler.plot_precision_recall_combined(precision, recall, 'Precision & Recall (library name only)', max_k=len(precision))

    # Chart 3: Precision & Recall (filename_library_name_version)
    plt.subplot(2, 2, 3)
    precision = metrics['filename_library_name_version']['precision']
    recall = metrics['filename_library_name_version']['recall']
    MetricsHandler.plot_precision_recall_combined(precision, recall, 'Precision & Recall (filename + library name + version)', max_k=len(precision))

    # Chart 4: Precision & Recall (filename_library_name_only)
    plt.subplot(2, 2, 4)
    precision = metrics['filename_library_name_only']['precision']
    recall = metrics['filename_library_name_only']['recall']
    MetricsHandler.plot_precision_recall_combined(precision, recall, 'Precision & Recall (filename + library name only)', max_k=len(precision))

    # Adjust the space between the charts
    plt.subplots_adjust(wspace=0.5, hspace=1.0)

    plt.tight_layout()
    plt.show()

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
        max_k = 10  # Suppose a max_k constant
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

# Function to plot average precision and recall
def plot_medie_precision_recall(precision_means, recall_means):
    plt.figure(figsize=(12, 12))

    metodologie = [
        'library_name_version',
        'library_name_only',
        'filename_library_name_version',
        'filename_library_name_only'
    ]

    # Mapping to convert methodology names into desired titles
    method_titles = {
        'library_name_version': 'library name + version',
        'library_name_only': 'library name only',
        'filename_library_name_version': 'filename + library name + version',
        'filename_library_name_only': 'filename + library name only'
    }

    # Plot the charts in a 2x2 grid
    for i, method in enumerate(metodologie):
        plt.subplot(2, 2, i + 1)
        precision = precision_means[method]
        recall = recall_means[method]
        # Use the mapping to get the correct title
        title = method_titles[method]
        MetricsHandler.plot_precision_recall_combined(precision, recall, f'Precision mean & Recall mean ({title})', max_k=len(precision))

    # Adjust the space between the charts with larger values
    plt.subplots_adjust(wspace=0.6, hspace=1.2)

    plt.tight_layout()
    plt.show()


# Main
def main():
    # Load results from JSON files
    saved_results = carica_risultati_json('metricsresult4files.json')
    comparison_results = carica_risultati_json('comparisonresult.json')

    # Print results from comparisonresult.json
    #stampa_comparison_results(comparison_results)

    # Print results from metricsresult.json
    #stampa_metrics_results(saved_results)

    # Calculate average precision and recall
    precision_means, recall_means = calcola_media_precision_recall(saved_results)

    # Print averages
    for method in precision_means.keys():
        print(f"\nAverages for methodology {method}:")
        print("Precision (media per ogni k):", precision_means[method])
        print("Recall (media per ogni k):", recall_means[method])

    # Plot averages
    plot_medie_precision_recall(precision_means, recall_means)

# Program start
if __name__ == "__main__":
    main()
