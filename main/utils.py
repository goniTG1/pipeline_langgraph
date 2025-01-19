import re


def validate_extracted_data(data):
    """Validate extracted data using regex patterns."""
    validation_rules = {
        "names": r"^[A-Za-z ]+$",
        "dates": r"^\d{4}-\d{2}-\d{2}$",
        "amounts": r"^\$\d+$",
    }

    errors = {}
    for key, pattern in validation_rules.items():
        for value in data.get(key, []):
            if not re.match(pattern, value):
                errors[key] = f"Invalid {key}: {value}"

    if errors:
        raise ValueError(f"Validation failed: {errors}")

    return True
