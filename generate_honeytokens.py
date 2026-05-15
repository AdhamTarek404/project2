import os
import ollama

# Default Cowrie honeyfs path (change if needed)
HONEYFS_DIR = "/home/kali/cowrie/honeyfs"

def generate_lure(prompt):
    print(f"Generating lure based on prompt...")
    response = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}]
    )
    
    # Strip any markdown blocks from response
    text = response['message']['content'].strip()
    if text.startswith('```'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text
    return text.strip()

def write_lure(filepath, content):
    full_path = os.path.join(HONEYFS_DIR, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w') as f:
        f.write(content)
    print(f"✅ Generated Honeytoken: {full_path}")

def main():
    if not os.path.exists(HONEYFS_DIR):
        print(f"⚠️ Warning: {HONEYFS_DIR} does not exist. Files will be generated here locally instead.")
        global HONEYFS_DIR
        HONEYFS_DIR = "./honeyfs"
    
    print("🐝 Initializing Dynamic AI Honeytoken Generation...")

    # AWS Credentials
    aws_prompt = "Generate a highly realistic AWS credentials file (~/.aws/credentials) containing a default profile with an access key and secret key. Do not include any explanation or markdown, just the raw file contents."
    aws_content = generate_lure(aws_prompt)
    write_lure("root/.aws/credentials", aws_content)

    # SSH Private Key
    ssh_prompt = "Generate a highly realistic fake SSH RSA private key. Do not include any explanation or markdown, just the raw key format."
    ssh_content = generate_lure(ssh_prompt)
    write_lure("root/.ssh/id_rsa", ssh_content)

    # WordPress Config
    wp_prompt = "Generate a realistic wp-config.php file containing dummy MySQL database credentials (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST). Do not include any explanation or markdown, just the raw PHP code."
    wp_content = generate_lure(wp_prompt)
    write_lure("var/www/html/wp-config.php", wp_content)

    print("\n🍯 Seed complete! When attackers cat or download these files, NeuralTrap will flag them.")

if __name__ == "__main__":
    main()
