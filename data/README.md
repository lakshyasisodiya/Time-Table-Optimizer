# Time-Table-Optimizer

A timetable optimizer that places courses into rooms and time slots without
faculty, room, or cohort clashes. The first method is a simple baseline; the
Soft Computing method is a Genetic Algorithm.

## Data Dictionary

| Field | Meaning | Type / unit | Rule |
|---|---|---|---|
| course_id | Course code (C01 Math, C02 Physics, C03 CS, C04 English, C05 Chemistry) | text | C01 to C05 |
| cohort_id | Student group | text | G1 or G2 |
| faculty_id | Teacher | text | F1 to F3, must not be blank |
| weekly_sessions | Sessions required per week | whole number | 1 to 4 |
| duration_slots | Length of one session | slots | 1 or 2 |
| required_room_type | Room type the course needs | category | classroom or lab |
| room_capacity | Seats in the room | whole number | positive (classroom 60, lab 30) |
| room_type | Type of the room | category | classroom or lab |
| slot_id | Time slot | text | S1 to S10 |

## Data note
All data is simulated for learning. It is not taken from any real university timetable.
