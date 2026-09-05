import os
import shutil
import yaml
from pathlib import Path

def get_pothole_class_id(dataset_dir):
    """Reads data.yaml to find the class ID for 'pothole'."""
    yaml_path = dataset_dir / 'data.yaml'
    if not yaml_path.exists():
        # Fallback if no yaml, assume 0
        return 0
        
    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
            
        names = data.get('names', [])
        
        # Sometimes 'names' is a dictionary: {0: 'pothole', 1: 'crack'}
        if isinstance(names, dict):
            for class_id, name in names.items():
                if 'pothole' in str(name).lower():
                    return int(class_id)
        # Sometimes 'names' is a list: ['pothole', 'crack']
        elif isinstance(names, list):
            for class_id, name in enumerate(names):
                if 'pothole' in str(name).lower():
                    return class_id
                    
    except Exception as e:
        print(f"Error reading {yaml_path}: {e}")
        
    return 0 # Default to 0 if we can't find it

def merge_datasets(dataset_paths, output_dir):
    out_dir = Path(output_dir)
    splits = ['train', 'valid', 'test']
    
    # Create master directory structure
    for split in splits:
        (out_dir / split / 'images').mkdir(parents=True, exist_ok=True)
        (out_dir / split / 'labels').mkdir(parents=True, exist_ok=True)

    total_images_copied = 0

    # Iterate over each dataset
    for ds_idx, ds_path in enumerate(dataset_paths):
        ds_dir = Path(ds_path)
        if not ds_dir.exists():
            print(f"Warning: Dataset path {ds_path} does not exist. Skipping.")
            continue
            
        print(f"\nProcessing dataset {ds_idx + 1}: {ds_dir.name}")
        
        # Find which class ID represents 'pothole' in this specific dataset
        target_class_id = get_pothole_class_id(ds_dir)
        print(f"  Mapped 'pothole' to class ID {target_class_id} for this dataset.")
        
        # Check all possible splits (sometimes 'val' is named 'valid')
        for split in splits:
            src_split = split
            if split == 'valid' and (ds_dir / 'val').exists():
                src_split = 'val'
                
            img_dir = ds_dir / src_split / 'images'
            lbl_dir = ds_dir / src_split / 'labels'
            
            if not img_dir.exists() or not lbl_dir.exists():
                continue
                
            print(f"  Merging '{split}' split...")
            
            # Copy images and corresponding labels
            for img_file in img_dir.glob('*.*'):
                if img_file.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
                    continue
                    
                # Create a unique name to prevent collisions between datasets
                unique_name = f"ds{ds_idx}_{img_file.stem}"
                
                # Check if label exists
                lbl_file = lbl_dir / f"{img_file.stem}.txt"
                if not lbl_file.exists():
                    continue
                    
                # Read original labels and filter/remap them
                valid_labels = []
                with open(lbl_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            class_id = int(parts[0])
                            # Only keep the bounding box if it's a pothole
                            if class_id == target_class_id:
                                # Rewrite the class ID to 0 (since our master dataset only has 1 class)
                                new_line = f"0 {' '.join(parts[1:])}\n"
                                valid_labels.append(new_line)
                
                # If there are no potholes in this image after filtering, we can skip copying it
                # (or keep it as a negative background image, but skipping is safer to save space)
                if not valid_labels:
                    continue
                    
                # Copy Image
                dest_img = out_dir / split / 'images' / f"{unique_name}{img_file.suffix}"
                shutil.copy2(img_file, dest_img)
                
                # Write newly mapped Label
                dest_lbl = out_dir / split / 'labels' / f"{unique_name}.txt"
                with open(dest_lbl, 'w') as f:
                    f.writelines(valid_labels)
                
                total_images_copied += 1

    # Create the master data.yaml
    master_yaml = {
        'train': 'train/images',
        'val': 'valid/images',
        'test': 'test/images',
        'nc': 1,
        'names': ['pothole']
    }
    
    with open(out_dir / 'data.yaml', 'w') as f:
        yaml.dump(master_yaml, f, sort_keys=False)
        
    print(f"\nSuccessfully merged datasets into '{output_dir}'")
    print(f"Total images combined: {total_images_copied}")
    print(f"Master data.yaml created at: {out_dir / 'data.yaml'}")


if __name__ == "__main__":
    # LIST YOUR DATASET FOLDERS HERE
    # Add as many paths as you want to merge!
    my_datasets = [
        r"E:\Application Dev\VS Code files\Git\pothole-18",
        r"E:\Application Dev\VS Code files\Git\pothole-indian-road-5",
        # r"E:\Application Dev\VS Code files\Git\another_downloaded_dataset",
    ]
    
    output_folder = r"E:\Application Dev\VS Code files\Git\master_pothole_dataset"
    
    merge_datasets(my_datasets, output_folder)

