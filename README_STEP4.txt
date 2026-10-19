TIME-TABLE OPTIMIZER — STEP 4 PACKAGE

IMPORTANT CONTEXT
The provided SC11 PDF is a worked example and explicitly says other projects must adapt the baseline and measures. Your current Step 3 contains a first-fit baseline, not a Genetic Algorithm. This Step 4 adaptation adds a permutation GA and compares it with that existing first-fit baseline so the comparison is meaningful, while preserving all Step 3 files.

FILES IN THIS PACKAGE
- src/run_genetic_algorithm.py: project-specific GA scheduling method
- src/compare_baseline.py: fair, repeatable first-fit-vs-GA evaluation
- notebooks/03_baseline_comparison.ipynb: notebook to run and save
- docs/STEP-4.md: report generated with real run results
- tests/test_genetic_scheduler.py: GA scheduler checks

HOW TO APPLY IT
1. Save all your current files in VS Code.
2. Confirm Step 3 was committed and pushed.
3. In VS Code terminal, go to the repository root and run:
       git status
   If the working tree is clean, create the branch from Step 3:
       git switch step-3-baseline
       git pull origin step-3-baseline
       git switch -c step-4-baseline
4. Extract this ZIP. Copy the contents INSIDE the extracted folder into the existing Time-Table-Optimizer repository, merging folders. Do not overwrite Step 1/2/3 files.
5. Make sure `data/processed/cleaned_scenarios.csv` exists. If it does not, run:
       python src/prepare_data.py
6. Run the comparison:
       python src/compare_baseline.py
   It compares both methods on all 10,000 Step 2 scenarios, checks that scenario IDs do not cross categories, verifies the first-fit totals against accepted Step 3, and uses the same room inventory and constraints for both methods. Allow a few minutes for the full run. If interrupted, rerun the same command; it resumes from temporary progress saved outside the repository.
7. Run tests:
       python -m unittest discover -s tests -v
8. Open `notebooks/03_baseline_comparison.ipynb`, select the same `.venv` kernel, click Run All, and save the notebook. The notebook loads and validates the saved output CSVs; it does not run the GA a second time.
9. Open `docs/STEP-4.md`. Confirm the numbers match the CSV. Replace the team contribution prompt with real contributions.
10. Review `git status`, then stage/commit/push only once the script, notebook, reports, chart and tests are ready.

GIT COMMANDS AFTER REVIEW
    git add README_STEP4.txt src/run_genetic_algorithm.py src/compare_baseline.py notebooks/03_baseline_comparison.ipynb docs/STEP-4.md data/reports/step4_baseline_metrics.csv data/reports/step4_comparison.csv data/reports/step4_paired_scenario_results.csv results/step4_baseline_vs_ga.png tests/test_genetic_scheduler.py
    git status
    git commit -m "Add fair baseline and genetic algorithm comparison"
    git push -u origin step-4-baseline

Do not merge this branch into main unless your teacher asks. The benchmark uses all 10,000 simulated scenarios and a simplified three-room inventory. The GA search budget is population 8 and 5 generations per scenario to keep the full benchmark practical; describe these limitations honestly.
