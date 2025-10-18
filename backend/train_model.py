"""
Project Aegis - Machine Learning Model Training Script
This script trains a phishing detection model using TF-IDF vectorization and Logistic Regression.
"""

import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import os

def load_data():
    """Load train and test datasets from the data directory."""
    print("Loading data...")
    train_df = pd.read_csv('data/train.csv')
    test_df = pd.read_csv('data/test.csv')
    
    print(f"Training data shape: {train_df.shape}")
    print(f"Testing data shape: {test_df.shape}")
    
    return train_df, test_df

def prepare_features_labels(train_df, test_df):
    """
    Separate features and labels, and handle empty text rows.
    
    Args:
        train_df: Training DataFrame
        test_df: Testing DataFrame
    
    Returns:
        X_train, X_test, y_train, y_test
    """
    print("\nPreparing features and labels...")
    
    # Drop rows with empty or NaN text
    train_df = train_df.dropna(subset=['text'])
    test_df = test_df.dropna(subset=['text'])
    
    # Remove rows where text is empty string
    train_df = train_df[train_df['text'].str.strip() != '']
    test_df = test_df[test_df['text'].str.strip() != '']
    
    # Separate features and labels
    X_train = train_df['text']
    y_train = train_df['label']
    X_test = test_df['text']
    y_test = test_df['label']
    
    print(f"Training samples after cleaning: {len(X_train)}")
    print(f"Testing samples after cleaning: {len(X_test)}")
    
    return X_train, X_test, y_train, y_test

def vectorize_text(X_train, X_test):
    """
    Vectorize text data using TF-IDF.
    
    Args:
        X_train: Training text data
        X_test: Testing text data
    
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
    X_train_vectorized = vectorizer.fit_transform(X_train)
    
    # Transform test data using the same vectorizer
    X_test_vectorized = vectorizer.transform(X_test)
    
    print(f"Vectorized feature dimensions: {X_train_vectorized.shape[1]}")
    
    return X_train_vectorized, X_test_vectorized, vectorizer

def train_model(X_train_vectorized, y_train):
    """
    Train a Logistic Regression classifier.
    
    Args:
        X_train_vectorized: Vectorized training features
        y_train: Training labels
    
    Returns:
        Trained classifier
    """
    print("\nTraining Logistic Regression model...")
    
    # Initialize and train the classifier
    classifier = LogisticRegression(
        max_iter=1000,
        random_state=42,
        solver='lbfgs'
    )
    
    classifier.fit(X_train_vectorized, y_train)
    
    print("Model training completed!")
    
    return classifier

def evaluate_model(classifier, X_test_vectorized, y_test):
    """
    Evaluate model performance and print classification report.
    
    Args:
        classifier: Trained classifier
        X_test_vectorized: Vectorized test features
        y_test: Test labels
    """
    print("\nEvaluating model performance...")
    
    # Make predictions
    y_pred = classifier.predict(X_test_vectorized)
    
    # Generate and print classification report
    print("\n" + "="*60)
    print("CLASSIFICATION REPORT")
    print("="*60)
    report = classification_report(y_test, y_pred, digits=4)
    print(report)
    print("="*60)
    
    return y_pred

def save_artifacts(vectorizer, classifier):
    """
    Save the trained vectorizer and classifier to disk.
    
    Args:
        vectorizer: Fitted TF-IDF vectorizer
        classifier: Trained classifier
    """
    print("\nSaving model artifacts...")
    
    # Save vectorizer
    vectorizer_path = 'vectorizer.pkl'
    joblib.dump(vectorizer, vectorizer_path)
    print(f"✓ Vectorizer saved to: {vectorizer_path}")
    
    # Save classifier
    classifier_path = 'classifier.pkl'
    joblib.dump(classifier, classifier_path)
    print(f"✓ Classifier saved to: {classifier_path}")
    
    # Verify files were created
    if os.path.exists(vectorizer_path) and os.path.exists(classifier_path):
        print("\n✓ All artifacts saved successfully!")
        print(f"  - Vectorizer size: {os.path.getsize(vectorizer_path) / 1024:.2f} KB")
        print(f"  - Classifier size: {os.path.getsize(classifier_path) / 1024:.2f} KB")
    else:
        print("\n✗ Error: Failed to save artifacts!")

def main():
    """Main execution function."""
    print("="*60)
    print("PROJECT AEGIS - MODEL TRAINING PIPELINE")
    print("="*60)
    
    # Step 1: Load data
    train_df, test_df = load_data()
    
    # Step 2: Prepare features and labels
    X_train, X_test, y_train, y_test = prepare_features_labels(train_df, test_df)
    
    # Step 3: Vectorize text
    X_train_vectorized, X_test_vectorized, vectorizer = vectorize_text(X_train, X_test)
    
    # Step 4: Train model
    classifier = train_model(X_train_vectorized, y_train)
    
    # Step 5: Evaluate performance
    evaluate_model(classifier, X_test_vectorized, y_test)
    
    # Step 6: Save artifacts
    save_artifacts(vectorizer, classifier)
    
    print("\n" + "="*60)
    print("TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*60)

if __name__ == "__main__":
    main()
