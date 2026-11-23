\# Error Log



\## 001 - Stray file .env.exampl

\- Date: 23 Nov 2026

\- Symptom: git ls-files showed .env.exampl next to .env.example

\- Cause: typo while creating files with echo on the command line

\- Fix: git rm .env.exampl

\- Prevention: run git ls-files after creating files, before pushing



\## 002 - Stray ^Z characters in a pasted command

\- Date: 23 Nov 2026

\- Symptom: import check printed nothing

\- Cause: Ctrl+Z characters at the start of the pasted line

\- Fix: retyped the command at an empty prompt

\- Prevention: check the line starts at the prompt before pressing Enter

