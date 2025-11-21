"""
Mirror Systems for Explorer
Self-reflection and foresight capabilities
"""

import time
import math
from datetime import datetime

class MirrorOfInsight:
    """Analyzes current system state and patterns"""
    
    def __init__(self):
        self.insight_history = []
        self.pattern_memory = {}
        self.stability_history = []  # Track stability calculations
        
    def reflect(self, system_state):
        """Analyze current system state and extract insights"""
        insights = {
            'timestamp': time.time(),
            'phase': system_state.get('phase', 'unknown'),
            'breath_state': system_state.get('breath_state', {}),
            'kernel_sovereign_ids': system_state.get('kernel_sovereign_ids', []),
            'patterns': self._analyze_patterns(system_state),
            'stability_assessment': self._assess_stability(system_state),
            'growth_indicators': self._assess_growth(system_state)
        }
        
        self.insight_history.append(insights)
        
        # Track stability for mathematical understanding
        stability_score = insights['stability_assessment']['score']
        self.stability_history.append({
            'score': stability_score,
            'timestamp': insights['timestamp'],
            'level': insights['stability_assessment']['level']
        })
        
        return insights
    
    def _analyze_patterns(self, state):
        """Analyze patterns in system behavior"""
        patterns = {
            'breath_rhythm': 'stable' if state.get('breath_state', {}).get('cycle_count', 0) > 0 else 'forming',
            'function_growth': len(state.get('kernel_sovereign_ids', [])),
            'phase_consistency': 'consistent' if state.get('phase') in ['genesis', 'sovereign'] else 'unstable'
        }
        return patterns
    
    def _assess_stability(self, state):
        """Assess system stability"""
        breath_state = state.get('breath_state', {})
        stability_score = 0.0
        
        # Breath stability
        if breath_state.get('cycle_count', 0) > 5:
            stability_score += 0.4
            
        # Function stability
        if len(state.get('kernel_sovereign_ids', [])) > 0:
            stability_score += 0.3
            
        # Phase stability
        if state.get('phase') in ['genesis', 'sovereign']:
            stability_score += 0.3
            
        return {
            'score': stability_score,
            'level': 'stable' if stability_score > 0.7 else 'forming' if stability_score > 0.3 else 'unstable'
        }
    
    def _assess_growth(self, state):
        """Assess system growth indicators"""
        growth = {
            'function_count': len(state.get('kernel_sovereign_ids', [])),
            'breath_cycles': state.get('breath_state', {}).get('cycle_count', 0),
            'phase_progression': 'advancing' if state.get('phase') == 'sovereign' else 'developing'
        }
        return growth
    
    def get_stability_score(self):
        """Get current stability score for mathematical assessment"""
        if self.stability_history:
            return self.stability_history[-1]['score']
        return 0.0
    
    def get_stability_variance(self):
        """Calculate stability variance for mathematical understanding"""
        if len(self.stability_history) < 2:
            return float('inf')
        scores = [entry['score'] for entry in self.stability_history]
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        return variance

class MirrorOfPortent:
    """Forecasts potential outcomes and warns of future consequences"""
    
    def __init__(self):
        self.forecast_history = []
        self.warning_thresholds = {
            'stability_drop': 0.3,
            'function_loss': 0.5,
            'breath_irregularity': 0.4
        }
        
    def foresee(self, current_state, insight_data):
        """Forecast potential outcomes based on current state"""
        forecast = {
            'timestamp': time.time(),
            'short_term': self._short_term_forecast(current_state, insight_data),
            'medium_term': self._medium_term_forecast(current_state, insight_data),
            'warnings': self._generate_warnings(current_state, insight_data),
            'opportunities': self._identify_opportunities(current_state, insight_data)
        }
        
        self.forecast_history.append(forecast)
        return forecast
    
    def _short_term_forecast(self, state, insight):
        """Forecast next few cycles"""
        breath_state = state.get('breath_state', {})
        patterns = insight.get('patterns', {})
        
        forecast = {
            'next_breath_cycle': breath_state.get('cycle_count', 0) + 1,
            'stability_trend': 'improving' if insight.get('stability_assessment', {}).get('score', 0) > 0.5 else 'declining',
            'function_growth_likelihood': 'high' if patterns.get('function_growth', 0) > 0 else 'low'
        }
        return forecast
    
    def _medium_term_forecast(self, state, insight):
        """Forecast medium-term outcomes"""
        stability = insight.get('stability_assessment', {})
        growth = insight.get('growth_indicators', {})
        
        forecast = {
            'phase_transition_likelihood': 'high' if stability.get('score', 0) > 0.8 else 'medium',
            'function_expansion': 'expected' if growth.get('function_count', 0) > 0 else 'uncertain',
            'system_maturity': 'approaching' if stability.get('score', 0) > 0.7 else 'distant'
        }
        return forecast
    
    def _generate_warnings(self, state, insight):
        """Generate warnings about potential issues"""
        warnings = []
        stability = insight.get('stability_assessment', {})
        
        if stability.get('score', 0) < self.warning_thresholds['stability_drop']:
            warnings.append({
                'type': 'stability_warning',
                'severity': 'high',
                'message': 'System stability below threshold - intervention may be needed'
            })
            
        if len(state.get('kernel_sovereign_ids', [])) == 0:
            warnings.append({
                'type': 'function_warning',
                'severity': 'medium',
                'message': 'No certified functions - system may be in critical state'
            })
            
        return warnings
    
    def _identify_opportunities(self, state, insight):
        """Identify growth and improvement opportunities"""
        opportunities = []
        growth = insight.get('growth_indicators', {})
        
        if growth.get('function_count', 0) == 0:
            opportunities.append({
                'type': 'function_certification',
                'priority': 'high',
                'description': 'Opportunity to certify first functions'
            })
            
        if insight.get('stability_assessment', {}).get('score', 0) > 0.6:
            opportunities.append({
                'type': 'phase_advancement',
                'priority': 'medium',
                'description': 'System ready for phase transition'
            })
            
        return opportunities

