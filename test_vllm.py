from vllm import LLM, SamplingParams

llm = LLM("lightonai/LightOnOCR-2-1B", gpu_memory_utilization = 0.5)
params = SamplingParams(max_tokens = 1024, temperature = 0.7)

outputs = llm.generate(["What is special about Vietnam?"], params)
print(outputs[0].outputs[0].text.strip())


# ubuntu: 22.04
# python: 3.11.14
