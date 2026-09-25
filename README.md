# Time-Table-Optimizer

## Data Dictionary

| Field | Simple meaning | Type/unit | Starter rule |
|---|---|---|---|
| course_id | Course name/code | text | C01 to C05 |
| cohort_id | Student group | text | G1 or G2 |
| faculty_id | Teacher | text | F1 to F3 |
| weekly_sessions | Sessions required per week | whole number | 1 to 4 |
| duration_slots | Length of one session | slots | 1 or 2 |
| required_room_type | Room needed | category | classroom or lab |
| room_capacity | Max students a room holds | number | Must fit cohort size |
| room_type | Type of room | category | classroom or lab |
| slot_id | Available teaching time | text/time | 10 named slots (S1 to S10) |
