def cluster_boxes(boxes, distance_threshold=60):
    """
    Groups bounding boxes that intersect or are extremely close to each other.
    boxes: list of dicts {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'conf': conf, 'class_name': name}
    """
    if not boxes: return []
    
    clusters = []
    for box in boxes:
        clusters.append({
            'x1': box['x1'], 'y1': box['y1'], 'x2': box['x2'], 'y2': box['y2'],
            'conf': box['conf'], 'class_name': box['class_name'],
            'count': 1
        })
    
    changed = True
    while changed:
        changed = False
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                c1 = clusters[i]
                c2 = clusters[j]
                
                # Check if boxes intersect or are close to each other
                if not (c1['x2'] < c2['x1'] - distance_threshold or 
                        c1['x1'] > c2['x2'] + distance_threshold or
                        c1['y2'] < c2['y1'] - distance_threshold or 
                        c1['y1'] > c2['y2'] + distance_threshold):
                    
                    # Merge c2 into c1 (fuse into a single massive cluster box)
                    c1['x1'] = min(c1['x1'], c2['x1'])
                    c1['y1'] = min(c1['y1'], c2['y1'])
                    c1['x2'] = max(c1['x2'], c2['x2'])
                    c1['y2'] = max(c1['y2'], c2['y2'])
                    c1['conf'] = max(c1['conf'], c2['conf'])
                    c1['count'] += c2['count']
                    
                    # Remove c2
                    clusters.pop(j)
                    changed = True
                    break
            if changed:
                break
                
    return clusters

def determine_severity_cluster(cluster_width, cluster_area, frame_width, frame_area, pothole_count):
    """
    Base the severity ("LOW", "MEDIUM", "HIGH", "VERY HIGH") on the width and area of 
    the bounding box relative to the total frame size.
    """
    width_percentage = cluster_width / frame_width if frame_width > 0 else 0
    area_percentage = cluster_area / frame_area if frame_area > 0 else 0
    
    # If the cluster spans > 40% of the screen width or contains 3+ potholes, automatically flag as "VERY HIGH"
    if width_percentage > 0.40 or pothole_count >= 3 or area_percentage > 0.15:
        return "VERY HIGH"
    elif width_percentage > 0.25 or area_percentage > 0.08:
        return "HIGH"
    elif width_percentage > 0.10 or area_percentage > 0.02:
        return "MEDIUM"
    else:
        return "LOW"

