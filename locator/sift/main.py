import argparse
import sys
import os
import vis
from train import build_database
from test import test_localization, calculate_accuracy_metrics


def main():
    parser = argparse.ArgumentParser(description='Image Localization System')
    parser.add_argument('command', choices=['train', 'test'], help='Command to run')
    parser.add_argument('--dataset_root', type=str, required=True, help='Dataset root directory')
    parser.add_argument('--mode', type=str, choices=['train', 'val', 'test'], default='val')
    parser.add_argument('--feature_type', type=str, choices=['sift', 'orb'], default='sift')
    parser.add_argument('--feature_path', type=str, help='Path to save/load features')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--vis_count', type=int, default=6, help='Number of queries to visualize (default: 6)')
    args = parser.parse_args()
    if not os.path.exists(args.dataset_root):
        print(f"Error: Dataset root does not exist: {args.dataset_root}")
        sys.exit(1)
    if args.command == 'train':
        save_path = args.feature_path or f'{args.mode}_features.pkl'
        print(f"Building database for {args.mode} set...")
        print(f"Feature type: {args.feature_type}")
        print(f"Output: {save_path}")
        try:
            build_database(
                dataset_root=args.dataset_root,
                mode=args.mode,
                feature_type=args.feature_type,
                save_path=save_path
            )
            if args.mode == 'val':
                print("\n" + "="*50)
                print("visualizing validation results...")
                print("="*50)
                from model import ImageLocalizer
                from dataload import DataLoader
                localizer = ImageLocalizer(feature_type=args.feature_type)
                dataloader = DataLoader(args.dataset_root)
                localizer.database_features, localizer.database_paths = dataloader.load_features(save_path)
                print("Testing validation set...")
                results_file = "val_results.json"
                results = test_localization(
                    dataset_root=args.dataset_root,
                    mode='val',
                    feature_path=save_path,
                    feature_type=args.feature_type,
                    output_file=results_file
                )
                metrics = calculate_accuracy_metrics(results)
                print(f"\nDetailed Metrics:")
                print(f"Success Rate: {metrics['success_rate']*100:.1f}%")
                print(f"Avg Best Match Score: {metrics['avg_best_match_score']:.1f}")
                print(f"Max Match Score: {metrics['max_match_score']}")
                vis.auto_visualize_best_results(args.dataset_root, localizer, results, args.vis_count)
                print("\nVisualization complete!")
            else:
                print(f"\nNote: Auto-visualization is only available for 'val' mode.")
                print(f"You can manually test {args.mode} results using:")
                print(f"python main.py test --dataset_root {args.dataset_root} --mode {args.mode} --feature_path {save_path}")
        except Exception as e:
            print(f"Training failed: {e}")
            sys.exit(1)
    elif args.command == 'test':
        if not args.feature_path:
            print("Error: --feature_path is required for test mode")
            sys.exit(1)
        if not os.path.exists(args.feature_path):
            print(f"Error: Feature file does not exist: {args.feature_path}")
            sys.exit(1)
        output_file = args.output or f'{args.mode}_results.json'
        print(f"Testing {args.mode} set...")
        print(f"Feature file: {args.feature_path}")
        print(f"Output: {output_file}")
        try:
            results = test_localization(
                dataset_root=args.dataset_root,
                mode=args.mode,
                feature_path=args.feature_path,
                feature_type=args.feature_type,
                output_file=output_file
            )
            metrics = calculate_accuracy_metrics(results)
            print(f"\nDetailed Metrics:")
            print(f"Success Rate: {metrics['success_rate']*100:.1f}%")
            print(f"Avg Best Match Score: {metrics['avg_best_match_score']:.1f}")
            from model import ImageLocalizer
            from dataload import DataLoader
            localizer = ImageLocalizer(feature_type=args.feature_type)
            dataloader = DataLoader(args.dataset_root)
            localizer.database_features, localizer.database_paths = dataloader.load_features(args.feature_path)
            vis.visualize_results_gallery(results, max_queries=9)
            if results:
                first_query = list(results.keys())[0]
                first_query_path = results[first_query]['query_path']
                vis.show_best_match_details(first_query_path, localizer)
        except Exception as e:
            print(f"Testing failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
