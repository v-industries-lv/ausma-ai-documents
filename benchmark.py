import argparse
import ollama
parser = argparse.ArgumentParser()
parser.add_argument('--model', type=str, help='Which model to benchmark.', required=True)
parser.add_argument('--iterations', type=int, help='How many iterations to measure.', default=5)
parser.add_argument('--use-cpu', action='store_true', help='Use CPU only')
args = parser.parse_args()

def benchmark(use_cpu = True):
    options = {
        "seed": 42
    }
    if use_cpu:
        options["num_gpu"] = 0

    response = ollama.chat(
        model=args.model,
        messages=messages,
        options=options
    )
    output = {
        "eval_duration": response.eval_duration,
        "prompt_eval_duration": response.prompt_eval_duration,
        "eval_count": response.eval_count,
        "prompt_eval_count": response.prompt_eval_count
    }
    return output

print(f"Benchmarking model: {args.model} {", cpu only" if args.use_cpu else ""}")

sys_message = {
    'role': 'system',
    'content': "You are a helpful assistant. "
}
user_message = {
    'role': 'user',
    'content': "What is the meaning of life?"
}
messages = [sys_message, user_message]
tokens_per_second = []

# Start-up the model
benchmark(args.use_cpu)

for i in range(0, args.iterations):
    metrics = benchmark(args.use_cpu)
    tokens = metrics["eval_count"] + metrics["prompt_eval_count"]
    duration = (metrics["eval_duration"] + metrics["prompt_eval_duration"])/1000000000
    print(f"{tokens} tokens in {duration} seconds: {tokens/duration} t/s")
    tokens_per_second.append(tokens/duration)
print(f"Average processing speed: {sum(tokens_per_second)/len(tokens_per_second)} t/s")