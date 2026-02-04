from vllm import LLM, SamplingParams
import os
import time

os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"

def main():
    llm = LLM("lightonai/LightOnOCR-2-1B")
    params = SamplingParams(max_tokens = 1024, temperature = 0.7)

    start_time = time.perf_counter()
    outputs = llm.generate(["What is special about Vietnam?"], params)
    end_time = time.perf_counter()
    ex_time = end_time - start_time
    print(outputs[0].outputs[0].text.strip())
    print('-'*70)
    print(f"Executed time: {ex_time:.4f} seconds.")


if __name__ == "__main__":
    main()
# # # ubuntu: 22.04
# # # python: 3.11.14


# import torch
# print(torch.cuda.is_available())
# print(torch.version.cuda)
