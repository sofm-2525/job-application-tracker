# AI Usage Documentation

> ✏️ **Draft — review and edit before submitting.** Sections marked **TODO** need your own words.
> Delete this note when you're done.

## Tools Used

- **Claude (Anthropic)** – checking my SQL assignment results, debugging MySQL Workbench errors,
  generating the project's `schema.sql`, Flask routes, HTML templates and CSS, and drafting the README.

<!-- TODO: add any other tools you used (ChatGPT, Gemini, GitHub Copilot...) -->

## Key Prompts

1. "My professor gave us the schema for the database to test bit by bit, but I'm not sure if I'm getting the right results." (shared my Assignment 3 code and the EXPLAIN commands)
2. "If I want to execute a command, what's the best way to do that? I just do Query > Execute (all or selection)."
3. "Why is everything still NULL after executing this line?" (with a screenshot of the Result Grid)
4. Shared the Action Output showing `Error Code: 1242. Subquery returns more than 1 row` and asked what went wrong.
5. "Can you give me what I need to paste into my code from the assignment?" (Assignment 4: transactions)
6. Shared the full project specification and asked for help building the database, Flask app, and Job Match feature.

## What Worked Well

- **Explaining error messages.** Claude used my Action Output log to find the real cause of `Error 1242`:
  I had run the same `INSERT` twice, so the subquery found two companies with the same name.
- **Catching a bug in the assignment instructions.** The Assignment 4 code used `'text' + CURDATE()`, which doesn't
  join text in MySQL. Claude replaced it with `CONCAT()`.
- **Spotting a schema mismatch.** The project spec uses different columns than the tables from the assignments
  (`contact_name` instead of `first_name`/`last_name`, plus the `requirements` and `interview_data` JSON columns),
  so the project needed a new `schema.sql`.
- **Generating the CRUD boilerplate quickly.** The routes, forms and templates for all four tables followed one pattern.
- **The Job Match algorithm:** match % = required skills I have ÷ total required skills, sorted from highest to lowest.

## What I Modified

<!-- TODO: be specific and honest. Examples of things you might have done — keep only what's true and add your own: -->
- Tested every page in my browser against my own MySQL database and reported errors back to fix
- Changed the sample data to …
- Changed the look of … in `style.css`
- Added / removed …

## Lessons Learned

- **How a statement is run matters as much as the SQL itself.** In MySQL Workbench, Cmd+Enter runs the statement
  under the cursor and doesn't move to the next one, so pressing it twice runs the same `INSERT` twice. Highlighting
  one full statement (through the `;`) and pressing Cmd+Shift+Enter is more predictable.
- **Always check the Action Output.** The ✅/❌ log showed exactly which statement failed and why.
- **Savepoints only exist inside a transaction.** Without `START TRANSACTION`, autocommit saves every statement
  right away, so `ROLLBACK TO` fails with `SAVEPOINT does not exist`.
- **AI-generated or provided code still needs testing.** Even the assignment's own code had a MySQL-specific bug.
- **Use IDs, not names, to update or delete specific rows.** Names can be duplicated; primary keys can't.

<!-- TODO: add 1–2 lessons in your own words -->
