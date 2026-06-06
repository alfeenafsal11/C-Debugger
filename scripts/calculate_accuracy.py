import csv
import asyncio
import os
import sys

EVAL_PROMPT = """You are an automated evaluator comparing two bug explanations.
You will assess if the GENERATED explanation correctly identifies the same core issue as the GROUND TRUTH explanation.

GROUND TRUTH: "{truth}"
GENERATED: "{generated}"

Are they semantically equivalent in identifying the root issue? (i.e. do they point to the same underlying problem, even if phrased differently?).
Answer ONLY "YES" or "NO".
"""

async def evaluate_single_explanation(id_, gt_exp, gen_exp, llm):
    prompt = EVAL_PROMPT.format(truth=gt_exp.strip(), generated=gen_exp.strip())
    try:
        if llm:
            response = await llm.acomplete(prompt)
            answer = response.text.strip().upper()
        else:
            raise ValueError("No LLM evaluator client initialized.")
        is_match = "YES" in answer
    except Exception as e:
        is_match = False
        answer = f"ERROR: {e}"
    return id_, gt_exp, gen_exp, is_match, answer

async def calculate_accuracy(samples_path, output_path):
    token = os.environ.get("HF_TOKEN")
    
    if not token:
        print("Please set the HF_TOKEN environment variable.")
        return

    from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
    llm = HuggingFaceInferenceAPI(
        model_name="meta-llama/Meta-Llama-3-8B-Instruct",
        token=token,
        temperature=0.1,
        max_tokens=10
    )
    print("Using Hugging Face (Llama-3-8B) for evaluation.")

    ground_truth = {}
    with open(samples_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ground_truth[row["ID"]] = row["Explanation"]

    generated = {}
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            generated[row["ID"]] = row["Explanation"]

    count = 0
    matches = 0

    print(f"{'ID':>4} | {'Match (LLM)':>15} | {'Ground Truth Preview':>30} | {'Generated Preview':>30}")
    print("-" * 88)

    tasks = []
    for id_, gen_exp in generated.items():
        if id_ in ground_truth:
            tasks.append(evaluate_single_explanation(id_, gt_exp, gen_exp, llm))
    
    results = await asyncio.gather(*tasks)

    for id_, gt_exp, gen_exp, is_match, answer in results:
        if is_match:
            matches += 1
        count += 1
        
        gt_preview = (gt_exp[:27] + '...') if len(gt_exp) > 30 else gt_exp
        gen_preview = (gen_exp[:27] + '...') if len(gen_exp) > 30 else gen_exp
        
        print(f"{id_:>4} | {'YES' if is_match else 'NO':>15} | {gt_preview:>30} | {gen_preview:>30}")

    if count > 0:
        print("-" * 88)
        print(f"Total Evaluated: {count}")
        print(f"Semantic Matches: {matches}")
        print(f"LLM Accuracy Score: {(matches / count) * 100:.2f}%")
    else:
        print("No matching IDs found to compare.")

if __name__ == "__main__":
    # Find paths relative to script or repo root
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    default_samples = os.path.join(base_dir, "datasets", "raw", "samples.csv")
    default_output = os.path.join(base_dir, "outputs", "output.csv")
    
    samples_path = sys.argv[1] if len(sys.argv) > 1 else default_samples
    output_path = sys.argv[2] if len(sys.argv) > 2 else default_output
    
    asyncio.run(calculate_accuracy(samples_path, output_path))
