# Contract: User

Application user

## Fields
- id: string [required]
- email: string [required] (email)
- username: string [required] (min:3)
- password_hash: string [required]

## Invariants
- email is required
- username must be at least 3 characters