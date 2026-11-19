# AI Usage Documentation


## Tools Used

- **Claude (Anthropic)** – checking my SQL assignment results, debugging MySQL Workbench errors,
  generating the project's `schema.sql`, Flask routes, HTML templates and CSS, and drafting the README.


## Key Prompts

1. "My professor gave us the schema for the database to test bit by bit, but I'm not sure if I'm getting the right results." (shared my Assignment 3 code and the EXPLAIN commands)
2. "Why is everything still NULL after executing this line?" (with a screenshot of the Result Grid)
4. Shared the Action Output showing `Error Code: 1242. Subquery returns more than 1 row` and asked what went wrong.
6. Shared the full project specification and asked for help to outline the steps for completing each phase: database schema, Flask routes, organizing things in github, etc

## What Worked Well

- **Explaining error messages.** Claude used my Action Output log to find the real cause of `Error 1242`:
  I had run the same `INSERT` twice, so the subquery found two companies with the same name.
- **Catching a bug in the assignment instructions.** The Assignment 4 code used `'text' + CURDATE()`, which doesn't
  join text in MySQL. Claude replaced it with `CONCAT()`.
- **Spotting a schema mismatch.** The project spec uses different columns than the tables from the assignments
  (`contact_name` instead of `first_name`/`last_name`, plus the `requirements` and `interview_data` JSON columns),
  so the project needed an adjustment to `schema.sql`.
- **Generating the CRUD boilerplate quickly.** The routes, forms and templates for all four tables followed one pattern.
- **The Job Match algorithm:** match % = required skills I have ÷ total required skills, sorted from highest to lowest.

## What I Modified

- Tested every page in my browser against my own MySQL database and reported errors back to fix
- Added / removed skills to job requirements to make the job match give the same results as the project specification example (Software Developer at TechCorp - 100% (3/3 skills) & Data Analyst at DataCo - 67% (2/3 skills) Missing: Tableau)


## Lessons Learned

- **How a statement is run matters as much as the SQL itself.** I noticed I tend to make a lot of small mistakes such as just running a line in SQL using cmd + enter, but I realized that this was causing me to insert things multiple times. I was frustrated before realizing that SQL is just a bit finniky compared to other languages I am more used to.
- **Always check the Action Output.** The ✅/❌ log showed exactly which statement failed and why.
- **Savepoints only exist inside a transaction.** Without `START TRANSACTION`, autocommit saves every statement
  right away, so `ROLLBACK TO` fails with `SAVEPOINT does not exist`. This felt redundant when I kept running into errors, but then I realized how much using the Action Output log would help me.
- **AI-generated or provided code still needs testing.** Even the assignment's own code had a MySQL-specific bug.
- **Use IDs, not names, to update or delete specific rows.** Names can be duplicated; primary keys can't. Running my code through Claude helped me realize this! I knew primary keys are important, but it is different to practice these conventions rather than just memorize its function for a quiz. 


