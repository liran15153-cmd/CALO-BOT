# Safety

## Safety-Sensitive Signals

The safety layer flags:

- Severe pain or injury
- Dizziness, fainting, chest pain, or dangerous symptoms
- Eating disorder language or extreme restriction
- Rapid unhealthy weight-loss requests
- Dangerous supplements or substances
- Medical conditions that require qualified care
- Minor/teen-specific risk when age range is under 18

## Response Policy

Unsafe cases should:

- Avoid diagnosis
- Avoid detailed dangerous instructions
- Recommend stopping painful or risky activity
- Suggest qualified professional guidance where appropriate
- Save a `safety_event`
- Keep tone calm and non-alarming

## Upload Safety

Meal uploads are local-only in v1. The backend accepts JPEG, PNG, and WEBP, checks file signatures against the declared content type, stores randomized filenames, and rejects files over 5 MB.

Remaining production gaps:

- Re-encode images before storage
- Strip EXIF and metadata
- Add malware scanning if uploads become public
- Add retention and cleanup policies
- Avoid returning absolute local paths in public APIs
