\# Error Log



\## 001 - Stray file .env.exampl

\- Date: 23 Nov 2026

\- Symptom: git ls-files showed .env.exampl next to .env.example

\- Cause: the first echo command wrote DB\_HOST=localhost into .env.exampl instead of .env.example, so the real file was missing that line (found by comparing file sizes: 19 bytes vs 78)

\- Fix: git rm .env.exampl, then appended DB\_HOST=localhost to .env.example

\- Prevention: run git ls-files after creating files, before pushing



\## 002 - Stray ^Z characters in a pasted command

\- Date: 23 Nov 2026

\- Symptom: import check printed nothing

\- Cause: Ctrl+Z characters at the start of the pasted line

\- Fix: retyped the command at an empty prompt

\- Prevention: check the line starts at the prompt before pressing Enter



\## 003 - PostgreSQL service stopped, psql missing, access denied

\- Date: 23 Nov 2026

\- Symptom: psql not recognised; net start and sc delete returned System error 5

\- Cause: leftover files and a stale service from an earlier, incomplete install; service commands were run in a non-administrator prompt

\- Fix: ran sc delete in an administrator prompt, renamed the old folder to 17\_old, installed PostgreSQL 19 with Command Line Tools

\- Prevention: check for "Administrator" in the window title before service commands; check the version folder after installing



\## 004 - Duplicate DB\_HOST line in .env.example

\- Date: 23 Nov 2026

\- Symptom: type .env.example showed DB\_HOST=localhost twice

\- Cause: the echo command that appends DB\_HOST was run twice

\- Fix: manual Notepad edit did not remove it; used findstr /v to drop the lines and re-appended one

\- Prevention: check with type before repeating an append command



\## 005 - db\_test.py not found

\- Date: 23 Nov 2026

\- Symptom: python src\\utils\\db\_test.py returned Errno 2, no such file

\- Cause: the file was never saved after the first Notepad attempt

\- Fix: recreated it and confirmed the name with dir src\\utils

\- Prevention: run dir after creating a file to confirm it exists



\## 006 - FAOSTAT download covered one year only

\- Date: 23 Nov 2026

\- Symptom: first file had 6 rows, all year 2024

\- Cause: only one year was selected in the FAOSTAT download filter; the re-download was saved as "(1).csv" and the old file was nearly used again

\- Fix: re-downloaded with all years selected; checked size and row count (90 rows, 2010 to 2024) before copying

\- Prevention: check row count and year range straight after downloading



\## 007 - Git line-ending warning on raw CSV

\- Date: 23 Nov 2026

\- Symptom: "LF will be replaced by CRLF" when adding data/raw files

\- Cause: Git's default line-ending conversion on Windows

\- Fix: .gitattributes with "data/raw/\* -text" so raw files stay byte-identical

\- Prevention: add .gitattributes before committing data files



\## 008 - ModuleNotFoundError when running the loader

\- Date: 24 Nov 2026

\- Symptom: No module named 'src.utils.db', then No module named 'src'

\- Cause: db.py had not been created; the second time the script was run directly instead of as a module

\- Fix: created src\\utils\\db.py; run with python -m src.load.load\_raw from the project root

\- Prevention: run dir to confirm each file exists; always use -m for project modules



\## 009 - psql password authentication failed

\- Date: 26 Nov 2026

\- Symptom: psql rejected the password; the same command had worked minutes earlier

\- Cause: password mistyped at the hidden prompt (nothing shows while typing)

\- Fix: retried slowly with Caps Lock off; confirmed .env still worked with db\_test.py

\- Prevention: if psql fails but db\_test.py works, the typed password is the problem



\## 010 - relation "staging.prices" does not exist

\- Date: 26 Nov 2026

\- Symptom: load\_staging failed with UndefinedTable

\- Cause: sql\\04\_create\_staging\_tables.sql had not been run, so the tables did not exist

\- Fix: ran the SQL file with psql and checked with \\dt staging.\*

\- Prevention: run the SQL step and confirm the tables exist before running Python that uses them



\## 011 - Test damage carried into analytics layer

\- Date: 28 Nov 2026

\- Symptom: Maize average price per kg was 3.95 retail and 3.41 wholesale instead of 3.81 and 3.25

\- Cause: two staging prices set to 99 for the repair test were never repaired, so the star build copied them

\- Fix: ran python -m src.run\_pipeline --start 2021-01-01 --end 2021-12-31

\- Prevention: repair test damage straight away; row-count checks cannot detect changed values

