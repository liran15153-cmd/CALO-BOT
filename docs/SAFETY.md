# Safety

## Safety-Sensitive Signals

The safety layer flags:

- Severe pain or injury
- Dizziness, fainting, chest pain, or dangerous symptoms
- Eating disorder language or extreme restriction
- Rapid unhealthy weight-loss requests
- Dangerous stimulant, steroid, or diuretic requests

The local keyword layer covers both English and Hebrew phrasing for common high-risk cases, including chest pain, dizziness, fainting, shortness of breath, sharp pain, skipped meals, purging language, extreme calorie restriction, and unsafe substances.

## Response Policy

Unsafe cases should:

- Avoid diagnosis
- Avoid detailed dangerous instructions
- Recommend stopping painful or risky activity
- Suggest qualified professional guidance where appropriate
- Save a `safety_event`
- Keep tone calm and non-alarming

The `coaching_knowledge` layer repeats these boundaries in provider context. It is not a substitute for clinically reviewed triage, but it keeps provider-backed coaching aligned with the local safety policy.

Preparticipation screening rules are included in provider context: red flags stop workout recommendations and point to qualified medical help; chronic conditions without red flags get conservative, gradual guidance and a prompt to follow professional instructions.

## Upload Safety

Meal uploads are local-only in v1. The backend accepts JPEG, PNG, and WEBP, checks file signatures against the declared content type, stores randomized filenames, and rejects files over 5 MB.

Remaining production gaps:

- Re-encode images before storage
- Strip EXIF and metadata
- Add malware scanning if uploads become public
- Add retention and cleanup policies
- Avoid returning absolute local paths in public APIs

Safety gaps before public release:

- Minor/teen-specific risk handling from profile age data
- Broader medical-condition triage
- Clinically reviewed safety taxonomy and copy
