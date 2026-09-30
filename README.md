
Run the vLLM backends, LiteLLM proxy, and agent together with:

```sh
bash run_local.sh
```

The script waits for each service to become healthy before continuing. It starts only the Qwen 2.5 7B 4-bit model. It looks for `vllm` on `PATH` or at `~/.venv-vllm-metal/bin/vllm`; set `VLLM_BIN` to use another installation. Logs are written to `$TMPDIR/llm-fun/` (usually under `/tmp`); stopping the agent with Ctrl-C also stops the services.

Example session:

```text
Ask a question, or type 'quit' to exit.
You: What is the weather in Boston?
Assistant: According to the tool, the current weather in Boston is moderate drizzle, with a temperature of 57.1°F (feels like 49.0°F), humidity of 87%, and a wind speed of 21.4 mph.
You: quit
Goodbye!
```