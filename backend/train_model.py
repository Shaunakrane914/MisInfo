"""
Project Aegis - Machine Learning Model Training Script
This script trains a misinformation detection model using TF-IDF vectorization, feature engineering, and XGBoost.
"""

import pandas as pd
import joblib
import numpy as np
import re
import nltk
import xgboost as xgb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
from scipy.sparse import hstack, csr_matrix
import os

# Download required NLTK data
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

try:
    nltk.data.find('punkt')
except LookupError:
    nltk.download('punkt')

# Import NLTK components after ensuring they're downloaded
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk import sent_tokenize, word_tokenize


def text_length(text):
    """Returns character length of text."""
    try:
        return len(str(text))
    except:
        return 0


def sentence_count(text):
    """Returns number of sentences using nltk.sent_tokenize."""
    try:
        return len(sent_tokenize(str(text)))
    except:
        return 0


def avg_word_length(text):
    """Returns average word length using nltk.word_tokenize."""
    try:
        words = word_tokenize(str(text))
        if len(words) == 0:
            return 0
        return np.mean([len(word) for word in words])
    except:
        return 0


def uppercase_ratio(text):
    """Returns the ratio of uppercase characters to total characters."""
    try:
        text_str = str(text)
        if len(text_str) == 0:
            return 0
        uppercase_count = sum(1 for c in text_str if c.isupper())
        return uppercase_count / len(text_str)
    except:
        return 0


def exclamation_count(text):
    """Returns the count of exclamation marks."""
    try:
        return str(text).count('!')
    except:
        return 0


def suspicious_keyword_count(text):
    """Count occurrences of suspicious keywords in the text."""
    try:
        suspicious_keywords = [
            "conspiracy", "hoax", "secret cure", "fake", "exposed", "they don't want you to know",
            "miracle cure", "doctors hate", "cover up", "hidden", "suppressed", "banned",
            "censored", "shocking", "urgent", "alert", "warning", "must read", "breaking",
            "insider", "leak", "proof", "evidence", "undeniable", "truth", "revealed"
        ]
        
        # Compile regex patterns for efficiency
        patterns = [re.compile(re.escape(keyword), re.IGNORECASE) for keyword in suspicious_keywords]
        
        text_str = str(text)
        count = 0
        for pattern in patterns:
            count += len(pattern.findall(text_str))
        return count
    except:
        return 0


def sentiment_score(text):
    """Use VADER to get the compound sentiment score."""
    try:
        analyzer = SentimentIntensityAnalyzer()
        scores = analyzer.polarity_scores(str(text))
        return scores['compound']
    except:
        return 0


def get_text_features(series):
    """
    Apply all feature engineering functions to a pandas Series of text.
    
    Args:
        series: pandas Series of text data
        
    Returns:
        pandas DataFrame containing engineered features
    """
    features = pd.DataFrame({
        'text_length': series.apply(text_length),
        'sentence_count': series.apply(sentence_count),
        'avg_word_length': series.apply(avg_word_length),
        'uppercase_ratio': series.apply(uppercase_ratio),
        'exclamation_count': series.apply(exclamation_count),
        'suspicious_keyword_count': series.apply(suspicious_keyword_count),
        'sentiment_score': series.apply(sentiment_score)
    })
    
    # Handle potential NaN/inf values
    features = features.replace([np.inf, -np.inf], 0)
    features = features.fillna(0)
    
    return features


def load_data():
    """Load train and test datasets from the data directory."""
    print("Loading data...")
    train_df = pd.read_csv('backend/data/train.csv')
    test_df = pd.read_csv('backend/data/test.csv')
    
    # Handle potential Unnamed: 0 columns
    if 'Unnamed: 0' in train_df.columns:
        train_df = train_df.drop(columns=['Unnamed: 0'])
    if 'Unnamed: 0' in test_df.columns:
        test_df = test_df.drop(columns=['Unnamed: 0'])
    
    # Fill any NaN values in the 'text' column with empty strings
    train_df['text'] = train_df['text'].fillna('')
    test_df['text'] = test_df['text'].fillna('')
    
    print(f"Training data shape: {train_df.shape}")
    print(f"Testing data shape: {test_df.shape}")
    
    # Print label distributions
    print("\nTraining label distribution:")
    print(train_df['label'].value_counts())
    print("\nTesting label distribution:")
    print(test_df['label'].value_counts())
    
    return train_df, test_df


