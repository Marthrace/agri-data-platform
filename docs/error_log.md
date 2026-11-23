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

