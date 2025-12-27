# Floor Selection Algorithm: Spatial and ML-Based Decision Logic

## Overview

This document describes a sophisticated floor selection algorithm that combines:
1. Spatial awareness (position relative to mezzanine boundaries)
2. ML-based floor predictions
3. Confidence thresholds
4. Configurable uncertainty zones

## Key Concepts

### Mezzanine Polygon
The mezzanine (Floor 1) occupies a specific area defined by a polygon:
```json
[
    [12.0, 45.6],
    [12.0, 40.1],
    [22.5, 40.1],
    [22.5, 36.3],
    [52.7, 36.3],
    [52.7, 37.3],
    [66.6, 37.3],
    [66.6, 45.6]
]
```

### Uncertainty Zone
A configurable buffer zone around the mezzanine polygon where both floors might be valid.
- Default: 2.0 meters
- Configurable via: `uncertainty_distance_threshold`

## Algorithm Flow

### 1. Initial Position Computation
- TDOA algorithm computes position candidates for each floor
- Each candidate has:
  - (x, y, z) coordinates
  - Variance/quality metrics
  - Source floor (0 or 1)

### 2. Spatial Analysis

```
For each position candidate:
    1. Calculate distance to mezzanine polygon boundary
    2. Determine spatial zone:
       - INSIDE: Within mezzanine polygon
       - OUTSIDE_FAR: Outside polygon by > uncertainty_distance_threshold
       - UNCERTAINTY_ZONE: Within uncertainty_distance_threshold of boundary
```

### 3. Decision Logic

#### Case 1: Single Candidate Available
```
If only one floor produced a valid position:
    If candidate is from Floor 1 and position is OUTSIDE_FAR:
        ❌ Reject position immediately (before ML prediction)
        Log: "Floor 1 position far outside mezzanine - spatially impossible"
        Do not run ML prediction
    
    Else:
        Run ML prediction (unless spatially certain and optimization enabled)
        
        If ML strongly disagrees (confidence > 0.85 for other floor):
            ❌ Trigger ML Trust Gate:
                Set confidence_for_quality_gate = 0.05
                Quality gate will reject (0.05 < 0.15 threshold)
                Log: "ML strongly disagrees: candidate is floor X but ML predicts floor Y"
        
        Else:
            Apply spatial logic to determine final confidence
            If candidate is Floor 0:
                If position is OUTSIDE_FAR:
                    ✓ Accept with high spatial confidence
                Else if position is INSIDE:
                    ✓ Accept with neutral spatial confidence (0.5)
                    Let ML confidence dominate decision
            
            If candidate is Floor 1:
                If position is INSIDE:
                    ✓ Accept with neutral spatial confidence (0.5)
                    Let ML confidence dominate decision
                Else if position is UNCERTAINTY_ZONE:
                    ✓ Accept with medium confidence
```

#### Case 2: Multiple Candidates Available
```
If both floors produced valid positions:
    For each candidate:
        If candidate is from Floor 1 and position is OUTSIDE_FAR:
            ❌ Discard this candidate immediately
            Log: "Floor 1 position far outside mezzanine - spatially impossible"
            Continue to next candidate
        
        Calculate spatial_score based on position:
            - Floor 0: Higher score when OUTSIDE_FAR
            - Floor 1: Higher score when INSIDE
            - Both: Lower score in UNCERTAINTY_ZONE
    
    If any candidate is spatially confident (not in uncertainty zone):
        If only one is spatially confident:
            ✓ Select that candidate
            Validate with ML (log if mismatch)
        Else:
            Run ML prediction
            Calculate effective_confidence for each candidate:
                - If ML prediction matches candidate floor: effective_conf = ml_conf
                - If ML prediction differs: effective_conf = ml_conf * 0.1
            Combine spatial_score with effective_confidence
            Select highest combined score
    
    Else (all candidates in uncertainty zone):
        Run ML prediction
        Calculate effective_confidence for each candidate
        Select based on effective_confidence
        If effective_confidence < 0.15 for both:
            ⚠️ Log low confidence warning
            Select based on variance (traditional method)
```

### 4. Confidence Calculation

#### Effective Confidence (Critical Concept)

The algorithm uses **effective_confidence** - ML confidence with a mismatch penalty applied:

```cpp
// When ML prediction doesn't match the candidate floor:
effective_confidence = ml_confidence * 0.1  // 90% penalty

// When ML prediction matches the candidate floor:
effective_confidence = ml_confidence  // No penalty
```