def prepare_features_labels(train_df, test_df):
    """
    Separate features and labels.
    
    Args:
        train_df: Training DataFrame
        test_df: Testing DataFrame
    
    Returns:
        X_train_text, X_test_text, y_train, y_test
    """
    print("\nPreparing features and labels...")
    
    # Separate features and labels
    X_train_text = train_df['text']
    y_train = train_df['label']
    X_test_text = test_df['text']
    y_test = test_df['label']
    
    print(f"Training samples: {len(X_train_text)}")
    print(f"Testing samples: {len(X_test_text)}")
    
    return X_train_text, X_test_text, y_train, y_test


def vectorize_text(X_train_text, X_test_text):
    """
    Vectorize text data using TF-IDF.
    
    Args:
        X_train_text: Training text data
        X_test_text: Testing text data
    
    Returns:
        X_train_vectorized, X_test_vectorized, vectorizer
    """
    print("\nVectorizing text using TF-IDF...")
    
    # Initialize TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95
    )
    
    # Fit on training data and transform
    X_train_vectorized = vectorizer.fit_transform(X_train_text)
    
    # Transform test data using the same vectorizer
    X_test_vectorized = vectorizer.transform(X_test_text)
    
    # Print the number of features using string conversion
    try:
        shape_str = str(X_train_vectorized.shape)
        # Extract the second number from the shape string (e.g., "(100, 5000)" -> 5000)
        if ',' in shape_str:
            parts = shape_str.split(',')
            if len(parts) >= 2:
                num_features = parts[1].strip().replace(')', '')
                print(f"Vectorized feature dimensions: {num_features}")
    except:
        print("Vectorized feature dimensions: Unknown")
    
    return X_train_vectorized, X_test_vectorized, vectorizer


def engineer_features(X_train_text, X_test_text):
    """
    Extract engineered features from text data.
    
    Args:
        X_train_text: Training text data (pandas Series)
        X_test_text: Testing text data (pandas Series)
        
    Returns:
        X_train_features, X_test_features, feature_scaler
    """
    print("\nEngineering text features...")
    
    # Extract features
    X_train_features_df = get_text_features(X_train_text)
    X_test_features_df = get_text_features(X_test_text)
    
    # Scale features
    feature_scaler = StandardScaler()
    X_train_features = feature_scaler.fit_transform(X_train_features_df)
    X_test_features = feature_scaler.transform(X_test_features_df)
    
    # Print the number of features using string conversion
    try:
        num_features = X_train_features_df.shape[1]
        print(f"Engineered {num_features} features")
    except:
        print("Engineered features: Unknown count")
    
    return X_train_features, X_test_features, feature_scaler


def combine_features(X_train_tfidf, X_test_tfidf, X_train_engineered, X_test_engineered):
    """
    Combine TF-IDF and engineered features.
    
    Args:
        X_train_tfidf: TF-IDF features for training
        X_test_tfidf: TF-IDF features for testing
        X_train_engineered: Engineered features for training
        X_test_engineered: Engineered features for testing
        
    Returns:
        Combined feature matrices for training and testing
    """
    print("\nCombining TF-IDF and engineered features...")
    
    # Convert dense engineered features to sparse matrices
    X_train_engineered_sparse = csr_matrix(X_train_engineered)
    X_test_engineered_sparse = csr_matrix(X_test_engineered)
    
    # Combine features using horizontal stacking
    X_train_combined = hstack([X_train_tfidf, X_train_engineered_sparse])
    X_test_combined = hstack([X_test_tfidf, X_test_engineered_sparse])
    
    # Print the shapes using string conversion
    try:
        train_shape_str = str(X_train_combined.shape)
        test_shape_str = str(X_test_combined.shape)
        print(f"Combined feature matrix shape - Train: {train_shape_str}, Test: {test_shape_str}")
    except:
        print("Combined feature matrix shape: Unknown")
    
    return X_train_combined, X_test_combined


def train_model(X_train_combined, y_train):
    """
    Train an XGBoost classifier.
    
    Args:
        X_train_combined: Combined training features
        y_train: Training labels
    
    Returns:
        Trained classifier
    """
    print("\nTraining XGBoost model...")
    
    # Initialize and train the classifier
    classifier = xgb.XGBClassifier(
        objective='binary:logistic',
        eval_metric='logloss',
        n_estimators=200,
        learning_rate=0.1,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        random_state=42
    )
    
    classifier.fit(X_train_combined, y_train)
    
    print("Model training completed!")
    
    return classifier


