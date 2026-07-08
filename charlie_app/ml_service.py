import json
from pathlib import Path
from typing import Dict, List

from django.conf import settings


def get_dataset_path() -> Path:
    return Path(settings.BASE_DIR) / 'charlie_app' / 'data' / 'pretrained_report_examples.json'


def get_model_path() -> Path:
    return Path(settings.BASE_DIR) / 'charlie_app' / 'ml_assets' / 'report_category_model.joblib'


def load_pretrained_dataset() -> List[Dict[str, str]]:
    dataset_path = get_dataset_path()
    if dataset_path.exists():
        with dataset_path.open('r', encoding='utf-8') as handle:
            return json.load(handle)

    dataset = [
        {"text": "a government officer demanded money to process a permit", "label": "bribery"},
        {"text": "the clinic had a broken ambulance and dirty waiting room", "label": "unsafe_service"},
        {"text": "the public office delayed my certificate without explanation", "label": "governance"},
        {"text": "a staff member insulted citizens at the tax station", "label": "misconduct"},
        {"text": "the school lacked proper safety equipment and lighting", "label": "unsafe_service"},
        {"text": "someone offered a payment to skip an inspection", "label": "corruption"},
        {"text": "a civil servant ignored my complaint for months", "label": "governance"},
        {"text": "an official used public funds for personal expenses", "label": "corruption"},
        {"text": "the hospital refused urgent treatment because of paperwork", "label": "unsafe_service"},
        {"text": "a police officer behaved unprofessionally during an arrest", "label": "misconduct"},
    ]

    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    with dataset_path.open('w', encoding='utf-8') as handle:
        json.dump(dataset, handle, indent=2)

    return dataset


def _coerce_training_rows(raw_data) -> List[Dict[str, str]]:
    if isinstance(raw_data, dict):
        if 'records' in raw_data:
            raw_data = raw_data['records']
        elif 'data' in raw_data and 'labels' in raw_data:
            return [
                {'text': str(text), 'label': str(label)}
                for text, label in zip(raw_data['data'], raw_data['labels'])
            ]

    if isinstance(raw_data, list):
        if not raw_data:
            return []
        if isinstance(raw_data[0], dict):
            text_keys = ('text', 'description', 'content', 'message', 'review', 'comment')
            label_keys = ('label', 'category', 'target', 'class', 'output')

            rows = []
            for item in raw_data:
                text_value = next((item[key] for key in text_keys if key in item and item[key] is not None), None)
                label_value = next((item[key] for key in label_keys if key in item and item[key] is not None), None)
                if text_value is not None and label_value is not None:
                    rows.append({'text': str(text_value), 'label': str(label_value)})
            if rows:
                return rows

    raise ValueError('Unsupported training data format. Expected a list of objects or a dict with data/labels.')


def load_training_rows_from_file(file_path) -> List[Dict[str, str]]:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == '.json':
        with path.open('r', encoding='utf-8') as handle:
            return _coerce_training_rows(json.load(handle))

    if suffix == '.csv':
        import pandas as pd
        dataframe = pd.read_csv(path)
        return _coerce_training_rows(dataframe.to_dict(orient='records'))

    if suffix in {'.xlsx', '.xls'}:
        import pandas as pd
        dataframe = pd.read_excel(path)
        return _coerce_training_rows(dataframe.to_dict(orient='records'))

    if suffix in {'.parquet'}:
        import pandas as pd
        dataframe = pd.read_parquet(path)
        return _coerce_training_rows(dataframe.to_dict(orient='records'))

    if suffix in {'.pkl', '.pickle', '.joblib', '.px'}:
        import pickle
        with path.open('rb') as handle:
            return _coerce_training_rows(pickle.load(handle))

    raise ValueError(f'Unsupported file type: {suffix}')


def download_kaggle_dataset(dataset_slug: str, destination_dir=None) -> Path:
    import shutil
    import subprocess

    destination = Path(destination_dir or Path(settings.BASE_DIR) / 'charlie_app' / 'data' / 'kaggle_download')
    destination.mkdir(parents=True, exist_ok=True)

    if shutil.which('kaggle') is None:
        raise RuntimeError('Kaggle CLI is not installed. Install it with: pip install kaggle')

    command = ['kaggle', 'datasets', 'download', '-d', dataset_slug, '-p', str(destination)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or 'Kaggle download failed')

    return destination


def train_and_save_model(force: bool = False, training_rows=None):
    import joblib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    model_path = get_model_path()
    if model_path.exists() and not force:
        return model_path

    dataset = training_rows or load_pretrained_dataset()
    texts = [item['text'] for item in dataset]
    labels = [item['label'] for item in dataset]

    pipeline = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2)),
        LogisticRegression(max_iter=2000),
    )
    pipeline.fit(texts, labels)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    return model_path


def predict_report_category(text: str) -> Dict[str, object]:
    import joblib

    # Load separate vectorizer and classifier (new two-file structure)
    vectorizer_path = Path(settings.BASE_DIR) / 'charlie_app' / 'ml_assets' / 'tfidf_vectorizer.joblib'
    classifier_path = Path(settings.BASE_DIR) / 'charlie_app' / 'ml_assets' / 'report_classifier.joblib'
    
    # Fallback to old single-file pipeline if new files don't exist
    if not vectorizer_path.exists() or not classifier_path.exists():
        model_path = get_model_path()
        if model_path.exists():
            # Fall back to old pipeline
            pipeline = joblib.load(model_path)
            prediction = pipeline.predict([text])[0]
            probabilities = pipeline.predict_proba([text])[0]
            confidence = round(float(max(probabilities)), 3)
        else:
            # Train new model
            train_and_save_model()
            return {'error': 'Models not trained yet. Please retry.', 'category': 'other', 'confidence': 0}
    else:
        # Load new two-file structure: vectorizer + LinearSVC classifier
        vectorizer = joblib.load(vectorizer_path)
        classifier = joblib.load(classifier_path)
        
        # Transform text using vectorizer, then predict with classifier
        text_vec = vectorizer.transform([text])
        prediction = classifier.predict(text_vec)[0]
        
        # LinearSVC uses decision_function instead of predict_proba
        # Calculate confidence from decision scores
        decision_scores = classifier.decision_function(text_vec)[0]
        confidence = round(float(max(abs(decision_scores)) / (1 + sum(abs(decision_scores)))), 3)

    return {
        'category': prediction,
        'confidence': confidence,
    }
