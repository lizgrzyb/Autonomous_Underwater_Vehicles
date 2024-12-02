import pandas as pd
import pickle

# Load the trained model
def load_model(model_path):
    with open(model_path, 'rb') as file:
        model = pickle.load(file)
    return model

# Preprocessing: Group data into chunks of 10 and extract features
def extract_features(data, group_size=10):
    features = []
    for i in range(0, len(data) - group_size + 1, group_size):
        chunk = data.iloc[i:i+group_size]
        # Compute statistical features
        avg = chunk['Power'].mean()
        std = chunk['Power'].std()
        min_val = chunk['Power'].min()
        max_val = chunk['Power'].max()
        range_val = max_val - min_val

        # Append features
        features.append([avg, std, min_val, max_val, range_val])
    
    # Return as DataFrame
    feature_df = pd.DataFrame(features, columns=['Mean', 'StdDev', 'Min', 'Max', 'Range'])
    return feature_df

# Function to evaluate incoming power data
def evaluate_power_data(model, input_file, output_file, group_size=10):
    """
    Evaluate incoming power data and save classification results to CSV.
    
    Parameters:
    - model: Trained machine learning model
    - input_file: Path to the CSV file containing power data
    - output_file: Path to save the classification results
    - group_size: Number of data points to group together for feature extraction
    """
    # Load incoming power data
    data = pd.read_csv(input_file)
    
    # Ensure the input data has the correct column
    if "Power" not in data.columns:
        raise ValueError("Input data must have a 'Power' column.")
    
    # Extract features from the data
    features = extract_features(data, group_size=group_size)
    
    # Make predictions
    predictions = model.predict(features)
    
    # Add predictions to the dataframe
    features["Prediction"] = predictions
    
    # Save the results to a CSV file
    features.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

# Main execution
if __name__ == "__main__":
    # Path to the trained model
    model_path = "IDS_power.pkl"
    
    # Input and output file paths
    input_test_file = "./Test_Data/new_output_power_attack_1000.csv"
    output_results_file = "power_classification_results.csv"
    
    # Load the model
    print("Loading model...")
    rf_model = load_model(model_path)
    
    # Evaluate the power data
    print("Evaluating power data...")
    evaluate_power_data(rf_model, input_test_file, output_results_file, group_size=10)
    print("Evaluation complete.")
