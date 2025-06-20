#!/usr/bin/env python3
"""
SceneValidator - A tool to validate scene structure and continuity in media projects.

This module provides functionality to validate scene structure against predefined templates,
check continuity elements across scenes, and identify potential issues with scene flow.
It integrates with Gemini API for intelligent validation and generates detailed validation reports.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import google.generativeai as genai
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SceneValidator")

class ValidationResult:
    """Represents the result of a scene validation operation."""
    
    def __init__(self):
        """Initialize a new ValidationResult instance."""
        self.valid = True
        self.issues = []
        self.warnings = []
        self.suggestions = []
        self.scene_data = None
        self.validation_time = datetime.now()
    
    def add_issue(self, issue: str) -> None:
        """Add a validation issue."""
        self.valid = False
        self.issues.append(issue)
        logger.warning(f"Validation issue: {issue}")
    
    def add_warning(self, warning: str) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)
        logger.info(f"Validation warning: {warning}")
    
    def add_suggestion(self, suggestion: str) -> None:
        """Add a validation suggestion."""
        self.suggestions.append(suggestion)
        logger.info(f"Validation suggestion: {suggestion}")
    
    def is_valid(self) -> bool:
        """Check if the validation was successful."""
        return self.valid
    
    def get_issues(self) -> List[str]:
        """Get the list of validation issues."""
        return self.issues
    
    def summary(self) -> str:
        """Generate a summary of the validation result."""
        status = "VALID" if self.valid else "INVALID"
        summary = f"Validation Status: {status}\n"
        
        if self.issues:
            summary += "\nIssues:\n"
            for i, issue in enumerate(self.issues, 1):
                summary += f"{i}. {issue}\n"
        
        if self.warnings:
            summary += "\nWarnings:\n"
            for i, warning in enumerate(self.warnings, 1):
                summary += f"{i}. {warning}\n"
        
        if self.suggestions:
            summary += "\nSuggestions:\n"
            for i, suggestion in enumerate(self.suggestions, 1):
                summary += f"{i}. {suggestion}\n"
        
        return summary
    
    def export_report(self, output_path: str) -> str:
        """Export a detailed validation report."""
        report = {
            "valid": self.valid,
            "validation_time": self.validation_time.isoformat(),
            "issues": self.issues,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "scene_data": self.scene_data
        }
        
        # Determine file format
        if output_path.endswith(".json"):
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)
        elif output_path.endswith(".html"):
            html_report = self._generate_html_report(report)
            with open(output_path, "w") as f:
                f.write(html_report)
        else:
            raise ValueError("Unsupported report format. Use .json or .html")
        
        logger.info(f"Validation report exported to {output_path}")
        return output_path
    
    def _generate_html_report(self, report_data: Dict) -> str:
        """Generate an HTML report from the validation data."""
        valid_class = "valid" if report_data["valid"] else "invalid"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Scene Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
        h1 {{ color: #333; }}
        .report-header {{ display: flex; justify-content: space-between; }}
        .status {{ padding: 10px; border-radius: 5px; font-weight: bold; }}
        .valid {{ background-color: #dff0d8; color: #3c763d; }}
        .invalid {{ background-color: #f2dede; color: #a94442; }}
        .section {{ margin: 20px 0; }}
        .issue {{ background-color: #f2dede; padding: 10px; margin: 5px 0; border-left: 4px solid #a94442; }}
        .warning {{ background-color: #fcf8e3; padding: 10px; margin: 5px 0; border-left: 4px solid #8a6d3b; }}
        .suggestion {{ background-color: #d9edf7; padding: 10px; margin: 5px 0; border-left: 4px solid #31708f; }}
        pre {{ background-color: #f5f5f5; padding: 10px; overflow: auto; }}
    </style>
</head>
<body>
    <h1>Scene Validation Report</h1>
    
    <div class="report-header">
        <div class="status {valid_class}">
            Status: {report_data["valid"] and "VALID" or "INVALID"}
        </div>
        <div class="timestamp">
            Generated: {report_data["validation_time"]}
        </div>
    </div>
    """
        
        if report_data["issues"]:
            html += """
    <div class="section">
        <h2>Issues</h2>
    """
            for issue in report_data["issues"]:
                html += f'        <div class="issue">{issue}</div>\n'
            html += "    </div>\n"
        
        if report_data["warnings"]:
            html += """
    <div class="section">
        <h2>Warnings</h2>
    """
            for warning in report_data["warnings"]:
                html += f'        <div class="warning">{warning}</div>\n'
            html += "    </div>\n"
        
        if report_data["suggestions"]:
            html += """
    <div class="section">
        <h2>Suggestions</h2>
    """
            for suggestion in report_data["suggestions"]:
                html += f'        <div class="suggestion">{suggestion}</div>\n'
            html += "    </div>\n"
        
        if report_data["scene_data"]:
            html += """
    <div class="section">
        <h2>Scene Data</h2>
        <pre>"""
            html += json.dumps(report_data["scene_data"], indent=2)
            html += """</pre>
    </div>
    """
        
        html += """
</body>
</html>
        """
        return html


