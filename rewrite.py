from mitmproxy import http
import json
import os
import time

##################################
# edit as needed
##################################
OLLAMA_HOST="10.0.29.96"
OLLAMA_PORT="11435"
ENABLE_REWRITE = True
##################################

inner1 = {
    "completion": "__COMPLETION__",
    "meta": {
        "raw_completion": "__COMPLETION__",
        "truncate_reason": None,
        "skip_reason": None,
        "token_healing_prefix": "",
        "tokens": [],  # TODO FIXME replace with actual tokens from __COMPLETION__
        "token_log_probs": [-1.0, -1.0, -1.0],
        "normalized_token_log_probs": [-1.0, -1.0, -1.0],
        "token_entropies": [3.625, 3.625, 3.625]
    },
    "type": "FirstLine" # 1st line
}
inner2 = {
    "filtered": False,
    "filter_pass_probability": 0.99,
    "random_pass": False,
    "type": "FirstLineFilter"
}
# WIP for 'Rest'
x_inner2_1 = {
    "filtered": False,
    "content": {
        "content": "",
        "meta": {
            "raw_completion": "",
            "truncate_reason": None,
            "skip_reason": "ONLY_SPACES",
            "token_healing_prefix": "",
            "tokens": [],
            "token_log_probs": [],
            "normalized_token_log_probs": [],
            "token_entropies": []
        }
    },
    "type": "Rest"
}
inner2_1 = {
    "filtered": False,
    "filter_pass_probability": 0.99,
    "random_pass": False,
    "type": "RestFilter"
}
inner3 = {
    "type": "Meta",
    "stop_reason": "eos_token",
    "llm_name": "Mellum-4b-base"
}

events = [
    'data: ' + json.dumps({"type": "Content", "event_type": "data", "content": json.dumps(inner1)}),
    'data: ' + json.dumps({"type": "Content", "event_type": "data", "content": json.dumps(inner2)}),
    'data: ' + json.dumps({"type": "Content", "event_type": "data", "content": json.dumps(inner2_1)}),
    'data: ' + json.dumps({"type": "Content", "event_type": "data", "content": json.dumps(inner3)}),
    'data: end'
]

            
def log_to_file(msg):
    with open("mitmproxy_script.log", "a") as f:
        f.write(msg + "\n")
            
def response(flow: http.HTTPFlow):    
    
    log_to_file(f"Response URL: {flow.request.pretty_url}")
    log_to_file(f"Response: {flow.response}")
                    
    if flow.request.pretty_url == "http://" + OLLAMA_HOST + "/v1/chat/completions":        
        try:
            json_response = flow.response.json()
            # log_to_file(f"JSON Response for chat: {json.dumps(json_response, indent=4)}")
        except Exception as e:
            log_to_file(f"Error parsing JSON response: {e}") 
            Raise(e)
            
        content = json_response["choices"][0]["message"]["content"]
        # log_to_file(f"content: {content}")
                
        inner1["completion"] = content
        inner1["meta"]["raw_completion"] = content
        events = [
                'data: ' + json.dumps({"type": "Content", "event_type": "data", "content": json.dumps(inner1)}),
                'data: ' + json.dumps({"type": "Content", "event_type": "data", "content": json.dumps(inner2)}),
                'data: ' + json.dumps({"type": "Content", "event_type": "data", "content": json.dumps(inner2_1)}),
                'data: ' + json.dumps({"type": "Content", "event_type": "data", "content": json.dumps(inner3)}),
                'data: end'
        ]               
        new_response = '\r\n\n'.join(events) + '\r\n\n'
                        
        flow.response.headers["Content-Type"] = "text/event-stream"
        flow.response.headers["Transfer-Encoding"] = "chunked"
        flow.response.headers["Connection"] = "keep-alive"
        flow.response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        flow.response.headers["Cache-Control"] = "no-cache"
        flow.response.headers["X-Amz-Cf-Pop"] = "LUM1-P1"
         
        log_to_file(f"new_response: {new_response}")
        
        if "Content-Length" in flow.response.headers:
            del flow.response.headers["Content-Length"]
            
        log_to_file(f"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
                    
        flow.response.content = new_response.encode('utf-8')
            
    
            
def request(flow: http.HTTPFlow):
    log_to_file(f"Request: {flow.request}")
    
    # ENABLE_REWRITE = False
    if ENABLE_REWRITE is True and flow.request.pretty_url == "https://api.jetbrains.ai/user/v5/task/stream/v4/code-complete-mellum":        
        log_to_file("*** Intercepted request to code-complete-mellum")
        
        if flow.request.content:
            try:
                data = json.loads(flow.request.content)
                dump = json.dumps(data, indent=4)
                log_to_file(f"Original data (prettied): {dump}")
                
                # TODO if available, use multilineAllowed=true

                prefix = data["parameters"]["prefix"]
                suffix = data["parameters"]["suffix"]
                language = data["parameters"]["language"]
                filepath = data["parameters"]["filepath"] #.split("/")[-1]
                                         
                fim_context = ""
                
                for entry in data.get("parameters", {}).get("context", []):
                    # note: contextual files have a type of Nearby
                    ctx_type = entry.get("type", "").split("/")[-1]
                    ctx_filename = entry.get("filepath", "") #.split("/")[-1]
                    ctx_content = entry.get("content", "")
                    log_to_file(f"Context entry: {ctx_type} {language} - {ctx_filename} - {ctx_content[:10]}...")                    
                    fim_context += f"<filename>{ctx_filename}\n{ctx_content}\n"
                    log_to_file(f"fim_context: {fim_context}")
                
                # per documentation: https://huggingface.co/JetBrains/Mellum-4b-base#fill-in-the-middle-with-additional-files-as-context-generation
                # append the user context <filename>foo.py\nBODY<filename>current.py\n<fim_suffix>....<fim_prefix>xxx<fim_middle>
                # TODO FIXME ask JB : contrary to doc, seems like setting more than one <filename> does not work ?
                fim_context = "<filename>utils.py\ndef multiply(x, y):return x*y\n" + fim_context  # Add utils.py as context                        
                user_content = (
                    # fim_context +
                    f"<filename>{filepath}\n"
                    f"<fim_suffix>{suffix}<fim_prefix>{prefix}<fim_middle>"
                )                                    

                xuser_content = (                    
                    # "<filename>"+ filepath + "\n" + "<fim_suffix>"+suffix+"<fim_prefix>"+ prefix + "<fim_middle>"
                    # fim_context + "<filename>"+ filepath + "\n" + "<fim_suffix>"+suffix+"<fim_prefix>"+ prefix + "<fim_middle>"
                )

                newData = {
                    "model": "JetBrains/Mellum-4b-base",
                    "messages": [
                        {
                            "role": "user",
                            "content": user_content
                        }
                    ],
                    "max_tokens": 16384,
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "stream": False
                }
                
                flow.request.url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/v1/chat/completions"
                flow.request.headers.update({
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                            "User-Agent": "Esquie/1.0 (https://www.expedition33.com/)",
                            "Host": OLLAMA_HOST,
                            "Referer": "http://localhost"
                        })
                log_to_file(f"Modified newData: {newData}")
                #time.sleep(2)
                assert flow.request.method == "POST", "Expected POST request"
                flow.request.content = json.dumps(newData).encode('utf-8')
            except json.JSONDecodeError as e:
                log_to_file(f"JSON decode error: {e}")
        
    

