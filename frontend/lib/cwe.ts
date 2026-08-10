const CWE_MAPPING: Record<string, [string, string]> = {
  "sql injection": ["CWE-89", "https://cwe.mitre.org/data/definitions/89.html"],
  sqli: ["CWE-89", "https://cwe.mitre.org/data/definitions/89.html"],
  "sql query construction": ["CWE-89", "https://cwe.mitre.org/data/definitions/89.html"],
  "parameterized quer": ["CWE-89", "https://cwe.mitre.org/data/definitions/89.html"],
  xss: ["CWE-79", "https://cwe.mitre.org/data/definitions/79.html"],
  "cross-site scripting": ["CWE-79", "https://cwe.mitre.org/data/definitions/79.html"],
  "cross site scripting": ["CWE-79", "https://cwe.mitre.org/data/definitions/79.html"],
  "html injection": ["CWE-79", "https://cwe.mitre.org/data/definitions/79.html"],
  "html escaping": ["CWE-79", "https://cwe.mitre.org/data/definitions/79.html"],
  "command injection": ["CWE-78", "https://cwe.mitre.org/data/definitions/78.html"],
  shell: ["CWE-78", "https://cwe.mitre.org/data/definitions/78.html"],
  pickle: ["CWE-502", "https://cwe.mitre.org/data/definitions/502.html"],
  deserialization: ["CWE-502", "https://cwe.mitre.org/data/definitions/502.html"],
  "path traversal": ["CWE-22", "https://cwe.mitre.org/data/definitions/22.html"],
  "hardcoded credential": ["CWE-798", "https://cwe.mitre.org/data/definitions/798.html"],
  "hardcoded password": ["CWE-259", "https://cwe.mitre.org/data/definitions/259.html"],
  csrf: ["CWE-352", "https://cwe.mitre.org/data/definitions/352.html"],
  "buffer overflow": ["CWE-120", "https://cwe.mitre.org/data/definitions/120.html"],
  "race condition": ["CWE-362", "https://cwe.mitre.org/data/definitions/362.html"],
  "null pointer": ["CWE-476", "https://cwe.mitre.org/data/definitions/476.html"],
  "division by zero": ["CWE-369", "https://cwe.mitre.org/data/definitions/369.html"],
  "open redirect": ["CWE-601", "https://cwe.mitre.org/data/definitions/601.html"],
  "weak cryptography": ["CWE-327", "https://cwe.mitre.org/data/definitions/327.html"],
  "insecure random": ["CWE-330", "https://cwe.mitre.org/data/definitions/330.html"],
  eval: ["CWE-95", "https://cwe.mitre.org/data/definitions/95.html"],
  exec: ["CWE-95", "https://cwe.mitre.org/data/definitions/95.html"],
};

export function classifyCwe(comment: string): [string, string] | null {
  const lower = comment.toLowerCase();
  for (const [keyword, value] of Object.entries(CWE_MAPPING)) {
    if (lower.includes(keyword)) return value;
  }
  return null;
}