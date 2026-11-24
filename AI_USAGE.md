# AI Usage Disclosure

## Tools used

- Claude Code (Claude Opus 5.5, Anthropic), in the Claude desktop app

## Conversation links

- Link 1: TODO — paste the share link of the Claude Code conversation here

## What I used them for

- Writing the implementation of all four modules from the assignment description and the starter skeleton
- Checking the code against the public test script and extra edge cases (BOM, `\r\n` endings, non-ASCII codes, non-padded dates, missing folders, bad query files)

## Which parts of the code were AI-generated or substantially AI-assisted

| File | Function or part | How (generated / modified / explained) |
| --- | --- | --- |
| `validator.py` | `load_airports`, `validate_row`, `to_record`, `is_valid_datetime` | generated |
| `csv_loader.py` | `parse_files`, `_read_lines` | generated |
| `query.py` | `run_query`, `run_queries`, `is_valid_query`, `_matches` | generated |
| `flight_parser.py` | `main`, argument parsing, logging setup, file reading/writing helpers | generated |

## Key prompts

1. "Read the assignment and do it" (with screenshots of the assignment description and the starter zip attached)
2. TODO — add any follow-up prompts you used

## What I changed or verified myself

TODO — for example: I ran `python tests/run_public_tests.py` in Codespaces (Python 3.13), read through the validation order and the query rules, and set my student constants.
