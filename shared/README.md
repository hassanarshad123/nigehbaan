# Shared Constants

Cross-language shared constants and type definitions for the Nigehbaan platform.

## Usage

### JavaScript/TypeScript (Frontend)
```js
import constants from '../../shared/constants.json';
```

### Python (Backend)
```python
import json
with open('shared/constants.json') as f:
    constants = json.load(f)
```

## Files

- `constants.json` — Province P-codes, incident type enums, report type enums, layer color mappings, and other shared constants
