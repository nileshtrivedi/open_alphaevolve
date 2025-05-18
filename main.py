import dask
import json
import random
import uuid
import os
import time
import logging
from google import genai

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"] or "YOUR_GEMINI_API_KEY"

@dask.delayed
def eval_fib(code):
    score = {
        "num_tests_passed": 0,
        "average_time": 10,
        "worst_time": 100,
        "memory_usage": 100,
        "cpu_usage": 100
    }
    try:
        start_time = time.time()
        temp_module = {}
        exec(code, temp_module)
        fib = temp_module.get('fib', lambda: None)
        if fib(1) == 1:
            score["num_tests_passed"] += 1
        if fib(3) == 2:
            score["num_tests_passed"] += 1
        if fib(8) == 21:
            score["num_tests_passed"] += 1
        time_taken = time.time() - start_time
        score["average_time"] = time_taken
        score["worst_time"] = time_taken
        score["memory_usage"] = 100
        score["cpu_usage"] = 100
    except Exception as e:
        score["logs"] = f"Error during execution: {str(e)}"
        
    return score

def build_prompt(task, parent_program, inspirations):
    """Builds a prompt for the LLM based on parent and inspiration programs."""
    prompt = "You are an expert programmer tasked with evolving code to solve a problem.\n"
    prompt += "Your goal is to suggest modifications (as a diff) to the 'Current program' to improve it.\n"
    prompt += "Consider the 'Prior programs' as inspiration for good ideas or approaches.\n\n"
    prompt += task + "\n\n"
    
    prompt += f"Current program to be modified: \n```\n{parent_program['code']}\n```\n\n"
    prompt += "Current program's evaluation scores:\n"
    for key, value in parent_program['score'].items():
        prompt += f"- {key}: {value}\n"
    
    if inspirations:
        prompt += "Inspiration programs:\n"
        for ins in inspirations:
            prompt += f"\n```\n- {ins['code']}\n```\n\n"
            prompt += "Inspiration program's evaluation scores:\n"
            for key, value in ins['score'].items():
                prompt += f"- {key}: {value}\n"
            prompt += "\n\n"
            
    prompt += "Suggest modifications to improve the current program."
    prompt += "Provide your suggested change in a diff format, like this:\n"
    prompt += "<<<<<<< SEARCH\n"
    prompt += "# Original code block to be found and replaced\n"
    prompt += "=======\n"
    prompt += "# New code block to replace the original\n"
    prompt += ">>>>>>> REPLACE\n\n"
    prompt += "If you are suggesting adding new code where nothing existed, "
    prompt += "the SEARCH block can be a comment indicating where to insert, "
    prompt += "or an adjacent line of code.\n"
    prompt += "If you are suggesting deleting code, the REPLACE block should be empty.\n"
    prompt += "Focus on a single, meaningful change. The change should be syntactically correct Python.\n"
    prompt += "Please provide only the diff block in your response. Do not provide any comments or codeblocks.\n"
    # Add more specific instructions based on the math/programming task if needed.
    prompt += "For example, if the current program is:\n"
    prompt += "```python\n# My Function\ndef my_func(x):\n    return x * 2\n```\n"
    prompt += "And you want to change it to `return x * 3`, the diff would be:\n"
    prompt += "<<<<<<< SEARCH\n    return x * 2\n=======\n    return x * 3\n>>>>>>> REPLACE\n"
    return prompt

def generate_diff_with_llm(prompt):
    """Generates a code modification (diff) using the LLM."""
    gemini = genai.Client(api_key=GEMINI_API_KEY)
    print("Generating diff with LLM...")
    print(f"Prompt: \n\n--------------\n\n{prompt}\n\n--------------\n")
    response = gemini.models.generate_content(model="gemini-2.5-flash-preview-04-17", contents=prompt)
    diff = response.text
    print(f"Response: \n\n--------------\n\n{diff}\n\n--------------\n\n\n")
    return diff

def apply_diff(parent_program, diff):
    """Applies the diff to the parent program to create a child program."""
    child_program = parent_program
    try:
        if "<<<<<<< SEARCH" not in diff or "=======" not in diff or ">>>>>>> REPLACE" not in diff:
            print("Warning: Diff format incorrect. Skipping application.")
            return parent_program # Return parent if diff is malformed

        parts = diff.split("=======")
        search_block = parts[0].replace("<<<<<<< SEARCH\n", "").rstrip()
        replace_block = parts[1].replace("\n>>>>>>> REPLACE", "").replace(">>>>>>> REPLACE", "").strip() # Handle cases with or without newline

        if search_block in child_program:
            child_program = child_program.replace(search_block, replace_block, 1)
            print("Diff applied successfully.")
        else:
            # Attempt to apply common cases like adding to an empty function
            if "pass" in search_block and "pass" in child_program:
                 child_program = child_program.replace("pass", replace_block, 1)
                 print("Diff applied by replacing 'pass'.")
            else:
                print("Warning: Search block not found in parent program. Diff not applied.")
                # Optionally, try to append if it's a completely new block and search was e.g. a comment
                # This part can be made more sophisticated.
                # For now, if exact search fails, we return the parent.
                return parent_program

    except Exception as e:
        print(f"Error applying diff: {e}")
        return parent_program # Return parent in case of error

    print(f"--- Child Program ---\n{child_program}\n---------------------")
    return child_program

def add_to_database(db, program_code, score):
    """Adds the new program and its evaluation results to the database."""
    new_program_entry = {
        "id": str(uuid.uuid4()),
        "code": program_code,
        "score": score
    }
    db["programs"].append(new_program_entry)
    print(f"Added program {new_program_entry['id']} with scores: {score}")
    
def sample_from_db(db):
    programs = db.get("programs", [])
    parent_program = random.choice(programs)
    num_inspirations = 2
    inspirations = []
    if len(programs) > 1:
        inspirations = random.sample([p for p in programs if p['id'] != parent_program['id']], 
                                     min(num_inspirations, len(programs)-1))
    return parent_program, inspirations

def save_database(db_path, database):
    """Saves the program database to a JSON file."""
    with open(db_path, 'w') as f:
        json.dump(database, f, indent=4)
        
def evolve(evaluator_func, db_path, max_steps=1, num_children=1):
    db = json.load(open(db_path))
    for step in range(max_steps):
        parent_program, inspirations = sample_from_db(db)
        prompt = build_prompt(db["task"], parent_program, inspirations)
        llm_tasks = []
        for _ in range(num_children):
            llm_tasks.append(dask.delayed(generate_diff_with_llm)(prompt))
        
        suggested_diffs = dask.compute(*llm_tasks)
        evaluation_tasks = []
        child_programs_generated = []
        
        for diff in suggested_diffs:
            child_program_code = apply_diff(parent_program['code'], diff)
            child_programs_generated.append(child_program_code)
            evaluation_tasks.append(evaluator_func(child_program_code))
        
        evaluation_results = dask.compute(*evaluation_tasks)
        for i, child_program_code in enumerate(child_programs_generated):
            results = evaluation_results[i]
            add_to_database(db, child_program_code, results)
        
        save_database(db_path, db)
    
    final_programs = db.get("programs", [])
    if final_programs:
        # Example: find program with highest 'num_tests_passed'
        best_program = max(final_programs, key=lambda p: p['score'].get('num_tests_passed', 0))
        print(f"Best program found (ID: {best_program['id']}):")
        print(best_program['code'])
        print(f"Scores: {best_program['score']}")
    else:
        print("No programs in the final database.")
        

if __name__ == '__main__':
    dask.config.set(scheduler='threads')
    evolve(eval_fib, "fib.json", max_steps=1, num_children=1)