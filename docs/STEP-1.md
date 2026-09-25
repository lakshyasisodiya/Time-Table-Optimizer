# Step 1 Project Contract

## Team and responsibilities
- Lakshya Sisodiya (Team Leader) - Data fields/dictionary, Baseline logic, and Soft Computing (Genetic Algorithm) design
- Md. Asif - Repository setup (create folders, add members, test clone/run steps)
- Rahul Pathak - Testing & UI (write validation script, draw Product V1 sketch, collect evidence)

## One-sentence problem
Place courses into rooms and time slots without faculty, room, or cohort clashes.

## User of the product
A timetable coordinator who needs a clash-free weekly schedule.

## Inputs and units
| Field | Simple meaning | Type/unit | Starter rule |
|---|---|---|---|
| course_id | Course name/code | text | C01 to C05 |
| cohort_id | Student group | text | G1 or G2 |
| faculty_id | Teacher | text | F1 to F3 |
| weekly_sessions | Sessions required per week | whole number | 1 to 4 |
| duration_slots | Length of one session | slots | 1 or 2 |
| required_room_type | Room needed | category | classroom or lab |
| room_capacity/type | Room properties | number/category | Must fit cohort and course |
| slot_day/time | Available teaching time | text/time | 10 clearly named slots |

## Outputs and units
course_id, room_id, slot_id, faculty_id, cohort_id, plus hard-violation count and soft-penalty count

## Baseline method
1. Read courses in file order.
2. For each course, scan slots from first to last.
3. Choose the first room and slot that does not create a hard clash.
4. If no placement is possible, mark that course unplaced.
5. Count unplaced courses and preference penalties.

## Soft Computing method for M1
A Genetic Algorithm timetable for a small test case, compared with random or greedy placement.

## Advanced method for M2
Add more objectives and constraints, test larger cases, improve the interface, and deploy it.

## Dataset/scenario sources
This is example/simulated data created by the team for learning purposes. Course names, room names, and time slots are simplified and are NOT taken from any real university timetable. All values are assumptions made by the team for Step 1 testing.

## Five mandatory test cases
1. **Fixture 1** - 5 courses (Math, Physics, CS, English, Chemistry), 3 rooms, 10 slots -> A feasible timetable must exist.
2. **Fixture 2** - Only one small room available -> Room shortage must be reported.
3. **Fixture 3** - Two courses, same faculty, same slot -> Faculty clash must be detected.
4. **Fixture 4** - Two courses, same cohort, same slot -> Cohort clash must be detected.
5. **Fixture 5** - Valid schedule but outside preferred time -> Soft penalty, not a hard failure.

## Product V1 screen sketch
(Insert screenshot/photo of docs/product-v1-sketch.png here after Rahul creates it)

## Risks and assumptions
- All course, room, and faculty data is simulated/example data, not real.
- Room capacity and type are fixed and simplified for Step 1 (only "classroom" or "lab").
- Only 10 time slots are used in Step 1; more slots may be added later.
- The baseline method is a simple first-fit rule, not the final Genetic Algorithm.
- Data will be scaled up to 10,000+ records only in Step 2, after this small sample is validated.

## Step 1 completion evidence
- Repository link: https://github.com/YOUR-USERNAME/Time-Table-Optimizer
- Commit history: (add link once pushed)
- Validation output screenshot: results/step1/
- Product V1 sketch: docs/product-v1-sketch.png
