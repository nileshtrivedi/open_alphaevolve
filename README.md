# OpenAlphaEvolve

Quick-and-dirty attempt to replicate Google Deepmind's AlphaEvolve approach for solving math and programming problems.

- Set up a JSON file for your task, similar to fib.json
- Define your evaluator in `main.py` like `eval_fib`
- make sure `GEMINI_API_KEY` is available in your environment
- Change the `evolve()` call with your eval function name, database filename and max_steps and max_children
- Run `python main.py`