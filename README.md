# What is this?

TL;DR : This is a script to make code completion of Jetbrains AI assistant available using a Mellum model hosted on an ollama server.

Jetbrains open sourced a base version of Mellum under https://blog.jetbrains.com/ai/2025/04/mellum-goes-open-source-a-purpose-built-llm-for-developers-now-on-hugging-face/

ATM code completion in Jetbrains IDEs is using a cloud-based Mellum focal model. Code completion does not currently work 
with an on-premise model served by a local or remote ollama server. 

Please observe https://youtrack.jetbrains.com/issue/LLM-2972/Support-for-local-on-premise-LLM-models-for-AI-Pro-for-all-AI-Assistant-features to get the status of this feature request.

# WARNING

DO NOT USE THIS CODE IN PRODUCTION! THIS CODE IS FOR PEOPLE WHO WANT TO LOCALLY USE MELLUM-4b MODEL FOR CODE COMPLETION IN JETBRAINS FOR EXPLORATION OR EDUCATIONAL PURPOSES ONLY!

If you want the whole power of Jetbrains AI assistant, please consider using it with the cloud-based solution provided by Jetbrains, which will be better than this base one using Ollama.

# Installation

- in ollama, pull https://ollama.com/JetBrains/Mellum-4b-base
- in IDEA, install Jetbrains AI assistant plugin
  - disable GitHub Copilot plugin if you enabled the plugin before. Mellum is better. hi JB
- in IDEA, setup an http proxy on host 127.0.0.1 && port 8080
- install https://mitmproxy.org/

# Usage

- put your OLLAMA_HOST and OLLAMA_PORT in `rewrite.py` and set ENABLE_REWRITE=True.
- run mitmproxy with `./mitmproxy -s rewrite.py`
- you may tail the logs with `tail -f mitmproxy_script.log`
- run IDEA with your mitm http proxy activated
- open a file, then type
- code completion will use Mellum model hosted under your ollama with SAFIM instructions, see https://huggingface.co/JetBrains/Mellum-4b-base#syntax-aware-fill-in-the-middle-safim
- to stop the script, press `ctrl+c` in the mitmproxy terminal

