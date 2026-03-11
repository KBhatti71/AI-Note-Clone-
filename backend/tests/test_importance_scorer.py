import pytest
from app.analyzers.importance_scorer import ImportanceScorer, TranscriptSegment, Context

@pytest.fixture
def base_prosody():
    return {
        'vocal_emphasis_score': 50,
        'speaking_rate': 4.0
    }

def test_initialization():
    scorer = ImportanceScorer(context=Context.SCHOOL)
    assert scorer.context == Context.SCHOOL

def test_score_critical_keywords(base_prosody):
    scorer = ImportanceScorer(context=Context.SCHOOL)
    
    # "Exam" is a critical keyword in SCHOOL context (20 points)
    segment = TranscriptSegment(text="Remember this is for the midterm exam.", start_time=0.0, end_time=2.0)
    
    result = scorer.score_segment(segment, base_prosody)
    breakdown = result['breakdown']
    
    assert breakdown['keywords'] >= 20
    assert result['score'] > 0
    
def test_user_highlight_boost(base_prosody):
    scorer = ImportanceScorer()
    
    segment = TranscriptSegment(text="Normal sentence.", start_time=0.0, end_time=2.0)
    
    # False highlight
    result1 = scorer.score_segment(segment, base_prosody, user_highlighted=False)
    
    # True highlight
    result2 = scorer.score_segment(segment, base_prosody, user_highlighted=True)
    
    assert 'user_highlight' in result2['breakdown']
    assert result2['breakdown']['user_highlight'] == 15
    assert result2['score'] > result1['score']

def test_repetition_scoring(base_prosody):
    scorer = ImportanceScorer()
    
    window = [
        TranscriptSegment(text="We need to focus on performance.", start_time=0.0, end_time=1.0),
        TranscriptSegment(text="Performance is the key issue here.", start_time=5.0, end_time=6.0)
    ]
    
    current = TranscriptSegment(text="Again, focus on performance.", start_time=10.0, end_time=12.0)
    
    result = scorer.score_segment(current, base_prosody, window_transcripts=window)
    
    assert result['breakdown']['repetition'] > 0