def evaluate_model(classifier, X_test_combined, y_test):
    """
    Evaluate model performance and print classification report.
    
    Args:
        classifier: Trained classifier
        X_test_combined: Combined test features
        y_test: Test labels
    """
    print("\nEvaluating model performance...")
    
    # Make predictions
    y_pred = classifier.predict(X_test_combined)
    y_pred_proba = classifier.predict_proba(X_test_combined)
    
    # Calculate and print accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy: {accuracy:.4f}")
    
    # Generate and print classification report
    print("\n" + "="*60)
    print("CLASSIFICATION REPORT")
    print("="*60)
    report = classification_report(y_test, y_pred, digits=4)
    print(report)
    print("="*60)
    
    # Print sample predicted probabilities
    print("\nSample predicted probabilities (first 10 samples):")
    for i in range(min(10, len(y_pred_proba))):
        print(f"Sample {i+1}: Label={y_test.iloc[i]}, Predicted={y_pred[i]}, Probability=[{y_pred_proba[i][0]:.4f}, {y_pred_proba[i][1]:.4f}]")
    
    return y_pred, y_pred_proba


def save_artifacts(vectorizer, feature_scaler, classifier):
    """
    Save the trained vectorizer, scaler, and classifier to disk.
    
    Args:
        vectorizer: Fitted TF-IDF vectorizer
        feature_scaler: Fitted feature scaler
        classifier: Trained classifier
    """
    print("\nSaving model artifacts...")
    
    # Save vectorizer
    vectorizer_path = 'backend/vectorizer_v2.pkl'
    joblib.dump(vectorizer, vectorizer_path)
    print(f"✓ Vectorizer saved to: {vectorizer_path}")
    
    # Save feature scaler
    scaler_path = 'backend/scaler_v2.pkl'
    joblib.dump(feature_scaler, scaler_path)
    print(f"✓ Feature scaler saved to: {scaler_path}")
    
    # Save classifier
    classifier_path = 'backend/classifier_v2.pkl'
    joblib.dump(classifier, classifier_path)
    print(f"✓ Classifier saved to: {classifier_path}")
    
    # Verify files were created
    if os.path.exists(vectorizer_path) and os.path.exists(scaler_path) and os.path.exists(classifier_path):
        print("\n✓ All artifacts saved successfully!")
        print(f"  - Vectorizer size: {os.path.getsize(vectorizer_path) / 1024:.2f} KB")
        print(f"  - Scaler size: {os.path.getsize(scaler_path) / 1024:.2f} KB")
        print(f"  - Classifier size: {os.path.getsize(classifier_path) / 1024:.2f} KB")
    else:
        print("\n✗ Error: Failed to save artifacts!")


def main():
    """Main execution function."""
    print("="*60)
    print("PROJECT AEGIS - ENHANCED MODEL TRAINING PIPELINE")
    print("="*60)
    
    # Step 1: Load data
    train_df, test_df = load_data()
    
    # Step 2: Prepare features and labels
    X_train_text, X_test_text, y_train, y_test = prepare_features_labels(train_df, test_df)
    
    # Step 3: Vectorize text
    X_train_tfidf, X_test_tfidf, vectorizer = vectorize_text(X_train_text, X_test_text)
    
    # Step 4: Engineer features
    X_train_engineered, X_test_engineered, feature_scaler = engineer_features(X_train_text, X_test_text)
    
    # Step 5: Combine features
    X_train_combined, X_test_combined = combine_features(
        X_train_tfidf, X_test_tfidf, X_train_engineered, X_test_engineered
    )
    
    # Step 6: Train model
    classifier = train_model(X_train_combined, y_train)
    
    # Step 7: Evaluate performance
    evaluate_model(classifier, X_test_combined, y_test)
    
    # Step 8: Save artifacts
    save_artifacts(vectorizer, feature_scaler, classifier)
    
    print("\n" + "="*60)
    print("TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\nNOTE: Remember to update the AnalystAgent code to load vectorizer_v2.pkl, scaler_v2.pkl,")
    print("and classifier_v2.pkl. Include the feature engineering functions and apply the same")
    print("feature transformation steps before making predictions.")


if __name__ == "__main__":
    main()