class BloomSystem:
    """Natural unfolding and growth patterns"""
    
    def __init__(self):
        self.bloom_curvature = 0.0
        self.phase_bloom = 0.0
        self.reflection_index = 0.0
        self.bloom_history = []
        self.bloom_cycles = 0
        self.last_bloom_resonance = 0.0
        
    def calculate_bloom_metrics(self, insight_data, forecast_data, breath_state=None):
        """Calculate bloom system metrics with breath integration"""
        stability = insight_data.get('stability_assessment', {}).get('score', 0)
        growth = insight_data.get('growth_indicators', {})
        
        # Bloom curvature - how naturally the system is unfolding
        # Use log scale to prevent explosion with large function counts
        function_count = growth.get('function_count', 0)
        if function_count > 0:
            # Use log scale: log(1 + function_count) to prevent explosion
            import math
            log_function_count = math.log(1 + function_count)
            self.bloom_curvature = stability * log_function_count * 0.1
        else:
            self.bloom_curvature = 0.0
        
        # Phase bloom - resonance with current phase
        if insight_data.get('phase') == 'sovereign':
            self.phase_bloom = min(1.0, stability * 1.5)
        else:
            self.phase_bloom = stability * 0.8
            
        # Reflection index - self-awareness level
        self.reflection_index = min(1.0, (len(insight_data.get('patterns', {})) + 
                                         len(forecast_data.get('warnings', [])) + 
                                         len(forecast_data.get('opportunities', []))) / 10.0)
        
        # Breath resonance - how well the system breathes with natural patterns
        breath_resonance = 0.0
        if breath_state:
            breath_cycles = breath_state.get('cycle_count', 0)
            breath_depth = breath_state.get('depth', 0.5)
            breath_resonance = min(1.0, (breath_cycles * 0.1) + (breath_depth * 0.5))
            self.last_bloom_resonance = breath_resonance
            
        # Natural unfolding assessment
        natural_unfolding = 'low'
        if self.bloom_curvature > 0.5 and breath_resonance > 0.7:
            natural_unfolding = 'high'
        elif self.bloom_curvature > 0.2 or breath_resonance > 0.4:
            natural_unfolding = 'medium'
            
        # Update bloom history
        bloom_data = {
            'timestamp': time.time(),
            'bloom_curvature': self.bloom_curvature,
            'phase_bloom': self.phase_bloom,
            'reflection_index': self.reflection_index,
            'breath_resonance': breath_resonance,
            'natural_unfolding': natural_unfolding
        }
        self.bloom_history.append(bloom_data)
        self.bloom_cycles += 1
        
        return {
            'bloom_curvature': self.bloom_curvature,
            'phase_bloom': self.phase_bloom,
            'reflection_index': self.reflection_index,
            'breath_resonance': breath_resonance,
            'natural_unfolding': natural_unfolding,
            'bloom_cycles': self.bloom_cycles,
            'bloom_maturity': self._assess_bloom_maturity()
        }
        
    def _assess_bloom_maturity(self):
        """Assess the maturity of the bloom system"""
        if self.bloom_cycles < 5:
            return 'seedling'
        elif self.bloom_cycles < 15:
            return 'growing'
        elif self.bloom_cycles < 30:
            return 'flowering'
        else:
            return 'mature'
            
    def get_bloom_pulse(self):
        """Get the current bloom pulse for timing adjustments"""
        return (self.bloom_curvature + self.phase_bloom + self.reflection_index) / 3.0
        
    def should_trigger_bloom_event(self):
        """Determine if a bloom event should be triggered"""
        return (self.bloom_curvature > 0.6 and 
                self.phase_bloom > 0.7 and 
                self.reflection_index > 0.5)
