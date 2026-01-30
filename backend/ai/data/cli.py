"""
Data Collection CLI
Command-line interface for running data collection and processing
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Digital Sahayak Data Collection CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  python -m backend.ai.data.cli --run-pipeline
  
  # Generate synthetic data only
  python -m backend.ai.data.cli --generate-synthetic --count 1000
  
  # Analyze existing data
  python -m backend.ai.data.cli --analyze data/processed/training_data.jsonl
  
  # Preprocess/clean raw data
  python -m backend.ai.data.cli --preprocess data/raw/collected.jsonl
  
  # Balance existing dataset
  python -m backend.ai.data.cli --balance data/raw/collected.jsonl --key category
"""
    )
    
    # Actions
    parser.add_argument(
        "--run-pipeline",
        action="store_true",
        help="Run full data collection and processing pipeline"
    )
    parser.add_argument(
        "--generate-synthetic",
        action="store_true",
        help="Generate synthetic training data"
    )
    parser.add_argument(
        "--analyze",
        type=str,
        metavar="FILE",
        help="Analyze distribution of a data file"
    )
    parser.add_argument(
        "--preprocess",
        type=str,
        metavar="FILE",
        help="Preprocess and clean a raw data file"
    )
    parser.add_argument(
        "--balance",
        type=str,
        metavar="FILE",
        help="Balance a data file and save result"
    )
    
    # Options
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output directory"
    )
    parser.add_argument(
        "--count",
        "-n",
        type=int,
        default=1000,
        help="Number of items to generate (for synthetic data)"
    )
    parser.add_argument(
        "--key",
        "-k",
        type=str,
        default="category",
        help="Key to balance by (category, state, etc.)"
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=100,
        help="Minimum samples per class for balancing"
    )
    parser.add_argument(
        "--no-collect",
        action="store_true",
        help="Skip collection step in pipeline"
    )
    parser.add_argument(
        "--no-synthetic",
        action="store_true",
        help="Skip synthetic generation in pipeline"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle actions
    if args.run_pipeline:
        asyncio.run(run_pipeline_cmd(args))
    
    elif args.generate_synthetic:
        generate_synthetic_cmd(args)
    
    elif args.analyze:
        analyze_cmd(args)
    
    elif args.preprocess:
        preprocess_cmd(args)
    
    elif args.balance:
        balance_cmd(args)
    
    else:
        parser.print_help()


async def run_pipeline_cmd(args):
    """Run full data pipeline"""
    from .pipeline import DataPipeline
    
    logger.info("Starting data pipeline...")
    
    pipeline = DataPipeline(
        output_dir=args.output,
        min_samples_per_class=args.min_samples
    )
    
    result = await pipeline.run(
        collect=not args.no_collect,
        balance=True,
        generate_synthetic=not args.no_synthetic,
        export=True
    )
    
    # Print summary
    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"\nStatistics:")
    for key, value in result["statistics"].items():
        print(f"  {key}: {value}")
    
    print(f"\nOutput Files:")
    for key, path in result["output_paths"].items():
        print(f"  {key}: {path}")
    
    print(f"\nDuration: {result['duration_seconds']:.1f} seconds")


def generate_synthetic_cmd(args):
    """Generate synthetic data"""
    from .synthetic import generate_training_dataset
    
    logger.info(f"Generating {args.count} synthetic items...")
    
    output_dir = args.output or (Path(__file__).parent / "generated")
    
    paths = generate_training_dataset(
        num_jobs=args.count,
        num_users=args.count // 2,
        output_dir=str(output_dir)
    )
    
    print("\n" + "="*60)
    print("SYNTHETIC DATA GENERATED")
    print("="*60)
    for key, path in paths.items():
        print(f"  {key}: {path}")


def preprocess_cmd(args):
    """Preprocess and clean raw data file"""
    import json
    from .preprocessor import DataPreprocessor
    
    data_path = Path(args.preprocess)
    if not data_path.exists():
        logger.error(f"File not found: {data_path}")
        sys.exit(1)
    
    # Load data
    data = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    logger.info(f"Loaded {len(data)} records from {data_path}")
    
    # Preprocess
    preprocessor = DataPreprocessor(required_fields=["title"])
    cleaned_data = preprocessor.process(data)
    stats = preprocessor.get_stats()
    
    # Save
    output_path = args.output or data_path.parent / f"{data_path.stem}_cleaned.jsonl"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in cleaned_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    print("\n" + "="*60)
    print("DATA PREPROCESSING COMPLETE")
    print("="*60)
    print(f"\nInput: {data_path}")
    print(f"Output: {output_path}")
    print(f"\nStatistics:")
    print(f"  Total records:        {stats['total_records']}")
    print(f"  Duplicates removed:   {stats['duplicates_removed']}")
    print(f"  Missing handled:      {stats['missing_values_handled']}")
    print(f"  Dates standardized:   {stats['dates_standardized']}")
    print(f"  Numbers standardized: {stats['numbers_standardized']}")
    print(f"  Text cleaned:         {stats['text_cleaned']}")
    print(f"  Fields normalized:    {stats['fields_normalized']}")
    print(f"  Invalid dropped:      {stats['invalid_records_dropped']}")
    print(f"  Final records:        {stats['final_records']}")


def analyze_cmd(args):
    """Analyze data file distribution"""
    import json
    from .balancer import DataBalancer
    
    data_path = Path(args.analyze)
    if not data_path.exists():
        logger.error(f"File not found: {data_path}")
        sys.exit(1)
    
    # Load data
    data = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    
    balancer = DataBalancer()
    
    print("\n" + "="*60)
    print(f"DATA ANALYSIS: {data_path.name}")
    print("="*60)
    print(f"\nTotal samples: {len(data)}")
    
    # Analyze multiple keys
    keys_to_analyze = ["category", "state", "language", "source"]
    
    for key in keys_to_analyze:
        # Check if key exists in data
        if not any(key in item for item in data[:10]):
            continue
        
        dist = balancer.analyze_distribution(data, key)
        
        print(f"\n{key.upper()} Distribution:")
        print(f"  Classes: {dist['num_classes']}")
        print(f"  Imbalance ratio: {dist['imbalance_ratio']}")
        print(f"  Min class: {dist['min_class'][0]} ({dist['min_class'][1]})")
        print(f"  Max class: {dist['max_class'][0]} ({dist['max_class'][1]})")
        
        if dist['num_classes'] <= 10:
            print(f"  Distribution:")
            for cls, count in sorted(dist['distribution'].items(), key=lambda x: -x[1]):
                pct = dist['percentages'].get(cls, 0)
                print(f"    {cls}: {count} ({pct}%)")


def balance_cmd(args):
    """Balance data file"""
    import json
    from .balancer import DataBalancer
    
    data_path = Path(args.balance)
    if not data_path.exists():
        logger.error(f"File not found: {data_path}")
        sys.exit(1)
    
    # Load data
    data = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    
    logger.info(f"Loaded {len(data)} items")
    
    balancer = DataBalancer(target_ratio=0.5)
    
    # Balance
    balanced = balancer.smote_like_augment(
        data, args.key,
        text_fields=["title", "description"],
        target_ratio=0.5
    )
    
    # Save
    output_path = args.output or data_path.parent / f"{data_path.stem}_balanced.jsonl"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in balanced:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    print("\n" + "="*60)
    print("DATA BALANCED")
    print("="*60)
    print(f"  Before: {len(data)}")
    print(f"  After: {len(balanced)}")
    print(f"  Output: {output_path}")


if __name__ == "__main__":
    main()
