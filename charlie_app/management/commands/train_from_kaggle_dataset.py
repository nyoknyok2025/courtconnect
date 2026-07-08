from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from charlie_app.ml_service import (
    download_kaggle_dataset,
    load_training_rows_from_file,
    train_and_save_model,
)


class Command(BaseCommand):
    help = 'Train a pretrained classifier from a Kaggle dataset or a local file'

    def add_arguments(self, parser):
        parser.add_argument('--dataset', dest='dataset_slug', help='Kaggle dataset slug, for example owner/dataset-name')
        parser.add_argument('--file', dest='dataset_file', help='Local path to a CSV, JSON, Excel, parquet, pickle, or .px file')

    def handle(self, *args, **options):
        dataset_slug = options.get('dataset_slug')
        dataset_file = options.get('dataset_file')

        if not dataset_slug and not dataset_file:
            raise CommandError('Provide --dataset for a Kaggle download or --file for a local file')

        if dataset_slug:
            download_dir = download_kaggle_dataset(dataset_slug)
            candidate_files = sorted(download_dir.glob('*'))
            dataset_path = None
            for candidate in candidate_files:
                if candidate.is_file() and candidate.suffix.lower() in {'.csv', '.json', '.xlsx', '.xls', '.parquet', '.pkl', '.pickle', '.joblib', '.px'}:
                    dataset_path = candidate
                    break
            if dataset_path is None:
                raise CommandError(f'No supported dataset file was found in {download_dir}')
            self.stdout.write(self.style.SUCCESS(f'Downloaded Kaggle dataset files to {download_dir}'))
            source_path = dataset_path
        else:
            source_path = Path(dataset_file)

        if not source_path.exists():
            raise CommandError(f'Dataset file not found: {source_path}')

        training_rows = load_training_rows_from_file(source_path)
        if not training_rows:
            raise CommandError('No usable training rows were found in the provided dataset')

        model_path = train_and_save_model(force=True, training_rows=training_rows)
        self.stdout.write(self.style.SUCCESS(f'Pretrained classifier saved to {model_path}'))
