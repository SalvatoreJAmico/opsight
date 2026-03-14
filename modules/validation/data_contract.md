# Validation Data Contract

This module validates canonical records.

Expected record structure:

- entity_id
- timestamp
- features
- metadata

Invalid records return a validation error object.

The validation module returns a dictionary with the following fields:

status
    Indicates whether the record passed validation.
    Possible values:
        valid
        invalid

errors
    A list of validation error messages.
    Empty if the record is valid.

{
  "status": "valid",
  "errors": []
}

{
  "status": "invalid",
  "errors": [
      "Missing entity_id",
      "Features must be a dictionary"
  ]
}