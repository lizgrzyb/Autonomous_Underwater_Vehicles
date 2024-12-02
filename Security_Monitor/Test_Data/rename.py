import os
directory = "./Test_Data/Sonar_Normal"

files = [f for f in os.listdir(directory)if os.path.isfile(os.path.join(directory, f))]

files.sort()

for i, file in enumerate(files, start=1):
    file_extension = os.path.splitext(file)[1]
    new_name = f"n_{i}{file_extension}"
    os.rename(
        os.path.join(directory, file),
        os.path.join(directory, new_name)
    )
    print(f"Renamed: {file} -> {new_name}")
print("All Files Renamed")
