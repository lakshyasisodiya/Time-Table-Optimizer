TIME-TABLE OPTIMIZER — STEP 5 PRODUCT V1 PACKAGE

IMPORTANT
This package adds only new Step 5 files. It does not include or replace your
Step 1–4 source files. It expects the Step 4 branch to already contain:
  src/run_baseline.py
  src/run_genetic_algorithm.py
and the root requirements.txt from the earlier steps.

BEFORE COPYING
1. Commit and push all completed Step 4 work first.
2. In Git, create branch step-5-product-v1 FROM step-4-baseline.
3. Confirm VS Code shows step-5-product-v1 before copying these files.

COPY
Extract the ZIP and copy its contents into the existing repository root.
Merge the folders. The listed Step 5 files are new. Do not replace or delete
Step 1–4 scripts, data, results, notebooks or reports.

INSTALL AND RUN (from repository root, with the project .venv selected)
  python -m pip install -r requirements-product-v1.txt
  python -m streamlit run app.py
Open the local URL shown in the terminal (normally http://localhost:8501).
Enter or upload five course rows, then click Generate timetable.

CHECK THE SAME METHOD OUTSIDE THE UI
  python src/check_product_scheduler.py

RUN STEP 5 TESTS
  python -m unittest discover -s tests -p "test_product_scheduler.py" -v
You may also run the full suite:
  python -m unittest discover -s tests -v

BEFORE COMMITTING
- Run the app manually with a normal input.
- Test boundary and invalid inputs; record what actually happens.
- Compare the same input through the UI and check_product_scheduler.py.
- Save screenshots under docs/evidence/step5/.
- Complete docs/STEP-5.md with actual observations and real team contributions.
- Review git status and stage only intended Step 5 files. Never stage .venv.

The app handles one five-course scenario at a time and uses the fixed Step 1–4
room inventory and constraints. It is an educational prototype, not a live
university timetable system.
