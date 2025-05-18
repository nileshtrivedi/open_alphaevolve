import dask
import time
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
        logs = ""
        if fib(1) == 1:
            score["num_tests_passed"] += 1
        else:
            logs += f"test_failure: fib(1) returned {fib(1)} instead of 1\n"
        if fib(3) == 2:
            score["num_tests_passed"] += 1
        else:
            logs += f"test_failure: fib(3) returned {fib(3)} instead of 2\n"
        if fib(8) == 21:
            score["num_tests_passed"] += 1
        else:
            logs += f"test_failure: fib(8) returned {fib(8)} instead of 21\n"
        time_taken = time.time() - start_time
        score["average_time"] = time_taken
        score["worst_time"] = time_taken
        score["memory_usage"] = 100
        score["cpu_usage"] = 100
    except Exception as e:
        score["logs"] += f"Error during execution: {str(e)}"
        
    return score