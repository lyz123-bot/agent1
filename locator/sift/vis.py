import cv2
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def visualize_query_results(query_path, localizer, top_k=6):
    results = localizer.query_image(query_path, top_k=top_k)
    if not results:
        print(f"No results found for {Path(query_path).name}")
        return
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    fig.suptitle(f'Query Results: {Path(query_path).name}', fontsize=14)
    query_img = cv2.imread(query_path)
    query_img = cv2.cvtColor(query_img, cv2.COLOR_BGR2RGB)
    axes[0, 0].imshow(query_img)
    axes[0, 0].set_title('Query Image')
    axes[0, 0].axis('off')
    positions = [(0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)]
    for i, ((db_name, score), (row, col)) in enumerate(zip(results, positions)):
        if i >= len(positions):
            break
        db_path = localizer.database_paths[db_name]
        db_img = cv2.imread(db_path)
        db_img = cv2.cvtColor(db_img, cv2.COLOR_BGR2RGB)
        axes[row, col].imshow(db_img)
        axes[row, col].set_title(f'#{i + 1}: {score} matches\n{db_name[:20]}...', fontsize=10)
        axes[row, col].axis('off')
    for i in range(len(results), len(positions)):
        row, col = positions[i]
        axes[row, col].axis('off')
    axes[1, 3].axis('off')
    plt.tight_layout()
    plt.show()


def visualize_feature_matches(query_path, db_name, localizer):
    query_img = cv2.imread(query_path, cv2.IMREAD_GRAYSCALE)
    db_path = localizer.database_paths[db_name]
    db_img = cv2.imread(db_path, cv2.IMREAD_GRAYSCALE)
    query_kp, query_desc = localizer.extractor.extract(query_path)
    db_kp, db_desc = localizer.extractor.extract(db_path)
    matches = localizer.matcher.match(query_desc, db_desc)
    match_img = cv2.drawMatches(query_img, query_kp, db_img, db_kp,
                                matches[:50], None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    plt.figure(figsize=(15, 8))
    plt.imshow(match_img, cmap='gray')
    plt.title(f'Feature Matches: {Path(query_path).name} vs {db_name} ({len(matches)} matches)')
    plt.axis('off')
    plt.show()


def visualize_results_gallery(results, max_queries=9):
    query_names = list(results.keys())[:max_queries]
    rows = int(np.ceil(len(query_names) / 3))
    fig, axes = plt.subplots(rows, 3, figsize=(15, 5 * rows))
    fig.suptitle('Query Results Gallery', fontsize=16)
    if rows == 1:
        axes = axes.reshape(1, -1)
    for i, query_name in enumerate(query_names):
        row = i // 3
        col = i % 3
        query_data = results[query_name]
        query_path = query_data['query_path']
        try:
            query_img = cv2.imread(query_path)
            query_img = cv2.cvtColor(query_img, cv2.COLOR_BGR2RGB)
            axes[row, col].imshow(query_img)
            if query_data['similar_images']:
                best_match = query_data['similar_images'][0]
                title = f'{query_name[:15]}...\nBest: {best_match[1]} matches'
            else:
                title = f'{query_name[:15]}...\nNo matches'
            axes[row, col].set_title(title, fontsize=10)
            axes[row, col].axis('off')
        except:
            axes[row, col].text(0.5, 0.5, f'Error loading\n{query_name}',
                                ha='center', va='center')
            axes[row, col].axis('off')
    for i in range(len(query_names), rows * 3):
        row = i // 3
        col = i % 3
        axes[row, col].axis('off')
    plt.tight_layout()
    plt.show()


def auto_visualize_best_results(dataset_root, localizer, results, max_queries=6):
    print(f"\nVisualizing top {max_queries} query results...")
    queries_with_matches = []
    for query_name, query_data in results.items():
        if query_data['similar_images'] and len(query_data['similar_images']) > 0:
            queries_with_matches.append((query_name, query_data))
    if not queries_with_matches:
        print("No queries with matches found for visualization")
        return
    queries_with_matches.sort(key=lambda x: x[1]['similar_images'][0][1], reverse=True)
    selected_queries = queries_with_matches[:max_queries]
    print(f"Found {len(queries_with_matches)} queries with matches")
    print(f"Visualizing top {len(selected_queries)} queries...")
    for i, (query_name, query_data) in enumerate(selected_queries, 1):
        query_path = query_data['query_path']
        best_match_score = query_data['similar_images'][0][1]
        print(f"\n[{i}/{len(selected_queries)}] Visualizing: {query_name}")
        print(f"Best match score: {best_match_score}")
        try:
            visualize_query_results(query_path, localizer, top_k=6)
        except Exception as e:
            print(f"Error visualizing {query_name}: {e}")
    print("\nShowing results gallery...")
    try:
        visualize_results_gallery(results, max_queries=9)
    except Exception as e:
        print(f"Error showing gallery: {e}")


def show_best_match_details(query_path, localizer):
    results = localizer.query_image(query_path, top_k=3)
    if not results:
        print("No matches found")
        return
    print(f"\nBest matches for {Path(query_path).name}:")
    for i, (db_name, score) in enumerate(results, 1):
        print(f"  {i}. {db_name}: {score} matches")
    best_match = results[0][0]
    print(f"\nShowing feature matches with best result: {best_match}")
    visualize_feature_matches(query_path, best_match, localizer)