This ensures that when ML strongly predicts a different floor than the candidate being evaluated, the spatial logic receives a very low confidence value, preventing it from overriding correct ML predictions.

#### Zone-Based Weighting

**INSIDE Mezzanine:**
- Both floors are spatially equally probable
- ML is the primary decision maker with candidate origin as secondary factor
- When ML confidence >= `inside_ml_trust_threshold` (0.7): Trust ML completely
- When ML and candidate agree: confidence = ml_confidence + 0.1 (for both floors)
- When ML and candidate disagree (symmetric treatment for both floors):
  - If ML > 0.85: ML overrides candidate, confidence = ml_confidence * 0.9
  - If ML > 0.6: ML overrides candidate, confidence = ml_confidence * 0.8
  - Otherwise: Keep candidate floor, confidence = 0.7 * ml_confidence + 0.15

**UNCERTAINTY_ZONE:**
- ML has much higher weight (90% vs 10%)
```
final_confidence = uncertainty_spatial_weight * spatial_conf + 
                   uncertainty_ml_weight * effective_conf
Where:
    uncertainty_spatial_weight = 0.1
    uncertainty_ml_weight = 0.9
    effective_conf = ML confidence with mismatch penalty
```

**OUTSIDE_FAR:**
- Balanced weights favor spatial slightly
```
final_confidence = spatial_weight * spatial_conf + 
                   ml_weight * effective_conf
Where:
    spatial_weight = 0.3
    ml_weight = 0.7
    effective_conf = ML confidence with mismatch penalty
```

**Important:** The spatial logic always receives `effective_confidence`, not raw ML confidence. This prevents spatial logic from incorrectly overriding ML predictions when there's a floor mismatch.

### 5. Quality Gates

The system implements multiple quality gates to ensure reliable floor detection:

#### ML Trust Gate (Primary)
When ML has high confidence (>0.85) but disagrees with the selected candidate:
```
If ML_confidence > 0.85 AND ML_predicted_floor ≠ candidate_floor:
    Set quality_gate_confidence = 0.05
    ❌ Position will be rejected
    Log: "ML strongly disagrees: candidate is floor X but ML predicts floor Y"
```

This ensures we trust ML predictions when they have high confidence, even if it means no position output.

#### Quality Threshold Gate
```
If quality_gate_confidence <= quality_gate_threshold (0.15):
    ❌ Reject position
    Log: "QUALITY GATE REJECTION: Winning candidate rejected due to low confidence"
```

#### Minimum Confidence Gate
```
If final_confidence < minimum_confidence_threshold (0.2):
    ❌ Reject position
    Log: "Position rejected due to low combined confidence"
```

Note: The ML Trust Gate is critical for handling cases like tags under the mezzanine,
where only a Floor 1 candidate might be available but ML correctly identifies it as Floor 0.

## Configuration Parameters

All floor selection parameters are configurable via the engine configuration JSON file:

```json
{
  "engine_config": {
    "floor_detector_config": {
      "enabled": true,
      "model_path": "ml_models/floor_detection_model_strategic_20250728_180850.ubj",
      "metadata_path": "ml_models/floor_detection_model_strategic_20250728_180850_metadata.json",
      "write_training_data": false,
      "quality_gate_enabled": true,
      "quality_gate_threshold": 0.15,
      
      "spatial_config": {
        "enabled": true,
        
        "mezzanine_polygon": [
          [12.0, 45.6], [12.0, 40.1], [22.5, 40.1], [22.5, 36.3],
          [52.7, 36.3], [52.7, 37.3], [66.6, 37.3], [66.6, 45.6]
        ],
        
        "uncertainty_distance_threshold": 2.0,
        
        "spatial_confidence_weight": 0.3,
        "ml_confidence_weight": 0.7,
        
        "uncertainty_spatial_weight": 0.1,
        "uncertainty_ml_weight": 0.9,
        
        "minimum_confidence_threshold": 0.2,
        "high_ml_confidence_threshold": 0.85,
        "ml_override_threshold": 0.95,
        "inside_ml_trust_threshold": 0.7,
        
        "skip_ml_when_spatially_certain": true,
        "spatial_certainty_distance": 5.0,
        
        "conflict_policy": "trust_ml"
      }
    }
  }
}
```

### Parameter Descriptions

