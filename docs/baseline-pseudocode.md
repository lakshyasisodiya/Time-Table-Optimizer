# Baseline: First-Fit Timetable Placement

Inputs: course list (in file order), rooms, 10 time slots
Output: for each course, a room and slot, or "unplaced"

1. Read courses in file order.
2. For each course:
   a. Go through slots from S1 to S10.
   b. In each slot, go through rooms of the required type that fit the cohort.
   c. If there is no faculty clash, cohort clash or room clash, place the
      course here and move to the next course.
   d. If no placement is found, mark the course "unplaced".
3. Count unplaced courses and preference penalties.
4. Print the totals.

This is only a simple benchmark. The Genetic Algorithm in M1 must beat it.
