import pytest
import json
import sys
from unittest.mock import patch, MagicMock

# ==========================================
# 1. Mock GenLayer Environment for Local Testing
# ==========================================
mock_gl = MagicMock()
mock_gl.message.sender_address = "0xTestAddress123"

# Mock strict_eq to bypass consensus and just execute the function
def mock_strict_eq(func):
    return func()
mock_gl.eq_principle.strict_eq = mock_strict_eq

# Mock GenVM storage types
class MockDynArray(list):
    pass

class MockTreeMap(dict):
    pass

def mock_u256(val):
    return int(val)

# Inject mocks into sys.modules before importing the contract
mock_genlayer = MagicMock()
mock_genlayer.gl = mock_gl
mock_genlayer.DynArray = MockDynArray
mock_genlayer.TreeMap = MockTreeMap
mock_genlayer.u256 = mock_u256
mock_genlayer.Address = str
mock_genlayer.allow_storage = lambda x: x
mock_genlayer.Contract = object

sys.modules['genlayer'] = mock_genlayer

# ==========================================
# 2. Import Contract & Setup Fixtures
# ==========================================
from NeuralPulseOracle import NeuralPulseOracle

@pytest.fixture
def oracle():
    contract = NeuralPulseOracle()
    # Manually initialize storage structures for local Python testing 
    # (GenVM does this automatically on-chain)
    contract.insights = MockDynArray()
    contract.latest_insight_id = MockTreeMap()
    return contract

# ==========================================
# 3. Test Cases
# ==========================================

@patch('NeuralPulseOracle.gl.nondet.exec_prompt')
def test_publish_insight_success(mock_exec_prompt, oracle):
    """Test successful publication of an insight with clear LLM response."""
    mock_exec_prompt.return_value = '{"trend": "bullish", "certitude": "high"}'
    
    oracle.publish_insight("BTC", "Bitcoin breaking all-time highs.")
    
    assert oracle.get_total_insights() == 1
    
    insight = oracle.get_latest_insight("BTC")
    assert insight["ticker"] == "BTC"
    assert insight["trend"] == "bullish"
    assert insight["certitude"] == "high"
    assert insight["state"] == "active"
    assert insight["author"] == "0xTestAddress123"

@patch('NeuralPulseOracle.gl.nondet.exec_prompt')
def test_publish_insight_hallucination_fallback(mock_exec_prompt, oracle):
    """Test the robust JSON extraction when LLM returns markdown and invalid enums."""
    # LLM hallucinates markdown wrappers and an invalid trend ("moon")
    mock_exec_prompt.return_value = 'Here is your sentiment: ```json\n{"trend": "moon", "certitude": "low"}\n```'
    
    oracle.publish_insight("DOGE", "To the moon!")
    
    insight = oracle.get_latest_insight("DOGE")
    
    # Contract should fallback invalid "moon" to "neutral" securely
    assert insight["trend"] == "neutral"
    assert insight["certitude"] == "low"

@patch('NeuralPulseOracle.gl.nondet.exec_prompt')
def test_challenge_insight_overturned(mock_exec_prompt, oracle):
    """Test challenging an insight where the AI changes its decision."""
    # 1. Publish initial insight
    mock_exec_prompt.return_value = '{"trend": "bullish", "certitude": "medium"}'
    oracle.publish_insight("SOL", "Fast transactions today.")
    
    # 2. Challenge the insight
    # LLM agrees with challenger and changes trend to bearish
    mock_exec_prompt.return_value = '{"trend": "bearish", "certitude": "high"}'
    oracle.challenge_insight(0, "Network just experienced an outage.")
    
    insight = oracle.get_insight(0)
    
    assert insight["state"] == "overturned"
    assert insight["trend"] == "bearish"
    assert insight["challenge_reason"] == "Network just experienced an outage."
    assert insight["initial_trend"] == "bullish"

@patch('NeuralPulseOracle.gl.nondet.exec_prompt')
def test_challenge_insight_upheld(mock_exec_prompt, oracle):
    """Test challenging an insight where the AI rejects the challenge."""
    mock_exec_prompt.return_value = '{"trend": "bullish", "certitude": "high"}'
    oracle.publish_insight("ETH", "Strong fundamentals.")
    
    # LLM keeps the trend as bullish despite the challenge
    mock_exec_prompt.return_value = '{"trend": "bullish", "certitude": "low"}'
    oracle.challenge_insight(0, "Gas fees are slightly up.")
    
    insight = oracle.get_insight(0)
    
    assert insight["state"] == "upheld"
    assert insight["trend"] == "bullish"
    
def test_get_nonexistent_insight(oracle):
    """Test fetching an insight that hasn't been published yet."""
    insight = oracle.get_latest_insight("UNKNOWN")
    assert insight["trend"] == "none"
    assert insight["state"] == "none"

def test_challenge_invalid_id(oracle):
    """Test that challenging an out-of-bounds ID raises an exception."""
    with pytest.raises(Exception, match="Insight ID is out of range"):
        oracle.challenge_insight(999, "Fake rationale")
