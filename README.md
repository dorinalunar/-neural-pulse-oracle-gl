# Neural Pulse Oracle 🧠📈

![GenLayer](https://img.shields.io/badge/GenLayer-Smart%20Contract-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**Neural Pulse Oracle** is an Intelligent Smart Contract built for the **GenLayer** network. It leverages the power of GenVM and Large Language Models (LLMs) to analyze cryptocurrency market sentiment directly on-chain. By evaluating raw text inputs, the oracle determines market vibes (bullish, bearish, or neutral) and securely stores these insights using a deterministic consensus mechanism.

## 🌟 Key Features

* **AI-Driven Sentiment Analysis:** Automatically evaluates complex text analysis to categorize the sentiment regarding specific crypto assets.
* **Deterministic LLM Consensus:** Utilizes GenLayer's `strict_eq` principle to ensure that all network validators reach an absolute agreement on non-deterministic LLM outputs before altering the state.
* **On-Chain Dispute Resolution:** A built-in challenge system allows the community to dispute an active insight by providing a rationale, triggering an AI re-evaluation.
* **Robust JSON Extraction:** Custom parsing safeguards ensure the contract extracts valid JSON formats, effectively mitigating issues caused by LLM hallucinations or unexpected markdown wrappers.

---

## 🔍 Smart Contract Highlights

### 1. Bulletproof JSON Extraction
The contract securely isolates non-deterministic LLM execution. It features a custom parsing mechanism to extract valid JSON even if the model hallucinates markdown tags or conversational text.

```python
def nondet_eval():
    res = gl.nondet.exec_prompt(prompt)
    
    try:
        if not res or not isinstance(res, str):
            raise ValueError("Empty or invalid LLM response")

        # Extract JSON even if there is extra text
        start_idx = res.find('{')
        end_idx = res.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
            clean_res = res[start_idx:end_idx + 1]
        else:
            clean_res = res
            
        # Parse and sanitize data...
```

### 2. Strict Consensus Verification
State changes are exclusively gated by validator consensus. The non-deterministic function is passed through `strict_eq`, ensuring that the blockchain state only updates when nodes perfectly agree on the extracted JSON string.

```python
        # Enforce consensus across validators before state mutation
        raw_result = gl.eq_principle.strict_eq(nondet_eval)
        return json.loads(raw_result)
```

### 3. AI-Powered Dispute Resolution
Users can challenge existing insights. The contract dynamically constructs a new prompt combining the original text and the challenger's rationale, allowing the LLM to act as an impartial judge.

```python
        context_prompt = (
            f"Original text regarding {target.ticker}: {target.raw_text}\n\n"
            f"A reviewer challenges this assessment with the following argument:\n{rationale}\n\n"
            f"Based ONLY on how the original text impacts {target.ticker}, re-evaluate the sentiment. "
            f"Determine if the reviewer's argument proves a misinterpretation in the original text."
        )
        
        new_eval = self._evaluate_market_vibe(target.ticker, context_prompt)
```

---

## 📖 API Reference

### Write Methods
* `publish_insight(ticker: str, text: str)`: Submits a new market analysis for a specific ticker. Evaluates the text via LLM and stores the insight on-chain.
* `challenge_insight(insight_id: int, rationale: str)`: Challenges an existing, active insight. The LLM re-evaluates the original text against the provided rationale, potentially overturning the initial sentiment.

### View Methods
* `get_latest_insight(ticker: str) -> dict`: Returns the most recently published insight for a given ticker symbol.
* `get_insight(insight_id: int) -> dict`: Returns the full data of a specific insight by its ID.
* `get_total_insights() -> int`: Returns the total number of insights processed by the contract.

---

## 🛠 Installation & Deployment

1. Clone this repository:
   ```bash
   git clone [https://github.com/dorinalunar/-neural-pulse-oracle-gl.git](https://github.com/dorinalunar/-neural-pulse-oracle-gl.git)
   ```
2. Open the [GenLayer Simulator](https://simulator.genlayer.com/) or your preferred GenVM deployment environment.
3. Paste the contents of `NeuralPulseOracle.py`.
4. Deploy the contract and start interacting with the AI-driven endpoints.

[![Run Tests](https://github.com/dorinalunar/-neural-pulse-oracle-gl/actions/workflows/tests.yml/badge.svg)](https://github.com/dorinalunar/-neural-pulse-oracle-gl/actions)

## 📄 License
This project is licensed under the MIT License.
