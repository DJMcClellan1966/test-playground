# Contract: Task

A task in the system

## Fields
- id: string [required]
- title: string [required] (min:1)
- description: text [optional]
- priority: integer [required] (min:1, max:5) = 1
- completed: boolean [required] = False
- user_id: string [required]

## Invariants
- title cannot be empty
- priority >= 1
- priority <= 5

## Relations
- user_id: belongs_to:User