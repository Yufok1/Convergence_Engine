"""
🔬 Tests for the Illumination Engine - Deep Causal Intelligence

Tests the new causation analysis features:
- Root cause analysis
- Impact analysis
- Event explanations
- Advanced search
- Most consequential events
- Timeline views
"""

import pytest
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from causation_explorer import CausationExplorer, Event


class TestIlluminationEngine:
    """Test the new Illumination Engine features"""
    
    @pytest.fixture
    def explorer_with_chain(self):
        """Create an explorer with a causation chain for testing"""
        explorer = CausationExplorer()
        
        # Create a chain of events: A -> B -> C -> D
        # This simulates: network change -> VP spike -> phase transition -> collapse
        
        base_time = time.time()
        
        event_a = Event(
            timestamp=base_time,
            component='reality_sim',
            event_type='state_change',
            data={'organism_count': 100, 'modularity': 0.8}
        )
        explorer.add_event(event_a)
        
        event_b = Event(
            timestamp=base_time + 0.5,
            component='djinn_kernel',
            event_type='threshold_crossed',
            data={'violation_pressure': 0.8, 'vp_classification': 'VP2'}
        )
        explorer.add_event(event_b)
        
        event_c = Event(
            timestamp=base_time + 1.0,
            component='explorer',
            event_type='phase_transition',
            data={'from_phase': 'exploration', 'to_phase': 'convergence'}
        )
        explorer.add_event(event_c)
        
        event_d = Event(
            timestamp=base_time + 1.5,
            component='reality_sim',
            event_type='collapse',
            data={'is_collapsed': True, 'modularity': 0.1}
        )
        explorer.add_event(event_d)
        
        return explorer, [event_a, event_b, event_c, event_d]
    
    def test_find_root_causes_exists(self, explorer_with_chain):
        """Test that find_root_causes method exists and returns proper structure"""
        explorer, events = explorer_with_chain
        
        # Find root causes for the last event (collapse)
        result = explorer.find_root_causes(events[-1].event_id)
        
        assert 'event' in result
        assert 'root_causes' in result
        assert 'total_roots_found' in result
        assert 'analysis_depth' in result
        
    def test_analyze_impact_exists(self, explorer_with_chain):
        """Test that analyze_impact method exists and returns proper structure"""
        explorer, events = explorer_with_chain
        
        # Analyze impact of the first event
        result = explorer.analyze_impact(events[0].event_id)
        
        assert 'source_event' in result
        assert 'total_affected_events' in result
        assert 'affected_by_component' in result
        assert 'leaf_effects' in result
        
    def test_explain_event_exists(self, explorer_with_chain):
        """Test that explain_event method exists and returns proper structure"""
        explorer, events = explorer_with_chain
        
        # Get explanation for middle event
        result = explorer.explain_event(events[1].event_id)
        
        assert 'event' in result
        assert 'summary' in result
        assert 'immediate_causes' in result
        assert 'immediate_effects' in result
        assert 'severity' in result
        
    def test_search_advanced_exists(self, explorer_with_chain):
        """Test that search_advanced method exists and returns proper structure"""
        explorer, events = explorer_with_chain
        
        # Search with various filters
        result = explorer.search_advanced(
            component='reality_sim',
            limit=10
        )
        
        assert 'results' in result
        assert 'total_matches' in result
        assert 'aggregations' in result
        assert 'filters_applied' in result
        
    def test_search_advanced_filters_work(self, explorer_with_chain):
        """Test that advanced search filters actually filter"""
        explorer, events = explorer_with_chain
        
        # Search for reality_sim events only
        result = explorer.search_advanced(component='reality_sim')
        
        for r in result['results']:
            assert r['event']['component'] == 'reality_sim'
            
    def test_get_most_consequential_exists(self, explorer_with_chain):
        """Test that get_most_consequential method exists and returns proper structure"""
        explorer, events = explorer_with_chain
        
        result = explorer.get_most_consequential(limit=5)
        
        assert isinstance(result, list)
        if result:
            assert 'event' in result[0]
            assert 'downstream_effects' in result[0]
            assert 'impact_score' in result[0]
            
    def test_get_timeline_exists(self, explorer_with_chain):
        """Test that get_timeline method exists and returns proper structure"""
        explorer, events = explorer_with_chain
        
        result = explorer.get_timeline()
        
        assert 'events' in result
        assert 'links' in result
        assert 'time_range' in result
        assert 'total_events' in result
        
    def test_severity_calculation(self, explorer_with_chain):
        """Test that severity calculation works for different event types"""
        explorer, events = explorer_with_chain
        
        # Collapse event should have high severity
        collapse_event = events[-1]  # The collapse event
        severity = explorer._calculate_severity(collapse_event)
        
        assert severity >= 0.7, "Collapse events should have high severity"
        
        # Normal state change should have lower severity
        normal_event = events[0]
        severity = explorer._calculate_severity(normal_event)
        
        assert severity <= 0.6, "Normal state changes should have lower severity"
        
    def test_metric_deltas_calculation(self, explorer_with_chain):
        """Test that metric delta calculation works"""
        explorer, events = explorer_with_chain
        
        # Calculate deltas between first and last event
        deltas = explorer._calculate_metric_deltas(events[0], events[-1])
        
        # Should detect modularity change (0.8 -> 0.1)
        assert 'modularity' in deltas
        assert deltas['modularity']['direction'] == '↓'
        assert deltas['modularity']['delta'] < 0


class TestWebAPIRoutes:
    """Test that the new API routes are registered"""
    
    def test_routes_registered(self):
        """Test that all new routes are registered in Flask app"""
        from causation_web_ui import app
        
        routes = [r.rule for r in app.url_map.iter_rules()]
        
        # Check new routes exist
        assert '/api/events/<event_id>/root-causes' in routes
        assert '/api/events/<event_id>/impact' in routes
        assert '/api/events/<event_id>/explain' in routes
        assert '/api/events/search/advanced' in routes
        assert '/api/events/consequential' in routes
        assert '/api/timeline' in routes


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
