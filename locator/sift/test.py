import json
import os
from tqdm import tqdm
from model import ImageLocalizer
from dataload import DataLoader


def test_localization(dataset_root, mode='val', feature_path=None, feature_type='sift', output_file=None):
    print(f"Testing localization on {mode} set...")
    localizer = ImageLocalizer(feature_type=feature_type)
    dataloader = DataLoader(dataset_root)
    if feature_path and os.path.exists(feature_path):
        print(f"Loading features from {feature_path}")
        localizer.database_features, localizer.database_paths = dataloader.load_features(feature_path)
        print(f"Loaded {len(localizer.database_features)} database images")
    else:
        print("Building features on-the-fly...")
        from train import build_database
        localizer.database_features, localizer.database_paths = build_database(
            dataset_root, mode, feature_type
        )
    if len(localizer.database_features) == 0:
        raise ValueError("No database features available")
    query_paths = dataloader.get_query_paths(mode)
    print(f"Found {len(query_paths)} query images")
    if len(query_paths) == 0:
        raise ValueError(f"No query images found in {dataset_root}/{mode}/queries")
    results = {}
    for query_path in tqdm(query_paths, desc="Processing queries"):
        query_name = query_path.name
        similar_images = localizer.query_image(str(query_path), top_k=10)
        results[query_name] = {
            'query_path': str(query_path),
            'similar_images': similar_images
        }
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_file}")
    total_queries = len(results)
    queries_with_matches = sum(1 for r in results.values() if r['similar_images'])
    print(f"\nTest Results:")
    print(f"Total queries: {total_queries}")
    print(f"Queries with matches: {queries_with_matches}")
    if total_queries > 0:
        print(f"Success rate: {queries_with_matches/total_queries*100:.1f}%")
    return results


def test_single_query(query_path, localizer, top_k=5):
    return localizer.query_image(query_path, top_k=top_k)


def calculate_accuracy_metrics(results):
    if not results:
        return {}
    total_queries = len(results)
    queries_with_matches = sum(1 for r in results.values() if r['similar_images'])
    match_scores = []
    for result in results.values():
        if result['similar_images']:
            match_scores.append(result['similar_images'][0][1])
    metrics = {
        'total_queries': total_queries,
        'queries_with_matches': queries_with_matches,
        'success_rate': queries_with_matches / total_queries if total_queries > 0 else 0,
        'avg_best_match_score': sum(match_scores) / len(match_scores) if match_scores else 0,
        'max_match_score': max(match_scores) if match_scores else 0,
        'min_match_score': min(match_scores) if match_scores else 0
    }
    return metrics
