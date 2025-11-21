"""
Dynamic Operations for Explorer
Intelligent, adaptive, learning operations that prevent infinite loops
"""

import time
import random
import math
from datetime import datetime

class DynamicOperations:
    """Generates intelligent, adaptive operations based on system state"""
    
    def __init__(self):
        self.operation_history = []
        self.learning_memory = {}
        self.defunct_sovereign_ids = set()
        self.success_patterns = {}
        self.failure_patterns = {}
        self.operation_templates = self._initialize_templates()
        
    def _initialize_templates(self):
        """Initialize operation templates for different scenarios"""
        return {
            'resource_optimization': {
                'base_traits': {'execution_time_ms': 120.0, 'memory_kb': 3000, 'terminated': 1},
                'variation_range': {'execution_time_ms': (50, 200), 'memory_kb': (1000, 5000)},
                'success_criteria': {'execution_time_ms': 100, 'memory_kb': 2000}
            },
            'parallelism': {
                'base_traits': {'execution_time_ms': 80.0, 'memory_kb': 1024, 'terminated': 1},
                'variation_range': {'execution_time_ms': (30, 150), 'memory_kb': (500, 3000)},
                'success_criteria': {'execution_time_ms': 60, 'memory_kb': 1500}
            },
            'feature_expansion': {
                'base_traits': {'execution_time_ms': 200.0, 'memory_kb': 4000, 'terminated': 1},
                'variation_range': {'execution_time_ms': (100, 300), 'memory_kb': (2000, 6000)},
                'success_criteria': {'execution_time_ms': 150, 'memory_kb': 3000}
            },
            'load_balancing': {
                'base_traits': {'execution_time_ms': 150.0, 'memory_kb': 2500, 'terminated': 1},
                'variation_range': {'execution_time_ms': (80, 250), 'memory_kb': (1500, 4000)},
                'success_criteria': {'execution_time_ms': 120, 'memory_kb': 2000}
            },
            'fixed_point': {
                'base_traits': {'execution_time_ms': 100.0, 'memory_kb': 1800, 'terminated': 1},
                'variation_range': {'execution_time_ms': (50, 180), 'memory_kb': (1000, 3000)},
                'success_criteria': {'execution_time_ms': 80, 'memory_kb': 1500}
            }
        }
    
    def generate_operations(self, current_state, insight_data, forecast_data):
        """Generate intelligent operations based on current state and insights"""
        operations = []
        
        # Analyze current state
        stability = insight_data.get('stability_assessment', {}).get('score', 0)
        function_count = len(current_state.get('kernel_sovereign_ids', []))
        warnings = forecast_data.get('warnings', [])
        opportunities = forecast_data.get('opportunities', [])
        
        # Determine operation count based on system state
        base_count = 2
        if stability > 0.7:
            base_count = 3  # More operations when stable
        elif stability < 0.3:
            base_count = 1  # Fewer operations when unstable
            
        # Generate operations based on opportunities and warnings
        for opportunity in opportunities:
            if opportunity['type'] == 'function_certification':
                operations.extend(self._generate_certification_operations(base_count))
            elif opportunity['type'] == 'phase_advancement':
                operations.extend(self._generate_advancement_operations(base_count))
                
        # Generate operations based on warnings
        for warning in warnings:
            if warning['type'] == 'stability_warning':
                operations.extend(self._generate_stability_operations(base_count))
            elif warning['type'] == 'function_warning':
                operations.extend(self._generate_recovery_operations(base_count))
                
        # If no specific operations generated, create adaptive ones
        if not operations:
            operations = self._generate_adaptive_operations(base_count, current_state)
            
        # Apply learning and variation
        operations = self._apply_learning(operations, current_state)
        
        return operations
    
    def _generate_certification_operations(self, count):
        """Generate operations for function certification"""
        operations = []
        templates = list(self.operation_templates.keys())
        
        for i in range(count):
            template_name = random.choice(templates)
            template = self.operation_templates[template_name]
            
            # Create varied operation
            operation = self._create_varied_operation(template, f"certification_{i}")
            operations.append(operation)
            
        return operations
    
    def _generate_advancement_operations(self, count):
        """Generate operations for phase advancement"""
        operations = []
        
        for i in range(count):
            # Focus on high-performance operations
            template = self.operation_templates['parallelism']
            operation = self._create_varied_operation(template, f"advancement_{i}")
            operations.append(operation)
            
        return operations
    
    def _generate_stability_operations(self, count):
        """Generate operations for stability improvement"""
        operations = []
        
        for i in range(count):
            # Focus on reliable operations
            template = self.operation_templates['load_balancing']
            operation = self._create_varied_operation(template, f"stability_{i}")
            operations.append(operation)
            
        return operations
    
    def _generate_recovery_operations(self, count):
        """Generate operations for system recovery"""
        operations = []
        
        for i in range(count):
            # Focus on basic, reliable operations
            template = self.operation_templates['resource_optimization']
            operation = self._create_varied_operation(template, f"recovery_{i}")
            operations.append(operation)
            
        return operations
    
    def _generate_adaptive_operations(self, count, current_state):
        """Generate adaptive operations based on current state"""
        operations = []
        function_count = len(current_state.get('kernel_sovereign_ids', []))
        
        # Choose templates based on current function count
        if function_count == 0:
            templates = ['resource_optimization', 'feature_expansion']
        elif function_count < 3:
            templates = ['parallelism', 'load_balancing']
        else:
            templates = ['fixed_point', 'feature_expansion']
            
        for i in range(count):
            template_name = random.choice(templates)
            template = self.operation_templates[template_name]
            operation = self._create_varied_operation(template, f"adaptive_{i}")
            operations.append(operation)
            
        return operations
    
    def _create_varied_operation(self, template, operation_id):
        """Create a varied operation based on template"""
        traits = {}
        
        for trait, base_value in template['base_traits'].items():
            if trait in template['variation_range']:
                min_val, max_val = template['variation_range'][trait]
                # Add some randomness while staying within bounds
                variation = random.uniform(0.8, 1.2)
                traits[trait] = max(min_val, min(max_val, base_value * variation))
            else:
                traits[trait] = base_value
                
        # Generate sovereign hash-based identifier for dynamic operation
        from identity import sovereign_hash_id
        operation_traits = {
            'operation_id': operation_id,
            'traits': traits,
            'generation_time': time.time()
        }
        sovereign_id = f"hash-{sovereign_hash_id(operation_traits)}"
        
        return {
            'traits': traits,
            'sovereign_id': sovereign_id,  # Sovereign hash-based identifier
            'template': template,
            'generation_time': time.time()
        }
    
    def _apply_learning(self, operations, current_state):
        """Apply learning from previous operations"""
        for operation in operations:
            # Check if similar operations failed before
            operation_key = self._get_operation_key(operation)
            if operation_key in self.failure_patterns:
                # Adjust operation to avoid previous failures
                operation = self._adjust_for_failures(operation, self.failure_patterns[operation_key])
                
            # Apply success patterns
            if operation_key in self.success_patterns:
                operation = self._apply_success_patterns(operation, self.success_patterns[operation_key])
                
        return operations
    
    def _get_operation_key(self, operation):
        """Generate a key for operation pattern matching"""
        traits = operation['traits']
        return f"{traits.get('execution_time_ms', 0):.0f}_{traits.get('memory_kb', 0):.0f}"
    
    def _adjust_for_failures(self, operation, failure_data):
        """Adjust operation to avoid previous failures"""
        # Simple adjustment - reduce resource usage if previous failures
        if failure_data.get('count', 0) > 2:
            operation['traits']['execution_time_ms'] *= 0.8
            operation['traits']['memory_kb'] *= 0.8
            
        return operation
    
    def _apply_success_patterns(self, operation, success_data):
        """Apply patterns from successful operations"""
        # Simple enhancement - increase resources slightly if previous successes
        if success_data.get('count', 0) > 1:
            operation['traits']['execution_time_ms'] *= 1.1
            operation['traits']['memory_kb'] *= 1.1
            
        return operation
    
    def record_operation_result(self, operation_sovereign_id, success, vp_value):
        """Record the result of an operation for learning"""
        operation_key = self._get_operation_key({'traits': {'execution_time_ms': vp_value * 100, 'memory_kb': vp_value * 1000}})
        
        if success:
            if operation_key not in self.success_patterns:
                self.success_patterns[operation_key] = {'count': 0, 'avg_vp': 0}
            self.success_patterns[operation_key]['count'] += 1
            self.success_patterns[operation_key]['avg_vp'] = (
                (self.success_patterns[operation_key]['avg_vp'] * (self.success_patterns[operation_key]['count'] - 1) + vp_value) /
                self.success_patterns[operation_key]['count']
            )
        else:
            if operation_key not in self.failure_patterns:
                self.failure_patterns[operation_key] = {'count': 0, 'avg_vp': 0}
            self.failure_patterns[operation_key]['count'] += 1
            self.failure_patterns[operation_key]['avg_vp'] = (
                (self.failure_patterns[operation_key]['avg_vp'] * (self.failure_patterns[operation_key]['count'] - 1) + vp_value) /
                self.failure_patterns[operation_key]['count']
            )
            self.defunct_sovereign_ids.add(operation_sovereign_id)
    
    def get_learning_stats(self):
        """Get learning statistics"""
        return {
            'success_patterns': len(self.success_patterns),
            'failure_patterns': len(self.failure_patterns),
            'defunct_sovereign_ids': len(self.defunct_sovereign_ids),
            'total_operations': len(self.operation_history)
        }
