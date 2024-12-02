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
        mean_heading = chunk['heading'].mean()
        std_heading = chunk['heading'].std()
        min_heading = chunk['heading'].min()
        max_heading = chunk['heading'].max()
        range_heading = max_heading - min_heading

        mean_angle = chunk['rudder angle'].mean()
        std_angle = chunk['rudder angle'].std()
        min_angle = chunk['rudder angle'].min()
        max_angle = chunk['rudder angle'].max()
        range_angle = max_angle - min_angle

        mean_power = chunk['rudder power'].mean()
        std_power = chunk['rudder power'].std()
        min_power = chunk['rudder power'].min()
        max_power = chunk['rudder power'].max()
        range_power = max_power - min_power

        # Append features
        features.append([
            mean_heading, std_heading, min_heading, max_heading, range_heading,
            mean_angle, std_angle, min_angle, max_angle, range_angle,
            mean_power, std_power, min_power, max_power, range_power
        ])
    
    # Return as DataFrame
    feature_columns = [
        'mean_heading', 'std_heading', 'min_heading', 'max_heading', 'range_heading',
        'mean_angle', 'std_angle', 'min_angle', 'max_angle', 'range_angle',
        'mean_power', 'std_power', 'min_power', 'max_power', 'range_power'
    ]
    return pd.DataFrame(features, columns=feature_columns)

# Function to evaluate incoming rudder data
def evaluate_rudder_data(model, input_file, output_file, group_size=10):
    """
    Evaluate incoming rudder data and save classification results to CSV.
    
    Parameters:
    - model: Trained machine learning model
    - input_file: Path to the CSV file containing rudder data
    - output_file: Path to save the classification results
    - group_size: Number of data points to group together for feature extraction
    """
    # Load incoming rudder data
    data = pd.read_csv(input_file)
    
    # Ensure the input data has the correct columns
    required_columns = ['heading', 'rudder angle', 'rudder power']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Input data must have a '{col}' column.")
    
    # Extract features from the data
    features = extract_features(data, group_size=group_size)
    
    # Make predictions
    predictions = model.predict(features)
    
    # Add predictions to the features dataframe
    features["Prediction"] = predictions
    
    # Save the results to a CSV file
    features.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

# Main execution
if __name__ == "__main__":
    # Path to the trained model
    model_path = "IDS_rudder.pkl"
    
    # Input and output file paths
    input_test_file = "./Test_Data/output_rudder_attack.csv"
    output_results_file = "rudder_classification_results.csv"
    
    # Load the model
    print("Loading model...")
    rf_model = load_model(model_path)
    
    # Evaluate the rudder data
    print("Evaluating rudder data...")
    evaluate_rudder_data(rf_model, input_test_file, output_results_file, group_size=10)
    print("Evaluation complete.")