- **model_path**: Path to the XGBoost model file (.ubj format)
- **metadata_path**: Path to the model metadata JSON file
- **write_training_data**: Enable to dump training data for model improvements
- **quality_gate_enabled**: Enable ML confidence-based quality checks
- **quality_gate_threshold**: Minimum ML confidence to accept a position

#### Spatial Configuration

- **enabled**: Enable/disable spatial floor selection logic
- **mezzanine_polygon**: Vertices defining Floor 1 boundary (L-shaped polygon)
- **uncertainty_distance_threshold**: Buffer zone around mezzanine (meters)
- **spatial_confidence_weight**: Weight for spatial confidence in OUTSIDE_FAR zone
- **ml_confidence_weight**: Weight for ML confidence in OUTSIDE_FAR zone
- **uncertainty_spatial_weight**: Weight for spatial confidence in UNCERTAINTY_ZONE
- **uncertainty_ml_weight**: Weight for ML confidence in UNCERTAINTY_ZONE
- **minimum_confidence_threshold**: Minimum combined confidence to accept position
- **high_ml_confidence_threshold**: ML confidence threshold for strong predictions
- **ml_override_threshold**: ML confidence that can override spatial logic
- **inside_ml_trust_threshold**: ML confidence to trust completely when inside mezzanine
- **skip_ml_when_spatially_certain**: Optimize by skipping ML when position is clear
- **spatial_certainty_distance**: Distance from boundary to consider "certain" (meters)
- **conflict_policy**: How to resolve spatial/ML conflicts ("trust_ml", "trust_spatial", or "reject")

## Logging Strategy

### Info Level
- Final floor selection with confidence
- Optimization skips (when ML not needed)

### Warning Level
- Spatial/ML mismatches
- Low confidence selections
- Positions in uncertainty zones

### Error Level
- Strong spatial/ML conflicts
- Position rejections

### Debug Level
- Distance calculations
- Zone determinations
- Individual confidence scores

## Benefits

1. **Efficiency**: Skip ML when spatially certain (reduces computation)
2. **Accuracy**: Combine geometric and signal-based intelligence
3. **Robustness**: Handle edge cases with configurable policies
4. **Observability**: Comprehensive logging for troubleshooting
5. **Flexibility**: All thresholds and weights configurable

## Implementation Notes

1. **Point-in-Polygon**: Use ray casting or winding number algorithm
2. **Distance to Polygon**: Calculate minimum distance to any edge
3. **Thread Safety**: Ensure polygon access is thread-safe
4. **Performance**: Cache polygon preprocessing (e.g., bounding box)

### Critical Implementation Details

1. **Effective Confidence**: The spatial logic in `makeFloorDecision()` must receive the effective_confidence (with mismatch penalty), not raw ML confidence. This prevents spatial logic from overriding correct ML predictions.

2. **Confidence Flow**:
   ```cpp
   // In tdoa_dispatcher.cpp:
   float effective_conf = (prediction.floor == candidate_floor) ? 
                         prediction.confidence : 
                         prediction.confidence * 0.1f;
   
   auto floor_decision = FloorSelectionSpatial::makeFloorDecision(
       Point2D(tag_x, tag_y),
       candidate_floor,
       prediction.floor,
       effective_conf,  // Must use effective_conf, not raw confidence!
       spatial_config);
   ```

3. **ML Trust Logic**: When ML has high confidence (>0.85) in a different floor than the candidate:
   ```cpp
   if (!best_prediction->ml_skipped && !best_prediction->is_match && 
       best_prediction->ml_confidence > 0.85) {
       // ML strongly believes it's a different floor
       confidence_for_quality_gate = 0.05f; // Triggers rejection
   }
   ```

4. **Quality Gate**: Rejects positions when confidence <= quality_gate_threshold (0.15).

5. **Debug Logging**: 
   - Wrong floor classifications logged at WARNING level
   - ML disagreements logged at INFO level
   - Quality gate rejections logged at INFO level for visibility

## Example Scenarios

### Scenario 1: Clear Floor 0
- Position: (5.0, 20.0) - 7m from mezzanine
- Candidate: Floor 0 only
- Decision: Accept immediately (skip ML)
- Confidence: 0.95 (high spatial confidence)

### Scenario 2: Uncertainty Zone
- Position: (13.5, 42.0) - 1.5m from boundary
- Candidates: Both floors
- ML Prediction: Floor 1 (0.75 confidence)
- Decision: Select Floor 1
- Confidence: 0.645 (0.3×0.3 + 0.7×0.75)