class SceneValidator:
    """Validates scene structure and continuity in media projects."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the SceneValidator.
        
        Args:
            config_path: Path to the configuration file. If None, uses default config.
        """
        self.config = self._load_config(config_path)
        self._setup_gemini_api()
        logger.info("SceneValidator initialized with config from %s", config_path or "default config")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from a file or use default config."""
        default_config = {
            "validation_rules": {
                "required_fields": ["id", "name", "duration", "elements"],
                "allowed_element_types": ["character", "prop", "environment", "effect"],
                "max_elements_per_scene": 50,
                "min_scene_duration": 1.0
            },
            "continuity_tracking": {
                "enabled": True,
                "track_characters": True,
                "track_props": True,
                "track_environments": True
            },
            "gemini_api": {
                "use_gemini": True,
                "model_name": "gemini-pro",
                "temperature": 0.2
            },
            "reporting": {
                "detail_level": "high",
                "include_suggestions": True,
                "format": "html"
            }
        }
        
        if not config_path:
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded configuration from {config_path}")
                return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            logger.info("Using default configuration")
            return default_config
    
    def _setup_gemini_api(self) -> None:
        """Setup Gemini API if enabled in config."""
        if self.config.get("gemini_api", {}).get("use_gemini", False):
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY environment variable not set. Gemini API will not be available.")
                self.gemini_available = False
                return
            
            try:
                genai.configure(api_key=api_key)
                model_name = self.config["gemini_api"]["model_name"]
                self.gemini_model = genai.GenerativeModel(model_name)
                self.gemini_available = True
                logger.info(f"Gemini API initialized with model {model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {e}")
                self.gemini_available = False
        else:
            self.gemini_available = False
    
    def validate(self, scene_path: str) -> ValidationResult:
        """
        Validate a scene file.
        
        Args:
            scene_path: Path to the scene file in JSON format.
        
        Returns:
            ValidationResult: The result of the validation.
        """
        result = ValidationResult()
        
        try:
            # Load the scene data
            scene_data = self._load_scene_data(scene_path, result)
            if not scene_data:
                return result
            
            result.scene_data = scene_data
            
            # Perform validation checks
            self._validate_required_fields(scene_data, result)
            self._validate_scene_structure(scene_data, result)
            self._validate_elements(scene_data, result)
            
            # Perform Gemini-based validation if available
            if self.gemini_available:
                self._perform_gemini_validation(scene_data, result)
            
            logger.info(f"Validation completed for {scene_path}. Valid: {result.is_valid()}")
            
        except Exception as e:
            result.add_issue(f"Unexpected error during validation: {str(e)}")
            logger.exception(f"Unexpected error validating {scene_path}")
        
        return result
    
    def _load_scene_data(self, scene_path: str, result: ValidationResult) -> Optional[Dict[str, Any]]:
        """Load scene data from a file."""
        try:
            with open(scene_path, 'r') as f:
                scene_data = json.load(f)
            return scene_data
        except FileNotFoundError:
            result.add_issue(f"Scene file not found: {scene_path}")
            return None
        except json.JSONDecodeError as e:
            result.add_issue(f"Invalid JSON in scene file: {e}")
            return None
    
    def _validate_required_fields(self, scene_data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate that all required fields are present in the scene data."""
        required_fields = self.config["validation_rules"]["required_fields"]
        for field in required_fields:
            if field not in scene_data:
                result.add_issue(f"Missing required field: {field}")
    
    def _validate_scene_structure(self, scene_data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate the general structure of the scene."""
        # Check scene duration
        min_duration = self.config["validation_rules"]["min_scene_duration"]
        if "duration" in scene_data and scene_data["duration"] < min_duration:
            result.add_warning(f"Scene duration ({scene_data['duration']}s) is less than minimum recommended ({min_duration}s)")
        
        # Check for empty name
        if "name" in scene_data and not scene_data["name"].strip():
            result.add_warning("Scene has an empty name")
    
    def _validate_elements(self, scene_data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate the elements within the scene."""
        if "elements" not in scene_data:
            # Already checked in required fields validation
            return
        
        elements = scene_data["elements"]
        if not isinstance(elements, list):
            result.add_issue("Scene elements must be a list")
            return
        
        # Check element count
        max_elements = self.config["validation_rules"]["max_elements_per_scene"]
        if len(elements) > max_elements:
            result.add_warning(f"Scene has {len(elements)} elements, which exceeds the recommended maximum of {max_elements}")
        
        # Check element types
        allowed_types = self.config["validation_rules"]["allowed_element_types"]
        for i, element in enumerate(elements):
            if not isinstance(element, dict):
                result.add_issue(f"Element at index {i} is not a valid object")
                continue
                
            if "type" not in element:
                result.add_issue(f"Element at index {i} is missing a type")
                continue
                
            if element["type"] not in allowed_types:
                result.add_issue(f"Element at index {i} has invalid type: {element['type']}. Allowed types: {', '.join(allowed_types)}")
                
            if "id" not in element:
                result.add_warning(f"Element at index {i} is missing an ID")
    
    def _perform_gemini_validation(self, scene_data: Dict[str, Any], result: ValidationResult) -> None:
        """Use Gemini API to perform additional intelligent validation."""
        try:
            prompt = self._generate_gemini_prompt(scene_data)
            gemini_response = self.gemini_model.generate_content(prompt)
            
            # Extract suggestions from Gemini response
            suggestions = self._parse_gemini_response(gemini_response.text)
            for suggestion in suggestions:
                result.add_suggestion(suggestion)
                
            logger.info("Gemini validation completed successfully")
        except Exception as e:
            logger.error(f"Error during Gemini validation: {e}")
            # Gemini validation is optional, so we don't mark the result as invalid
            result.add_warning(f"Could not perform Gemini-based validation: {str(e)}")
    
    def _generate_gemini_prompt(self, scene_data: Dict[str, Any]) -> str:
        """Generate a prompt for Gemini API based on scene data."""
        scene_json = json.dumps(scene_data, indent=2)
        
        prompt = f"""
        You are an expert media production consultant specializing in scene structure and continuity.
        
        Please analyze the following scene data and provide suggestions for improvement, focusing on:
        1. Structural issues that could impact production
        2. Potential continuity problems
        3. Efficiency improvements
        4. Best practices for this type of scene
        
        Format your response as a bulleted list of specific, actionable suggestions.
        
        Scene data:
        ```json
        {scene_json}
        ```
        """
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> List[str]:
        """Parse Gemini API response to extract suggestions."""
        suggestions = []
        
        # Simple parsing: extract bullet points
        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                suggestion = line[1:].strip()
                if suggestion:
                    suggestions.append(suggestion)
            elif line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                parts = line.split('.', 1)
                if len(parts) > 1:
                    suggestion = parts[1].strip()
                    if suggestion:
                        suggestions.append(suggestion)
        
        return suggestions


def main():
    """Main function for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate scene structure and continuity in media projects")
    parser.add_argument("scene_path", help="Path to the scene file to validate")
    parser.add_argument("--config", "-c", help="Path to configuration file")
    parser.add_argument("--output", "-o", help="Path to output validation report")
    parser.add_argument("--format", "-f", choices=["json", "html"], default="html", help="Output format for the report")
    
    args = parser.parse_args()
    
    validator = SceneValidator(config_path=args.config)
    result = validator.validate(args.scene_path)
    
    print(result.summary())
    
    if args.output:
        output_path = args.output
        if not output_path.endswith(f".{args.format}"):
            output_path = f"{output_path}.{args.format}"
        result.export_report(output_path)
        print(f"Validation report saved to {output_path}")


if __name__ == "__main__":
    main()