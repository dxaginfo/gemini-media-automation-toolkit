# SceneValidator

A tool to validate scene structure and continuity in media projects.

## Features

- Validates scene structure against predefined templates
- Checks continuity elements across scenes
- Identifies potential issues with scene flow
- Integrates with Gemini API for intelligent validation
- Generates detailed validation reports

## Prerequisites

- Python 3.8+
- Gemini API key
- Google Cloud Storage (optional, for storing validation reports)

## Installation

```bash
# Navigate to the tool directory
cd tools/scene-validator

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Usage

### Basic Validation

```python
from scene_validator import SceneValidator

# Initialize the validator
validator = SceneValidator(config_path="config/default.json")

# Validate a scene file
validation_result = validator.validate("path/to/scene.json")

# Print validation results
print(validation_result.summary())

# Export detailed report
validation_result.export_report("path/to/report.html")
```

### Integration with TimelineAssembler

```python
from scene_validator import SceneValidator
from timeline_assembler import TimelineAssembler

# Initialize both tools
validator = SceneValidator(config_path="config/default.json")
assembler = TimelineAssembler(config_path="config/timeline_config.json")

# Validate scenes before assembly
scenes = ["scene1.json", "scene2.json", "scene3.json"]
valid_scenes = []

for scene in scenes:
    result = validator.validate(scene)
    if result.is_valid():
        valid_scenes.append(scene)
    else:
        print(f"Scene {scene} has issues: {result.get_issues()}")

# Assemble timeline with valid scenes
if valid_scenes:
    timeline = assembler.assemble(valid_scenes)
    assembler.export(timeline, "final_timeline.json")
```

## Configuration Options

The `config/default.json` file supports the following options:

```json
{
  "validation_rules": {
    "required_fields": ["id", "name", "duration", "elements"],
    "allowed_element_types": ["character", "prop", "environment", "effect"],
    "max_elements_per_scene": 50,
    "min_scene_duration": 1.0
  },
  "continuity_tracking": {
    "enabled": true,
    "track_characters": true,
    "track_props": true,
    "track_environments": true
  },
  "gemini_api": {
    "use_gemini": true,
    "model_name": "gemini-pro",
    "temperature": 0.2
  },
  "reporting": {
    "detail_level": "high",
    "include_suggestions": true,
    "format": "html"
  }
}
```

## API Reference

See the [API documentation](../../docs/scene-validator/api.md) for detailed information on all classes and methods.

## Examples

Check the `examples/` directory for additional usage examples.

## Integration

This tool integrates seamlessly with:

- TimelineAssembler - For validating scenes before timeline assembly
- ContinuityTracker - For deeper continuity analysis
- StoryboardGen - For validating storyboards against scene requirements