### Scenario 3: Spatial/ML Conflict
- Position: (30.0, 40.0) - Inside mezzanine
- Candidate: Floor 0 only
- ML Prediction: Floor 0 (0.92 confidence)
- Decision: Accept with ML confidence (spatial and ML agree)
- Confidence: 0.92

### Scenario 4: Tag Under Mezzanine
- Position: (20.0, 42.0) - Inside mezzanine polygon
- Physical Reality: Tag is on Floor 0, physically under the mezzanine structure
- Candidate: Floor 1 only (Floor 0 candidate has poor quality)
- ML Prediction: Floor 0 (0.95 confidence)
- Decision: Reject (ML Trust Gate triggered)
- Quality Gate: Confidence set to 0.05, triggers rejection
- Log: "ML strongly disagrees: candidate is floor 1 but ML predicts floor 0"
- Note: This is correct behavior - the tag is truly on Floor 0

## Quality Assessment Configuration

The algorithm supports quality assessment using known ground truth tags for monitoring performance:

### Configuration Options

```json
{
  "quality_assessment_config": {
    "enabled": true,
    "logging_interval_seconds": 120,
    "log_wrong_classifications": true,
    "log_all_decisions": false,
    "ground_truth_assignments": {
      "f260a59af3be": 0,
      "eacbbb80d2ae": 1
    }
  }
}
```

### Parameters

- **enabled**: Enable/disable quality assessment (default: `false`, recommended: `true` for debugging)
- **logging_interval_seconds**: Frequency of quality metrics logging (default: `120` seconds for debugging)
- **log_wrong_classifications**: Always log incorrect classifications for debugging (default: `true`)
- **log_all_decisions**: Log every decision for ground truth tags - verbose mode (default: `false`)
- **ground_truth_assignments**: Map of tag MAC addresses to their true floor assignments

### Quality Metrics

The system tracks and logs:
- **Overall Accuracy**: Percentage of correct floor assignments
- **Floor 0 Accuracy**: Accuracy specifically for Floor 0 tags
- **Floor 1 Accuracy**: Accuracy specifically for Floor 1 tags
- **Decision Volume**: Number of decisions processed
- **Time Window**: Duration of metrics collection

### Example Output

**Startup Log:**
```
🎯 [QUALITY INIT] Floor detection quality assessment ENABLED | 
Ground truth tags: 60 total (30 Floor0, 30 Floor1) | 
Metrics interval: 120s | Wrong classifications: LOGGED | All decisions: silent
```

**Wrong Classification (Critical for Debugging):**
```
[QUALITY ERROR] Tag f260a59af3be | TRUE Floor: 0 | PREDICTED: 1 | Position: (25.3, 42.1) | 
Final Confidence: 0.723 | Zone: UNCERTAINTY | Spatial Conf: 0.450 | ML Conf: 0.832 | 
*** WRONG CLASSIFICATION - NEEDS INVESTIGATION ***
```

**Periodic Quality Status:**
```
🟢 [QUALITY STATUS] EXCELLENT: 98.1% accuracy (52 correct, 1 wrong) | 
Floor0: 96.7% (29/30), Floor1: 100.0% (23/23) | 
Window: 3.2min | Algorithm performing well ✓

🟡 [QUALITY STATUS] DEGRADED: 84.5% accuracy (49 correct, 9 wrong) | 
Floor0: 80.0% (24/30), Floor1: 89.3% (25/28) | 
Window: 5.1min | Check for issues ⚠️

🔴 [QUALITY STATUS] POOR: 72.1% accuracy (31 correct, 12 wrong) | 
Floor0: 65.2% (15/23), Floor1: 80.0% (16/20) | 
Window: 2.8min | URGENT: Algorithm needs attention! 🚨
```

### Ground Truth Tags

The system includes 60 strategically placed tags (30 per floor) with known positions for validation:
- **Floor 0 Tags**: 30 tags physically located on the ground floor
- **Floor 1 Tags**: 30 tags physically located on the mezzanine
- **Validation Accuracy**: Achieved 99.96% accuracy on 121,383 samples during training

## Future Enhancements

1. **Dynamic Mezzanine Boundaries**: Time-based or event-based changes
2. **Multi-Floor Support**: Extend beyond binary floor selection
3. **Historical Bias**: Use previous positions to influence decisions
4. **Anchor-Specific Weights**: Some anchors may be more reliable for floor detection
5. **Machine Learning Integration**: Train model with spatial features included
6. **Advanced Quality Metrics**: Track accuracy by spatial zone and ML confidence ranges