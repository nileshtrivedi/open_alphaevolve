# OpenAlphaEvolve

Quick-and-dirty attempt to replicate Google Deepmind's AlphaEvolve ([blog post](https://deepmind.google/discover/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/), [technical report](https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/AlphaEvolve.pdf)) approach for solving math and programming problems.

- Set up a JSON file as database of programs for your task, similar to fib.json
- Define an evaluator function for your task similar to `eval_fib` in `fib.py`
- make sure `GEMINI_API_KEY` is available in your environment
- At the bottom of `main.py`, change the `evolve()` call to use your eval function, database filename and max_steps and max_children
- Run `python main.py`