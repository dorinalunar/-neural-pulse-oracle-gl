# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

import json
from dataclasses import dataclass

VALID_TRENDS = ("bullish", "bearish", "neutral")
VALID_CERTITUDE = ("low", "medium", "high")


@allow_storage
@dataclass
class MarketInsight:
    ticker: str
    trend: str
    certitude: str
    author: Address
    raw_text: str
    state: str
    challenge_reason: str
    initial_trend: str
    initial_certitude: str


class NeuralPulseOracle(gl.Contract):
    insights: DynArray[MarketInsight]
    latest_insight_id: TreeMap[str, u256]
    total_insights: u256

    def __init__(self):
        # DynArray and TreeMap are initialized automatically by GenVM
        self.total_insights = u256(0)

    def _evaluate_market_vibe(self, ticker_key: str, text: str) -> dict:
        prompt = f"""
You are an expert crypto analyst assessing market sentiment.
Analyze the text provided below and determine its sentiment specifically regarding the asset "{ticker_key}".

Text to analyze:
\"\"\"{text}\"\"\"

Output ONLY a JSON object in this exact format, with no additional text, markdown, or commentary:
{{
  "trend": "bullish",
  "certitude": "high"
}}
"""
        def nondet_eval():
            res = gl.nondet.exec_prompt(prompt)
            
            try:
                if not res or not isinstance(res, str):
                    raise ValueError("Empty or invalid LLM response")

                # Extract JSON even if there is extra text or markdown
                start_idx = res.find('{')
                end_idx = res.rfind('}')
                
                if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
                    clean_res = res[start_idx:end_idx + 1]
                else:
                    clean_res = res
                
                data = json.loads(clean_res)
                trend_val = str(data.get("trend", "neutral")).strip().lower()
                certitude_val = str(data.get("certitude", "low")).strip().lower()

                if trend_val not in VALID_TRENDS:
                    trend_val = "neutral"
                if certitude_val not in VALID_CERTITUDE:
                    certitude_val = "low"

                return json.dumps({"trend": trend_val, "certitude": certitude_val})
            
            except Exception:
                # Safe default fallback in case of model error
                return json.dumps({"trend": "neutral", "certitude": "low"})

        raw_result = gl.eq_principle.strict_eq(nondet_eval)
        return json.loads(raw_result)

    @gl.public.write
    def publish_insight(self, ticker: str, text: str) -> None:
        tkr = ticker.strip().upper()
        if not tkr:
            raise Exception("Ticker symbol cannot be empty")
        if not text.strip():
            raise Exception("Analysis text cannot be empty")

        ai_result = self._evaluate_market_vibe(tkr, text)

        new_insight = MarketInsight(
            ticker=tkr,
            trend=ai_result["trend"],
            certitude=ai_result["certitude"],
            author=gl.message.sender_address,
            raw_text=text,
            state="active",
            challenge_reason="",
            initial_trend=ai_result["trend"],
            initial_certitude=ai_result["certitude"]
        )
        
        self.insights.append(new_insight)
        self.latest_insight_id[tkr] = self.total_insights
        self.total_insights += u256(1)

    @gl.public.write
    def challenge_insight(self, insight_id: int, rationale: str) -> None:
        if insight_id < 0 or insight_id >= int(self.total_insights):
            raise Exception("Insight ID is out of range")
        if not rationale.strip():
            raise Exception("Challenge rationale cannot be empty")

        target = self.insights[insight_id]
        if target.state != "active":
            raise Exception("Only an active insight can be challenged")

        context_prompt = (
            f"Original text regarding {target.ticker}: {target.raw_text}\n\n"
            f"A reviewer challenges this assessment with the following argument:\n{rationale}\n\n"
            f"Based ONLY on how the original text impacts {target.ticker}, re-evaluate the sentiment. "
            f"Determine if the reviewer's argument proves a misinterpretation in the original text."
        )
        
        new_eval = self._evaluate_market_vibe(target.ticker, context_prompt)

        updated_insight = MarketInsight(
            ticker=target.ticker,
            trend=new_eval["trend"],
            certitude=new_eval["certitude"],
            author=target.author,
            raw_text=target.raw_text,
            state="upheld" if new_eval["trend"] == target.trend else "overturned",
            challenge_reason=rationale,
            initial_trend=target.initial_trend,
            initial_certitude=target.initial_certitude
        )
        
        self.insights[insight_id] = updated_insight

    @gl.public.view
    def get_latest_insight(self, ticker: str) -> dict:
        tkr = ticker.strip().upper()
        if tkr not in self.latest_insight_id:
            return {"ticker": tkr, "trend": "none", "certitude": "none", "state": "none"}
        idx = self.latest_insight_id[tkr]
        return self._serialize(self.insights[int(idx)])

    @gl.public.view
    def get_insight(self, insight_id: int) -> dict:
        if insight_id < 0 or insight_id >= int(self.total_insights):
            raise Exception("Insight ID is out of range")
        return self._serialize(self.insights[insight_id])

    @gl.public.view
    def get_total_insights(self) -> int:
        return int(self.total_insights)

    def _serialize(self, record: MarketInsight) -> dict:
        return {
            "ticker": record.ticker,
            "trend": record.trend,
            "certitude": record.certitude,
            "author": str(record.author),
            "raw_text": record.raw_text,
            "state": record.state,
            "challenge_reason": record.challenge_reason,
            "initial_trend": record.initial_trend,
            "initial_certitude": record.initial_certitude
        }